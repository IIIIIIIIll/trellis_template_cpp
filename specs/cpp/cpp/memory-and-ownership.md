# Memory and Ownership

> Ownership rules, smart-pointer discipline, and lifetime pitfalls for C++ in this project.

---

## Overview

Memory-safety defects dominate long-lived C++ codebases. This document makes ownership explicit: every object has exactly one owner, ownership is expressed in types, and non-owning access is visibly borrowed. Every pitfall names the tool that catches it, so violations surface in CI rather than in production.

Baseline: C++17 (`std::string_view`, `std::optional`, `std::unique_ptr`). C++20's `std::span` replaces pointer-plus-size pairs where available; the rules are identical either way.

---

## RAII Is Non-Negotiable

Every resource — memory, file descriptors, sockets, mutexes, GPU handles — is owned by an object whose destructor releases it. Manual acquire/release pairs are forbidden no matter how careful the surrounding code looks, because the next editor of the function inserts an early return.

Wrong:

```cpp
bool read_config(const char* path) {
    FILE* f = std::fopen(path, "r");
    if (!f) return false;
    if (!parse(f)) {
        return false;                 // leaks f
    }
    std::fclose(f);
    return true;
}
```

Right:

```cpp
bool read_config(std::string_view path) {
    std::ifstream f{std::string(path)};
    if (!parse(f)) return false;      // destructor closes
    return true;
}
```

A resource without an existing wrapper gets one immediately: a `std::unique_ptr<T, Deleter>` or a small scoped guard. Wrapping once beats remembering everywhere.

Caught by: ASan's LeakSanitizer (leaks), static analyzer leak checkers for handle types.

---

## The Ownership Ladder

| Rank | Tool | Use when | Notes |
|------|------|----------|-------|
| Default owner | `std::unique_ptr<T>` | Single owner, dynamic lifetime | Zero overhead; the factory return type of choice |
| Borrowed view | Raw `T*`, `T&`, `std::span`, `std::string_view` | Access without ownership | Must not dangle; the caller guarantees outliving |
| Shared owner | `std::shared_ptr<T>` | Lifetime genuinely shared, owner unknowable statically | Requires a written justification; cycles go through `weak_ptr` |
| Forbidden | Owning raw `new`/`delete`, mixing `malloc`/`free` | Never | Blocked in review |

Rules:

1. Create with `std::make_unique` / `std::make_shared`, never `unique_ptr<T>(new T(...))` — exception safety, and one allocation instead of two for shared.
2. "Maybe null, not owning" parameters take `T*`; "present, not owning" parameters take `T&`. Pointer out-parameters are forbidden; return values instead.
3. A `shared_ptr` in a signature is a design decision, not convenience. Copying one costs an atomic operation and freezes object lifetime; justify it in a comment or downgrade to `unique_ptr`/references.
4. Observing a shared object without extending its life takes `std::weak_ptr` and locks — mandatory for back-edges in parent/child graphs, caches, and observer lists.

Caught by: ASan (use-after-free and double-free from broken ownership), LSan (leaked cycles that `weak_ptr` should have broken), review for shared-ptr sprawl.

---

## Pass-by Rules

| Parameter kind | Convention |
|----------------|------------|
| Read-only text or bytes | `std::string_view` |
| Read-only sequence of objects | `std::span<const T>` (pointer + size until C++20) |
| Read-only single object, present | `const T&` |
| Read-only single object, maybe absent | `const T*`, documented as nullable |
| Sink — the callee stores or moves the argument | By value, then `std::move` into storage |
| Out-parameter | Return value; `T&` only when a second output genuinely exists |
| Optional result | Return `std::optional<T>`, never a sentinel or `nullptr` |

Wrong:

```cpp
class Parser {
public:
    // Caller with a literal or substring pays a needless std::string copy;
    // the parser then copies AGAIN into name_.
    void set_source(const std::string& s) { name_ = s; }
private:
    std::string name_;
};
```

Right:

```cpp
class Parser {
public:
    // Sink: takes its copy exactly once, moves into place.
    void set_source(std::string s) { name_ = std::move(s); }
private:
    std::string name_;
};

// Read-only entry points take views and accept literals for free.
void log_prefix(std::string_view prefix);
```

Notes:

- View parameters are borrow-only: if the value must outlive the call, copy it deliberately (see the pitfalls below before storing one).
- Do not maintain both a `const std::string&` and a `string_view` overload for the same parameter; one spelling wins.
- Sinks take by value even when callers usually pass lvalues: the copy happens at the boundary where the compiler can prove the source is no longer needed.

Caught by: clang-tidy `performance-unnecessary-value-param` (missing moves in sinks); the `const std::string&`-that-should-be-a-view case has no reliable automatic check and is a review item.

---

## Lifetime Pitfalls

### Dangling views into locals

Wrong:

```cpp
std::string_view host_of(std::string_view url) {
    std::string normalized = normalize(url);
    auto host = extract_host(normalized);   // view into `normalized`...
    return host;                            // ...dead on return
}
```

Right: return an owning `std::string`, or return a view strictly derived from memory the caller already owns. A `string_view`/`span` return type is a promise: "points into input memory that outlives this expression."

The same trap with a temporary:

```cpp
std::string_view sv = make_name();   // make_name returns std::string by value: dangles immediately
```

Caught by: GCC 13+ `-Wdangling-reference` in simple cases; ASan flags the use-after-return at first access. Any view returned across a function boundary deserves a look in the `asan` preset.

### Iterator and reference invalidation

| Container | insert / emplace | erase | Notes |
|-----------|------------------|-------|-------|
| `vector` | Reallocation invalidates everything; otherwise iterators/refs past the insertion point | Iterators and refs at and past the erased position | `reserve()` up front in hot loops |
| `deque` | Middle ops invalidate all iterators and references; end ops invalidate iterators only | All iterators and references | Rarely worth the semantics; prefer `vector` or `list` |
| `list` / `forward_list` | Nothing invalidated | Only the erased element | Node-stable |
| `map` / `set` | Nothing invalidated | Only the erased element | Node-stable |
| `unordered_map` / `unordered_set` | Rehash invalidates all iterators (references/pointers survive) | Only the erased element | `reserve()` to prevent rehash storms; `erase(it)` returns a still-valid iterator |

Wrong:

```cpp
auto& first = v.front();
v.push_back(x);        // may reallocate
use(first);            // dangling reference
```

Right: `reserve()` before the growth loop, hold keys/indices instead of references across mutations, or re-fetch after mutating.

Caught by: ASan for the heap cases; libstdc++ debug mode (`_GLIBCXX_DEBUG`) or libc++ hardened/debug assertions catches container-internal violations deterministically — worth one dedicated CI job if the budget allows.

### Containers of views versus owning containers

A `std::vector<std::string_view>` sliced from a `std::vector<std::string>` dangles wholesale the moment the owner resizes. Defaults:

1. Containers own by default (`std::vector<std::string>`).
2. A container of views is allowed only when the owner provably outlives it in the same scope, and the declaration site says so in a comment naming the owner.
3. At storage boundaries (config load, deserialization, IPC), re-own: convert views to owning strings once, then pass views downward.

### shared_ptr cycles

Parent owns children through `shared_ptr`; child stores a `shared_ptr` back to the parent; nothing is ever destroyed. All back-edges — parent links, observer registrations, cache entries — use `weak_ptr` and lock briefly.

Caught by: LeakSanitizer reports the unreachable cycle cluster; the leak dump pointing at both ends of a mutual `shared_ptr` is the classic signature.

### Arenas and pools on hot paths

Where the profiler shows allocator pressure, arenas (bump allocators) and object pools are encouraged — under rules that keep them safe:

1. The arena owns everything allocated from it; individual objects are never freed individually. Deallocation is a batch `reset()` at a well-defined scope exit.
2. Nothing escapes the arena scope. Handing an arena-backed pointer out across the boundary is the dangling-local bug wearing a costume; document arena-lifetime at every such API edge.
3. Preserve the sanitizer story: wire `reset()` to poison/unpoison the region (ASan container annotations or explicit poison calls) so use-after-reset stays detectable. An arena that blinds ASan turns tomorrow's bug into a heisenbug.
4. Measure first. Pools justified by intuition rather than a profile are complexity debt, not performance work.

Caught by: ASan when annotations are wired; review for pointers escaping the arena scope.

---

## Quality Check

```bash
cmake --preset asan && cmake --build --preset asan
ctest --preset asan --output-on-failure
```

Review checklist:

- [ ] No owning raw `new`/`delete` added; owners are `unique_ptr`, containers, or RAII guards
- [ ] Every new `shared_ptr` carries a lifetime-sharing justification
- [ ] Views (`string_view`, `span`, raw pointers) are never stored past the call they were passed to unless the owner is documented
- [ ] Container mutations near held iterators/references checked against the invalidation table
- [ ] Hot-path allocation changes backed by a measurement, arenas annotated for ASan

---

## Complete Coverage: R

The remaining ISO C++ Core Guidelines resource-management rules, each dispositioned against the ownership ladder: a row either restates a rung, enforces one of the ladder rules, or records a deliberate difference.

| Rule | Stance | Disposition |
|------|--------|-------------|
| `R.2` | Adopt | A raw `T*` denotes exactly one borrowed object; arrays decay and lose their length, so sequences travel as `std::span`/`string_view` — subscripting a lone pointer is the range-error opening this closes. |
| `R.3` | Adopt | Raw pointers sit on the Borrowed-view rung by definition; owning raw pointers occupy the Forbidden rung outright, so unlike upstream this project needs no `owner<T*>` annotation — nothing legal remains for it to mark. |
| `R.4` | Adopt | References borrow too: `T&` is a present, non-owning view with no null state; binding one to `*new` is an owning raw pointer in disguise and dies in review like any Forbidden-rung allocation. |
| `R.5` | Adopt | Scoped objects — locals, members, globals — cost no separate cleanup and let destructors manage members; reach for the Default owner only when lifetime must exceed the scope, keeping the guideline's own escape hatch for oversized locals: a `const unique_ptr<BigObject>`. |
| `R.6` | Adopt | A non-`const` global is an undeclared shared owner and a data-race candidate; constants are `constexpr`, mutable state gets explicit ownership plus the Concurrency guide's locking story, and init-order traps follow Quality Guidelines' accessor-function pattern. |
| `R.10` | Adopt | `malloc`/`free` construct and destroy nothing — a `malloc`-ed record's `string` member is just a string-sized bag of bits — and mixing them with `new`/`delete` is undefined; both verbs share the Forbidden rung, with `nothrow` new as the fallback where exceptions truly cannot fly. |
| `R.12` | Adopt | Hand every acquisition to its manager object immediately: registering the guard even one line after the open leaves a window where the next allocation throws and leaks the handle — an RAII wrapper at the acquisition site closes it entirely. |
| `R.13` | Adopt | Two allocations in one statement can interleave under unspecified evaluation order and leak when the second constructor throws; factories (`make_unique`, `make_shared`) remove the naked allocation, making the hazard unreachable — ladder rule 1. |
| `R.14` | Adopt | `void f(int[])` is `f(int*)` after decay — the length is simply gone; sequence parameters take `std::span` (pointer-plus-size spelling until C++20) per the pass-by table. |
| `R.15` | Adopt | Any custom `operator new` ships with its matching `operator delete`, or that deallocation function is deliberately `=delete`-ed; in practice this bites only arena and pool authors, since application code writes neither operator. |
| `R.20` | Adopt | Ownership is spelled in types: `unique_ptr` as Default owner, `shared_ptr` as Shared owner with written justification; assigning `new`'s result to a raw pointer strands the object outside the ladder by construction. |
| `R.21` | Adopt | `unique_ptr` outranks `shared_ptr` for the guideline's exact reasons — deterministic destruction, no atomic refcount traffic — so sharing is a design decision carrying its justification comment (ladder rule 3). |
| `R.22` | Adopt | `make_shared` names the type once and fuses control block with object into a single allocation; it is the only accepted spelling for creating a shared owner. |
| `R.23` | Adopt | `make_unique` avoids repeating the type name and keeps naked `new` out of call sites; factory functions returning a Default owner are built on it. |
| `R.24` | Adopt | Back-edges in shared graphs — parent links, observers, cache entries — hold `weak_ptr` and lock briefly, because a `shared_ptr` cycle's use count never reaches zero; LSan clusters pointing at both ends of a mutual pair are the signature of forgetting. |
| `R.30` | Adopt | Smart-pointer parameters are lifetime statements, not habits: readers take Borrowed views (`T*`, `T&`, span), sinks take by-value `unique_ptr`, and a by-value `shared_ptr` parameter nobody stores is an atomic no-op billed to every caller. |
| `R.31` | Adopt | Third-party and custom handle wrappers join the ladder via the std pattern — copyable counts as shared-like, move-only as unique-like — so every parameter rule below applies to them unchanged. |
| `R.32` | Adopt | A by-value `unique_ptr<widget>` parameter documents and enforces an ownership takeover — the callee intends to store or consume the widget; anything less takes `widget*` or `widget&`. |
| `R.33` | Adopt | `unique_ptr<widget>&` means the callee reseats the slot — assigns or calls `reset()` on some path; an lvalue-reference parameter never reassigned is a forbidden pointer out-parameter wearing a template. |
| `R.34` | Adopt | Take `shared_ptr<widget>` by value only to join the owner set (store a copy, ideally moved); otherwise every call pays atomic refcount traffic for nothing — the Shared-owner justification applies to signatures, not just members. |
| `R.35` | Adopt | `shared_ptr<widget>&` declares possible reseating, under the same contract as the unique case: no assignment or reset anywhere, no lvalue-reference parameter. |
| `R.36` | Adapt | Upstream hedges this rule and so does the ladder: reserve `const shared_ptr<widget>&` for conditionally retaining a count; definite sharers take the smart pointer by value, definite readers take a plain view. |
| `R.37` | Adopt | Never pass a pointer or reference pulled from an aliased smart pointer: pin the subtree first with a cheap local strong copy, then extract the view — resetting through another alias mid-call destroys the object under the borrowed reference. |

---

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
