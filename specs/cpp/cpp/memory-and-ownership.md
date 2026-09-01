# Memory and Ownership

> Ownership rules, smart-pointer discipline, and lifetime pitfalls for C++ in this project.

---

## Overview

Memory-safety defects dominate long-lived C++ codebases. This document makes ownership explicit: every object has exactly one owner, ownership is expressed in types, and non-owning access is visibly borrowed. Every pitfall names the tool that catches it, so violations surface under sanitizers rather than in production.

Baseline: C++14 (`std::make_unique`, generic lambdas, relaxed `constexpr`).
C++17 and C++20 additions appear as marked upgrades where they change the
recommendation — `std::string_view`, `std::optional`, `if constexpr`,
`[[nodiscard]]`, `std::span` — each with the C++14 spelling alongside, so a
C++14 project can follow every rule as written. C++20's `std::span` replaces
pointer-plus-size pairs where available; the rules are identical either way.

---

## RAII Is Non-Negotiable

Caught by: ASan's LeakSanitizer (leaks), static analyzer leak checkers for handle types.

**MEM-1 (hard).** Every resource — memory, file descriptors, sockets, mutexes, GPU handles — is owned by an object whose destructor releases it. Manual acquire/release pairs are forbidden no matter how careful the surrounding code looks, because the next editor of the function inserts an early return.

Wrong:

```cpp
// compiles; UB at runtime
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
// C++17
bool read_config(std::string_view path) {
    std::ifstream f{std::string(path)};
    if (!parse(f)) return false;      // destructor closes
    return true;
}
```

**MEM-2 (hard).** A resource without an existing wrapper gets one immediately: a `std::unique_ptr<T, Deleter>` or a small scoped guard. Wrapping once beats remembering everywhere.

**MEM-3 (hard).** Give the result of an acquisition to its manager immediately (`R.12`): registering the guard even one line after the open leaves a window where the next allocation throws and leaks the handle. Wrapping at the acquisition site closes the window entirely.

**MEM-4 (default).** Prefer scoped objects (`R.5`): locals, members, and globals cost no separate cleanup and let destructors manage members; reach for the Default owner rung only when lifetime must exceed the scope. For an oversized local, the common escape hatch stands — a `const std::unique_ptr<BigObject>` moves the bytes onto the heap while keeping the lifetime scoped.

---

## The Ownership Ladder

Caught by: ASan (use-after-free and double-free from broken ownership), LSan (leaked cycles that `weak_ptr` should have broken), TSan (data races from undeclared shared owners), review for shared-ptr sprawl.

Default strength: hard.

| Rank | Tool | Use when | Notes |
|------|------|----------|-------|
| **MEM-5** Default owner | `std::unique_ptr<T>` | Single owner, dynamic lifetime | Zero overhead; the factory return type of choice |
| **MEM-6** Borrowed view | Raw `T*`, `T&`, `std::span` (C++20; C++14: `T*` + size), `std::string_view` (C++17; C++14: `const std::string&`) | Access without ownership | Must not dangle; the caller guarantees outliving |
| **MEM-7** Shared owner | `std::shared_ptr<T>` | Lifetime genuinely shared, owner unknowable statically | Requires a written justification; cycles go through `weak_ptr` |
| **MEM-8** Forbidden | Owning raw `new`/`delete`, mixing `malloc`/`free` | Never | Blocked in review |

- **MEM-9.** The rungs are exhaustive by construction (`R.20`): ownership is spelled in types, and assigning `new`'s result to a raw pointer strands the object outside the ladder. Raw pointers sit on Borrowed view by definition (`R.3`) — a `T*` denotes exactly one borrowed object (`R.2`); arrays decay and lose their length, so sequences travel as a pointer-plus-size pair (**C++17:** `string_view` for text; **C++20:** `std::span` for element ranges). On the owning side, `new T[n]` is Forbidden like every other naked allocation; a genuine need for an uninitialized heap array is spelled `std::make_unique<T[]>(n)`, and constructed elements default to containers.

**MEM-10.** Owning raw pointers occupy Forbidden outright, which is why this project needs no `owner<T*>` annotation: nothing legal remains for it to mark. References borrow too (`R.4`): a `T&` is a present, non-owning view with no null state, and binding one to `*new` is an owning raw pointer in disguise that dies in review like any Forbidden-rung allocation.

**MEM-11.** `malloc`/`free` share the Forbidden rung (`R.10`) — they construct and destroy nothing (a `malloc`-ed record's `std::string` member is just a string-sized bag of bits) and mixing the verb pairs is undefined behavior; `nothrow` new stays as the fallback where exceptions truly cannot fly.

**MEM-12.** A non-`const` global is an undeclared shared owner and data-race candidate (`R.6`): constants are `constexpr`, mutable state gets explicit ownership plus [Concurrency](./concurrency.md)'s locking story, and init-order traps follow [Quality Guidelines](./quality-guidelines.md)' accessor-function pattern.

Rules:

- **MEM-13.** Create with `std::make_unique` / `std::make_shared`, never `unique_ptr<T>(new T(...))` (`R.22`, `R.23`) — one spelling instead of repeating the type name, exception safety, and one allocation instead of two for shared. The root cause is `R.13`: two allocations in one statement can interleave under unspecified evaluation order and leak when the second constructor throws; factories remove the naked allocation, making the hazard unreachable.
- **MEM-14.** "Maybe null, not owning" parameters take `T*`; "present, not owning" parameters take `T&`. Pointer out-parameters are forbidden; return values instead.
- **MEM-15.** A `shared_ptr` in a signature is a design decision, not convenience. Copying one costs an atomic operation and freezes object lifetime; justify it in a comment or downgrade to `unique_ptr`/references — `R.21`: `unique_ptr` outranks `shared_ptr` for deterministic destruction and zero refcount traffic.
- **MEM-16.** Observing a shared object without extending its life takes `std::weak_ptr` and locks — mandatory for back-edges in parent/child graphs, caches, and observer lists.
- **MEM-17.** Non-`std` smart pointers join the ladder through the `std` pattern (`R.31`): copyable counts as shared-like, move-only as unique-like — every smart-pointer signature rule below applies to them unchanged.
- **MEM-18.** Custom-deleter owners: `std::make_unique` has no deleter-taking form (`R.23` fixes only the default-deleter spelling), so an unwrapped resource with non-default cleanup writes its owner out in full at the acquisition site — `std::unique_ptr<Handle, Deleter>{acquire(...), release}` — and never parks the raw handle in between. A deleter that never runs is LeakSanitizer's classic leak signature.
- **MEM-19.** `make_shared` carve-outs (`R.22`): the fused allocation keeps the object's bytes alive while any `weak_ptr` exists — a mandated `weak_ptr` back-edge or cache entry over a large object pays full memory after the object is logically dead — and `make_shared` cannot take a custom deleter. When either bite lands, write the deliberate exception with a comment saying why: `std::shared_ptr<T>{new T{...}}` separates object from control block so weak observers stop pinning the bytes, and `std::shared_ptr<Handle>{acquire(...), release}` carries the deleter. No checker sees the retained bytes — the footprint is a review item — while the compiler rejects `make_shared` with a deleter outright.

---

## Pass-by Rules

The copy-cost side of these same decisions lives in [Functions and Interfaces](./functions-and-interfaces.md) under Value versus Const Reference (`F.15`, `F.16`) — its table prices copies, the one below fixes parameter kinds: companions, not rivals.

Caught by: clang-tidy `performance-unnecessary-value-param` (missing moves in sinks); the `const std::string&`-that-should-be-a-view case has no reliable automatic check and is a review item.

Default strength: default.

| Parameter kind | Convention |
|----------------|------------|
| **MEM-20** Read-only text or bytes | `std::string_view` (C++17; C++14: `const std::string&`) |
| **MEM-21** Read-only sequence of objects | `std::span<const T>` (C++20; C++14: `const T*` + size) |
| **MEM-22** Read-only single object, present | `const T&` |
| **MEM-23** Read-only single object, maybe absent | `const T*`, documented as nullable |
| **MEM-24** Sink — the callee stores or moves the argument | By value, then `std::move` into storage |
| **MEM-25 (hard)** Out-parameter | Return value; `T&` only when a second output genuinely exists |
| **MEM-26 (hard)** Optional result (value) | Return `std::optional<T>` (C++17; C++14: a named result struct), never a sentinel or `nullptr` |

Wrong:

```cpp
// compiles; UB at runtime
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
// C++17
class Parser {
public:
    // Sink: takes its copy exactly once, moves into place.
    void set_source(std::string s) { name_ = std::move(s); }
private:
    std::string name_;
};

// Read-only entry points take views and accept literals for free
// (C++14 spelling: void log_prefix(const std::string& prefix)).
void log_prefix(std::string_view prefix);
```

Notes:

- **MEM-27 (hard).** View parameters are borrow-only: if the value must outlive the call, copy it deliberately (see the pitfalls below before storing one).

Caught by: ASan for the use-after-free at first access; review for the store itself.

- A `string_view` promises no NUL termination: `.data()` is not a C string. Copy to `std::string` before handing text to a C interface (`fopen`, `exec`, sqlite...) — the `std::string(path)` conversion in the RAII example exists for exactly this reason.

- **MEM-28.** Do not maintain both a `const std::string&` and a `string_view` overload for the same parameter; one spelling wins.

Caught by: review — no automated detector.

- Sinks take by value even when callers usually pass lvalues: the copy happens at the boundary where the compiler can prove the source is no longer needed.
- **MEM-29 (hard).** Array parameters decay: `void f(int[])` *is* `f(int*)` after adjustment — the length is simply gone (`R.14`). Sequences take a pointer-plus-size pair (`const T* p, std::size_t n`), matching the table above; **C++20:** `std::span`.
- **MEM-30.** The optional-result row covers *value* results only. A finder that locates an existing object inside storage the caller already owns returns its position as a nullable `T*` (`F.42`, [Functions and Interfaces](./functions-and-interfaces.md)) — not a sentinel, and not an `optional<T>` that copies the object out of place.

---

## Smart Pointers in Signatures

Caught by: review — no checker reliably distinguishes takeover from borrow, so treat smart-pointer parameter types as reviewed API surface.

Default strength: hard.

**MEM-31.** Take smart pointers as parameters only to explicitly express lifetime semantics (`R.30`): readers take Borrowed views (`widget*`, `widget&`; **C++20:** `std::span`), sinks take by-value owners, and a by-value `shared_ptr` parameter nobody stores is an atomic no-op billed to every caller.

| Parameter | Contract | Notes |
|-----------|----------|-------|
| **MEM-32** `unique_ptr<widget>` by value | Callee assumes ownership — stores or consumes the widget | Anything less takes `widget*` or `widget&` (`R.32`) |
| **MEM-33** `unique_ptr<widget>&` | Callee reseats the slot — assigns or calls `reset()` on some path | Never reassigned, it is a forbidden pointer out-parameter wearing a template (`R.33`) |
| **MEM-34** `shared_ptr<widget>` by value | Callee joins the owner set — stores a copy, ideally moved | Otherwise every call pays atomic refcount traffic for nothing; the Shared-owner justification applies to signatures, not just members (`R.34`) |
| **MEM-35** `shared_ptr<widget>&` | Callee might reseat the pointer | Same contract as the unique case: no assignment or reset anywhere, no parameter (`R.35`) |
| **MEM-36** `const shared_ptr<widget>&` | Reserved for conditionally retaining a count | See the deviation below |

Deviation from `R.36`: upstream offers `const shared_ptr<widget>&`, hedged with warnings, for the "might retain a refcount" case; the ladder resolves the hedge. Definite sharers take the `shared_ptr` by value, definite readers take a plain view, and the const-lvalue-reference spelling survives only for genuinely conditional retention.

**MEM-37.** Never pass a pointer or reference obtained from an aliased smart pointer down a call chain (`R.37`): resetting through another alias mid-call destroys the object under the borrowed reference. Pin the subtree first with a cheap local strong copy, then extract the view.

---

## Lifetime Pitfalls

Default strength: hard.

### Dangling views into locals

**MEM-38.** A borrowed-view return — `T&`, `T*`, `const std::string&` included (**C++17:** `string_view`; **C++20:** `std::span`) — is a promise: it points into input memory that outlives the expression; never return a view into a local or a temporary.

Wrong:

```cpp
// C++17
// compiles; UB at runtime
std::string_view host_of(std::string_view url) {
    std::string normalized = normalize(url);
    auto host = extract_host(normalized);   // view into `normalized`...
    return host;                            // ...dead on return
}
```

Right:

Return an owning `std::string`, or return a view strictly derived from memory the caller already owns.

The same trap with a temporary:

```cpp
// C++17
// compiles; UB at runtime
std::string_view sv = make_name();   // make_name returns std::string by value: dangles immediately
```

Caught by: GCC 13+ `-Wdangling-reference` flags simple cases but is prone to false positives — treat findings as leads, not verdicts; ASan flags the use-after-return at first access. Any view returned across a function boundary deserves a look under an ASan+UBSan build.

### Iterator and reference invalidation

| Container | insert / emplace | erase | Notes |
|-----------|------------------|-------|-------|
| `vector` | Reallocation invalidates everything; otherwise iterators/refs past the insertion point | Iterators and refs at and past the erased position | `reserve()` up front in hot loops |
| `deque` | Middle ops invalidate all iterators and references; end ops invalidate iterators only | Middle ops invalidate all iterators and references; end ops invalidate only the erased element's | Rarely worth the semantics; prefer `vector` or `list` |
| `list` / `forward_list` | Nothing invalidated | Only the erased element | Node-stable |
| `map` / `set` | Nothing invalidated | Only the erased element | Node-stable |
| `unordered_map` / `unordered_set` | Rehash invalidates all iterators (references/pointers survive) | Only the erased element | `reserve()` to prevent rehash storms; `erase(it)` returns a still-valid iterator |

**MEM-39.** Never hold an iterator or reference across a container mutation that may invalidate it.

Wrong:

```cpp
// compiles; UB at runtime
auto& first = v.front();
v.push_back(x);        // may reallocate
use(first);            // dangling reference
```

Right:

`reserve()` before the growth loop, hold keys/indices instead of references across mutations, or re-fetch after mutating.

Caught by: ASan for the heap cases; libstdc++ debug mode (`_GLIBCXX_DEBUG`) or libc++ hardened/debug assertions catches container-internal violations deterministically — worth a dedicated debug-mode build if the budget allows.

### Containers of views versus owning containers

A container of views sliced from a `std::vector<std::string>` — `std::vector<const std::string*>` at C++14, `std::vector<std::string_view>` on the C++17 upgrade — dangles wholesale the moment the owner resizes. Defaults:

Caught by: ASan for the dangling use; review — no automated detector for the owner-naming declaration.

- **MEM-40 (default).** Containers own by default (`std::vector<std::string>`).
- **MEM-41.** A container of views is allowed only when the owner provably outlives it in the same scope, and the declaration site says so in a comment naming the owner.
- **MEM-42.** At storage boundaries (config load, deserialization, IPC), re-own: convert views to owning strings once, then pass views downward.

### shared_ptr cycles

**MEM-43.** Parent owns children through `shared_ptr`; child stores a `shared_ptr` back to the parent; nothing is ever destroyed. All back-edges — parent links, observer registrations, cache entries — use `weak_ptr` and lock briefly (`R.24`: a cycle's use count never reaches zero).

Caught by: LeakSanitizer reports the unreachable cycle cluster; the leak dump pointing at both ends of a mutual `shared_ptr` is the classic signature.

**MEM-44.** The adjacent double-own trap is `this` itself. Inside a member function `this` is unowned — the object already lives under whichever `shared_ptr` brought the caller here — so `std::shared_ptr<T>{this}` mints a second, independent owner of the same object, and the two control blocks destroy it twice. Types reachable as shared objects inherit `std::enable_shared_from_this<T>` and return `shared_from_this()`, which joins the existing control block; the call is legal only once a `shared_ptr` already manages the object — called earlier, it throws `std::bad_weak_ptr`.

Caught by: ASan catches the resulting double-free; a `shared_ptr` constructed directly from `this` is a review item.

### Arenas and pools on hot paths

Where the profiler shows allocator pressure, arenas (bump allocators) and object pools are encouraged — under rules that keep them safe:

Caught by: ASan when annotations are wired; review for pointers escaping the arena scope.

- **MEM-45.** The arena owns everything allocated from it; individual objects are never freed individually. Deallocation is a batch `reset()` at a well-defined scope exit. Objects enter through placement-`new`, and `reset()` must run their destructors (reverse construction order) before reclaiming — a reset that only rewinds the bump pointer leaks every constructed object.
- **MEM-46.** Nothing escapes the arena scope. Handing an arena-backed pointer out across the boundary is the dangling-local bug wearing a costume; document arena-lifetime at every such API edge.
- **MEM-47.** Preserve the sanitizer story: wire `reset()` to poison/unpoison the region (ASan container annotations or explicit poison calls) so use-after-reset stays detectable. An arena that blinds ASan turns tomorrow's bug into a heisenbug.
- **MEM-48 (default).** Measure first. Pools justified by intuition rather than a profile are complexity debt, not performance work.
- **MEM-49.** Custom allocators ship matched pairs (`R.15`): any custom `operator new` comes with its matching `operator delete`, or that deallocation function is deliberately `=delete`-ed. Application code writes neither operator, so this bites only arena and pool authors.

---

## Quality Check

Gates before merging ownership work: format-clean (`clang-format --dry-run`) and tidy-clean on changed sources, and the unit suite green under an ASan+UBSan build — allocation and lifetime are exactly what sanitizers exist to catch.

Review checklist:

- [ ] No owning raw `new`/`delete` added; owners are `unique_ptr`, containers, or RAII guards
- [ ] Every new `shared_ptr` carries a lifetime-sharing justification
- [ ] Views (`string_view`, `span`, raw pointers) are never stored past the call they were passed to unless the owner is documented
- [ ] Container mutations near held iterators/references checked against the invalidation table
- [ ] Hot-path allocation changes backed by a measurement, arenas annotated for ASan

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
