# Functions and Interfaces

> Calling conventions for C++ functions: parameter roles, return-value economics, function design, and interface intent made visible in signatures.

---

## Overview

A signature is a contract compilers partially enforce and reviewers fully judge. This page fixes that contract: parameter roles (`in`/`out`/`inout`), value-versus-reference decisions, view inputs, return economics, function size and purity, and the surface details — explicit constructors, named constants, `[[nodiscard]]` — that make intent unambiguous.

Ownership mechanics live in [Memory and Ownership](./memory-and-ownership.md); failure signaling lives in [Error Handling](./error-handling.md). Baseline is C++17; C++20's `std::span` replaces pointer-plus-size spellings without changing any rule below.

---

## Parameter Roles: in, out, inout

Every parameter plays exactly one role, readable off the declaration — through type and qualifiers — not off the body.

| Role | Signature | Contract |
|------|-----------|----------|
| `in` | `T` (cheap copy), `const T&`, `std::string_view`, `std::span<const T>` | Callee reads; copies anything it stores |
| `out` | Return value | `T&` reserved for a genuine second output |
| `inout` | `T&` | Reads and overwrites; the name states the transformation |
| will-move-from | `T&&` plus `std::move` | Consuming sinks only |
| forward | Template `TP&&` plus `std::forward` | Generic plumbing only |

```cpp
// Wrong: three behaviors behind one signature; every call site is a guess.
void process(std::string text, std::vector<int>& items, Stats& stats);

// Right: roles visible at the call site.
Stats process(std::string_view text);        // in -> out
void append_ids(std::vector<int>& items);    // inout: appends, preserves existing
```

Rules:

1. An `out` value returns as the return value (`F.20`); when two results genuinely exist, return a struct (`F.21`) instead of stacking a second `T&`.
2. An `inout` parameter's name declares the transformation: `normalize_path(p)`, `merge_into(acc)` — never a generic `update` (`F.17`).
3. Mutating through a `const T&` (casts, mutable caches keyed on the argument) turns an advertised `in` into a hidden `inout`. Forbidden.

Caught by: review — hidden `inout` behavior has no dependable static check; the signature convention makes it catchable by humans.

---

## Value versus Const Reference

Copy cost decides, not habit (`F.16`). Indirection is not free either: a `const T&` bound to a `double` costs more than copying eight bytes.

| Argument situation | Pass | Why |
|--------------------|------|-----|
| Scalar or two-word trivial type | By value | Copy beats aliasing machinery |
| Class instance, read-only | `const T&` | Skips an expensive copy |
| Text, read-only | `std::string_view` by value (`SL.str.12`) | Literals and substrings arrive without conversion |
| Sequence, read-only | `std::span<const T>` (`F.24`; pointer + size before C++20) | One spelling for arrays, vectors, slices |
| Sink storing the argument | By value, then `std::move` | One copy at the provable last use |
| Consumed inside generic code | `T&&` plus `std::move` (`F.18`) | Consumption stated explicitly |
| Presence varies | `const T*`, documented nullable (`F.22`) | Optionality encoded in the type |

Wrong:

```cpp
void add_user(const User& u) {
    users_.push_back(u);          // copied twice: argument -> parameter -> vector
}
double apply(const double rate);  // reference-to-scalar: pure indirection
```

Right:

```cpp
void add_user(User u) {           // sink: one copy, moved into place
    users_.push_back(std::move(u));
}
double apply(double rate);
```

Hot paths measuring differently may revert a sink to `const T&` plus an explicit copy — with the measurement in the comment. Do not maintain parallel `const std::string&` and `string_view` overloads; pick the view spelling once.

Caught by: clang-tidy `performance-unnecessary-value-param` catches sinks missing their move; needless `const T&` on scalars is a review item.

---

## View Inputs Borrow, Never Store

Read-only text and sequences enter as views so callers pay no conversion tax (`SL.str.12`, `F.24`). A view is a borrow: read it during the call; copy anything kept.

```cpp
Result find_record(const std::string& key);   // Wrong: literal callers pay an allocation
void checksum(const uint8_t* data, size_t len);   // Wrong: pointer and length drift apart

class Cache {                                 // Wrong: stored view dangles when caller dies
public:
    void put(std::string_view key, Entry e) { index_[key] = std::move(e); }
private:
    std::map<std::string_view, Entry> index_;
};

Result find_record(std::string_view key);     // Right: views flow inward
void checksum(std::span<const uint8_t> data); // Right: length travels with the bytes
class OwnedCache {                            // Right: storage boundaries re-own
public:
    void put(std::string key, Entry e) { index_[key] = std::move(e); }
private:
    std::map<std::string, Entry> index_;
};
```

At untrusted-input boundaries (config load, IPC, deserialization), validate and re-own first. Lifetime traps for stored views are cataloged in [Memory and Ownership](./memory-and-ownership.md).

Caught by: ASan flags use-after-free when a stored view outlives its owner; review catches the boundary case earlier.

---

## Results Return by Value

Since C++17 a prvalue is constructed directly in the destination (guaranteed elision) and named locals usually get NRVO — returning by value is the cheapest correct spelling, and it composes.

1. Build the result locally, `return local;` — never `return std::move(local);`, which changes the expression type and defeats NRVO (`F.48`).
2. Never return a pointer or reference to a local, including wrapped in a view (`F.43`). A `string_view`/`span` return promises memory the caller owns that outlives the call.
3. Never return `T&&` — it invites dangling temporaries and buys nothing over by-value (`F.45`).
4. Multiple results travel as a named struct (`F.21`).

```cpp
std::vector<Token> tokenize(std::string_view src) {
    std::vector<Token> out;
    // ...
    return std::move(out);        // Wrong: defeats NRVO, returns reference-shaped thing
}

std::string_view trim_prefix(std::string_view s) {
    std::string buf(s.substr(PREFIX_LEN));
    return buf;                   // Wrong: buf dies here; caller gets a dangling view
}

struct ParseOutcome {             // Right: multiple results, self-documenting, grows safely
    AST ast;
    size_t bytes_consumed;
};
ParseOutcome parse(std::string_view src);

Amount& ledger_total(Ledger& l);  // Fine: referent is a member that outlives the call
```

Caught by: GCC 13+ `-Wdangling-reference` for simple cases, ASan on first use otherwise; clang-tidy flags `std::move` in return statements.

---

## `[[nodiscard]]`: Results That Must Not Vanish

Discarding a computed answer or status is a bug wearing an optimization hat. Policy:

| Category | `[[nodiscard]]` |
|----------|-----------------|
| Status/result returns (`Result<T,E>`, `optional`, predicates) | Always |
| Pure computation where the result is the point; factories and builders | Yes |
| Effect-only procedures (logging, duplicate-tolerant inserts) | No |

```cpp
[[nodiscard]] Result<Config, Error> load_config(std::string_view path);
load_config("app.conf");          // Wrong: compiles; failure swallowed

auto cfg = load_config("app.conf");
if (!cfg) return cfg.error();     // Right: handled, not dropped
```

This extends `F.20`: once outputs travel as values, discarding them stops compiling. Treat new violations as CI errors.

Caught by: `-Wunused-result` via the attribute; review for categories the attribute cannot see.

---

## Function Design

### One Operation, Small Body

A function performs one logical operation (`F.2`), fits on one screen (`F.3`), and earns a name that says exactly that (`F.1`); nesting past three levels triggers extraction. Prefer pure functions — same input, same output, no hidden state (`F.8`); push I/O, locking, and globals to the edges.

```cpp
// Wrong: one name, four jobs — decode, validate, mutate globals, emit.
void handle_message(const uint8_t* data, size_t len) {
    auto msg = decode(data, len);
    if (!valid(msg)) { g_errors++; return; }
    g_cache[msg.key] = msg.value;
    send(msg.serialize());
}

// Right: effectful shell around testable cores.
std::optional<Message> parse_message(std::span<const uint8_t> bytes);
bool is_valid(const Message& m);
void handle_message(std::span<const uint8_t> bytes) {
    auto msg = parse_message(bytes);
    if (!msg || !is_valid(*msg)) return;
    cache_store(msg->key, msg->value);
    send(serialize(*msg));
}
```

### Default Arguments Beat Overload Pyramids

Collapse same-behavior overloads into default arguments (`F.51`). Separate overloads exist only where parameter types differ in behavior, not spelling.

```cpp
// Wrong: three spellings, one behavior.
std::string join(const std::vector<std::string>& parts);
std::string join(const std::vector<std::string>& parts, const std::string& sep);

// Right: knobs live in an options struct; defaults carry the common case.
struct JoinOptions { std::string_view sep = ", "; };
std::string join(std::span<const std::string> parts, JoinOptions opts = {});
```

### `noexcept` on Narrow Interfaces

Leaf accessors and swaps that provably cannot throw carry `noexcept` (`F.6`); anything allocating, formatting, logging, or calling unknown code must not. [Error Handling](./error-handling.md) owns the full discipline.

```cpp
class Ring {
public:
    [[nodiscard]] bool empty() const noexcept { return head_ == tail_; }  // narrow: holds
    void push(int value);                                                 // allocates: not noexcept
};
```

---

## Interface Intent

### Explicit Constructors

Single-argument constructors are `explicit` by default (`C.46`); implicit conversion is reserved for value types where it reads naturally, decided deliberately.

```cpp
class Port {
public:
    Port(uint16_t n) : n_(n) {}    // Wrong: any integer silently becomes a Port
};
void bind(Port p);
bind(port_count() * scale());      // binds a nonsense port without a peep

class StrictPort {
public:
    explicit StrictPort(uint16_t n) : n_(n) {}   // Right: intent at every call site
private:
    uint16_t n_;
};
```

### Named Constants, Not Magic Numbers

Meaningful literals get names (`Enum.2`): `constexpr` for single constants (`Con.5`), `enum class` for related sets (`Enum.1`). Loose booleans cluster into `enum class` parameters — `open(file, true, false)` is unreadable.

```cpp
if (attempts > 3) return false;                        // Wrong: what is 3?
std::this_thread::sleep_for(std::chrono::milliseconds(500));

constexpr int kMaxAttempts = 3;                        // Right
constexpr auto kRetryBackoff = std::chrono::milliseconds{500};
enum class Mode { Truncate, Append };                  // flag soup becomes names
```

### Const as Documentation

Default to immutability: objects that need not change stay `const` (`Con.1`), observing member functions are `const` (`Con.2`), inputs arrive as `const` references (`Con.3`). Const-correctness lets the compiler prove the read-only half of every contract above.

```cpp
class Ledger {
public:
    [[nodiscard]] std::optional<Amount> balance(Account id) const;  // observes
    Amount post(Account id, Amount delta);                          // mutates
};
```

---

## Quality Check

```bash
cmake --preset default && cmake --build --preset default
ctest --preset default --output-on-failure
clang-tidy -p build/default path/to/changed.cpp
```

Review checklist:

- [ ] Every parameter's role is readable from type and name; scalars by value, objects by `const T&`
- [ ] Text and sequences enter as views; nothing borrowed is stored without a documented owner
- [ ] Sinks take by value and `std::move`; no parallel view/non-view overloads
- [ ] No `return std::move(local)`; no pointer, reference, or view into a local escapes
- [ ] Multi-part results return structs; `[[nodiscard]]` on every status/computation/factory
- [ ] Functions do one operation, fit a screen, keep impure effects at the edge
- [ ] Same-shape overloads collapsed into default arguments; `noexcept` only on proven-narrow interfaces
- [ ] Single-argument constructors `explicit` unless conversion is the design
- [ ] Magic numbers replaced by `constexpr`/`enum class`; observers are `const`

---

## Complete Coverage: F, I, P, Con

Every rule ID from the Guidelines' Functions, Interfaces, Philosophy, and Constants sections that the prose above does not already cite gets its disposition here. Rows marked "covered elsewhere" route to the guide that owns the substance.

**F — Functions**

| Rule | Stance | Disposition |
|------|--------|-------------|
| `F.4` | Covered elsewhere | Quality Guidelines owns compile-time discipline: mark functions `constexpr` when the body is naturally constant-evaluable and never contort logic to earn the keyword; `constexpr` permits but does not force compile-time evaluation |
| `F.5` | Adopt | `inline` is a measured hint for very small, time-critical functions — not decoration. In-class definitions and templates are inline regardless, and anything meant as a stable binary surface stays out-of-line because an inline body is part of the ABI |
| `F.7` | Adopt | Interfaces that merely borrow take `T*`/`T&`; a smart pointer appears in a signature only to transfer or share ownership. A copyable smart-pointer parameter that is only dereferenced restricts callers for no benefit (ownership ladder in Memory and Ownership) |
| `F.9` | Adopt | Unused parameters stay unnamed, or carry `[[maybe_unused]]` when only conditionally dead (template dispatch); a named parameter claims a purpose it does not have |
| `F.10` | Adopt | An operation worth reusing earns a name — the oversized lambda hiding a case-insensitive compare extracts into a named helper. Purely local algorithm callbacks are exempt |
| `F.11` | Adopt | A simple function object needed in exactly one place stays an unnamed lambda at the call site; naming one for clarity is fine, but identical or near-identical lambdas must graduate into a named function |
| `F.15` | Adopt | Pass information the conventional way: this page's parameter-role and value-versus-reference tables are the local spelling of the Guidelines' normal-passing advice (already enforced above), and any cleverer scheme owes a measurement plus a comment |
| `F.19` | Adopt | Forwarding plumbing takes `TP&&` and `std::forward`s exactly once on every static path — piecewise per member is fine; already enforced above in the parameter-roles table's `forward` row, which reserves `TP&&` for generic plumbing only |
| `F.60` | Adopt | When "no object" is a valid input, say so with `T*` — never a fake-null reference; when absence is impossible, `T&` is simpler and often faster. Complements the presence-varies row above (`F.22`) |
| `F.23` | Adapt | Nullability belongs in the signature: a parameter that may be null takes a documented `const T*`, one that cannot takes `T&`. We spell the Guidelines' `not_null<T>` intent with those native forms since GSL vocabulary does not cross project APIs |
| `F.25` | Adapt | Text arrives as `std::string_view`; `zstring`-style zero-terminated spellings survive only at C interop seams where null termination is part of the wire contract, and they never imply ownership |
| `F.26` | Covered elsewhere | Memory and Ownership owns the ladder: transferring ownership through a pointer means returning `std::unique_ptr<T>` — the factory return type of choice for polymorphic results — never a locally allocated raw pointer |
| `F.27` | Covered elsewhere | Memory and Ownership again: `shared_ptr` is reserved for genuinely shared lifetimes, carries a written justification, prefers `unique_ptr` when one owner at a time suffices, and breaks cycles through `weak_ptr` |
| `F.42` | Adopt | A returned `T*` means "a position, possibly none" — finders may return nullable positions, never ownership; deletion rights stay with the owner |
| `F.44` | Adopt | Return `T&` when a copy is undesirable and "no object" cannot happen (accessors into members that outlive the call); already shown above with the `ledger_total` example — a returned reference never transfers ownership |
| `F.46` | Adopt | `main` returns `int` and may omit the `return` statement; `void main()` is a language extension, not C++, and costs portability |
| `F.47` | Adopt | Assignment operators assign and return non-`const` `*this` — "do as the ints do", consistent with standard-library types; the historical `const T&` advice is rejected as solving a problem nobody has |
| `F.49` | Adopt | Do not return `const T`: the top-level `const` blocks the rare accidental temporary write but suppresses move semantics on every extraction; drop the qualifier and return the value |
| `F.50` | Adopt | Reach for a lambda only when a function will not do — capturing locals, or definition at local scope. When either works, write the plain function; lambdas cannot overload, and generic lambdas are the one concise exception |
| `F.52` | Adopt | Lambdas used locally — including passed to parallel algorithms that join before returning — capture by reference: cheaper than copies and preserving intended side effects on the caller's objects |
| `F.53` | Adapt | A lambda that escapes its scope — queued to another thread, stored, returned — captures by value; a needed non-local pointer is owned (`unique_ptr`) and capturing the whole object spells `[*this]`, mirroring the borrowed-view rules above and in Memory and Ownership |
| `F.54` | Adopt | Never `[=]` inside a member function: it captures `this` by value, so members arrive by reference wearing a value-capture costume; write `[this]` (or `[i, this]`) explicitly, or `[*this]` for a true snapshot |
| `F.55` | Adopt | No `va_arg` argument passing: reading varargs trusts caller discipline the type system cannot verify, so mismatches are undefined. Variadic templates with fold expressions cover the real cases; a bare `...` used only to close an overload set stays acceptable |
| `F.56` | Covered elsewhere | Expressions and Flow sets the flow style: guard clauses first, early returns by default, compound conditions merged or extracted once nesting passes two levels |

**I — Interfaces**

| Rule | Stance | Disposition |
|------|--------|-------------|
| `I.1` | Adopt | Interfaces carry their behavior in the signature: no call modes read from namespace-scope variables, no results reported through side channels a caller can forget to check — failures throw or return checked statuses |
| `I.2` | Adopt | Non-`const` globals hide dependencies, initialize in unspecified order, and invite data races — every pointer or reference to mutable non-local data is a candidate race. Mutable namespace-scope state needs review justification; global constants stay welcome |
| `I.3` | Adopt | Avoid singletons — they are complicated globals in disguise. The acceptable form is a function-local static accessor for initialization on first use, kept simple enough that its destruction needs no synchronization; immutable global state is just `const`/`constexpr` |
| `I.4` | Adopt | Interfaces are precisely and strongly typed: no `void*`, no boolean flag soup (loose flags cluster into `enum class`), units carried by types such as durations — largely already enforced above through views, option structs, and named constants |
| `I.5` | Adapt | State every precondition the type system cannot express. Our spelling is `assert` for programmer errors plus a comment naming the constraint (Error Handling's failure taxonomy); a class invariant is established once by the constructor, not restated per member |
| `I.6` | Adapt | Prefer a dedicated precondition spelling over ad-hoc `if`s buried in the body; we do not adopt the GSL `Expects()` macro — `assert` with a comment plays the same role for programmer errors, and `unsigned` types are not the fix for non-negativity |
| `I.7` | Adapt | Postconditions deserve stating, especially for effects invisible in the return value ("the mutex is released on exit") — and resource-release postconditions are enforced in code by RAII rather than remembered by hand |
| `I.8` | Adapt | Same intent as `I.6` for the exit side: `Ensures()`-style checks are not adopted; "this resource must be released" becomes a scoped guard, other postconditions become asserts or contract comments |
| `I.9` | Covered elsewhere | Templates and Generics requires template parameters to document themselves: a named concept on C++20, a `static_assert` over standard traits on C++17 |
| `I.10` | Adapt | A failure to perform a required task must be unignorable. Error Handling splits the response — programmer errors assert, expected recoverable failures return checked statuses, rare failures throw — and `errno`-style codes survive only at ABI edges |
| `I.12` | Adapt | A pointer that must not be null says so in the signature; we express it as `T&` or a documented non-null `T*` rather than adopting the GSL `not_null` wrapper, gaining the same reviewer-visible guarantee |
| `I.13` | Adopt | Arrays never enter as a bare decayed pointer: sequences arrive as `std::span`/`std::string_view` so size travels with the elements (already enforced above); zero-terminated C strings are the sole exception |
| `I.22` | Covered elsewhere | Quality Guidelines bans cross-translation-unit global-constructor dependencies: `constexpr` initialization where possible, accessor functions otherwise — never one global's initializer reading another |
| `I.23` | Adopt | Keep the argument count low — aim under four. A long list usually means a missing abstraction (bundle into an options struct, as above) or a function doing two jobs that should be split |
| `I.24` | Adopt | Adjacent same-type parameters that could be swapped silently are defect bait (`copy_n(p, q, n)`); mark the source `const`, pass spans, or bundle into named fields. Order-insensitive pairs like `max(a, b)` are exempt |
| `I.25` | Covered elsewhere | Classes and Hierarchies defines interfaces as pure protocol: no data members, virtual destructor, deleted copies — data in a base forces one layout on every implementation |
| `I.26` | Adapt | Cross-compiler ABIs are not a project target, so full C++ interfaces are fine in-process; at genuine module edges the C-style subset discipline lives in Error Handling (total catches translating to status codes) and Quality Guidelines (ABI-stable headers) |
| `I.27` | Covered elsewhere | Quality Guidelines prescribes the Pimpl idiom — out-of-line destructor and move operations — for library headers distributed as binaries |
| `I.30` | Adopt | Ugly but necessary techniques get wrapped once behind a clean interface, with the suppression commented inside the abstraction; rule violations must never leak through an API into user code (mirrors the deviation-comment policy in Core Guidelines Alignment) |

**P — Philosophy**

| Rule | Stance | Disposition |
|------|--------|-------------|
| `P.2` | Covered elsewhere | Build and Toolchain pins the ISO baseline (C++17 on GCC 12+/Clang 15+/MSVC `/permissive-`) with `-Wpedantic` and `-Werror`, so compiler extensions fail CI instead of creeping in; necessary extensions would be localized and encapsulated |
| `P.3` | Adopt | Code states intent — through names, types, and roles — so a reader can tell whether it does what it should; this page's signature-first organization is that principle applied to interfaces (already enforced throughout) |
| `P.4` | Adopt | Push toward static type safety: unions become `variant`, array decay becomes `span`, and narrowing conversions plus casual casts are banned — Expressions and Flow owns the conversion and initialization rules |
| `P.6` | Covered elsewhere | What compile time cannot catch must be checkable at run time: Error Handling routes runtime failures through the assert/status/throw taxonomy, and Build and Toolchain runs ASan/TSan/UBSan presets so those checks actually execute |
| `P.8` | Covered elsewhere | Memory and Ownership makes leaks structural: RAII everywhere, owning `new`/`delete` banned, LeakSanitizer gating sanitized runs; a leak is anything no longer cleanable, and process-shutdown cleanup may rely on the OS |
| `P.9` | Covered elsewhere | Performance operationalizes "don't waste time or space": measurement first, allocation pressure priced explicitly, struct padding treated as real cost |
| `P.10` | Adopt | Prefer immutable data: something constant cannot change unexpectedly, cannot race, and optimizes better — already enforced above as default-to-`const`, with mutability required to justify itself at review |
| `P.11` | Adopt | Encapsulate messy constructs rather than spreading them: raw allocation, pointer arithmetic, and casting get wrapped once inside an abstraction (the standard library is the model), and low-level mess outside abstraction implementations is a review finding |
| `P.13` | Adopt | Use support libraries and need a reason not to: the standard library first, well-maintained third-party next; a widely used library beats a hand-rolled one on correctness, performance, and portability alike |

**Con — Constants and Immutability**

| Rule | Stance | Disposition |
|------|--------|-------------|
| `Con.4` | Adopt | Objects whose values never change after construction are declared `const` — a non-`const` local forces every reader to assume it mutates somewhere below; unmodified non-`const` variables are cleanup fodder (house style already, under default-to-immutability above) |

---

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
