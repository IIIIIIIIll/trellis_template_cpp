# Functions and Interfaces

> Calling conventions for C++ functions: parameter roles, return-value economics, function design, and interface intent made visible in signatures.

---

## Overview

A signature is a contract compilers partially enforce and reviewers fully judge. This page fixes that contract: parameter roles (`in`/`out`/`inout`), value-versus-reference decisions, view inputs, return economics, function size and purity, and the surface details — explicit constructors, named constants, `[[nodiscard]]` — that make intent unambiguous. The principle underneath (`P.3`): code states intent through names, types, and roles so a reader can tell whether it does what it should — a signature-first page is that principle applied. And when the standard library or a well-maintained third-party library already provides a capability, reaching for it beats hand-rolling (`P.13`): correctness, performance, and portability come pre-tested.

Ownership mechanics live in [Memory and Ownership](./memory-and-ownership.md), which makes leaks structural instead of hunting them one by one (`P.8`); failure signaling lives in [Error Handling](./error-handling.md), owning what compile time cannot catch and run time must (`P.6`).

Baseline: C++14 (`std::make_unique`, generic lambdas, relaxed `constexpr`).
C++17 and C++20 additions appear as marked upgrades where they change the
recommendation — `std::string_view`, `std::optional`, `if constexpr`,
`[[nodiscard]]`, `std::span` — each with the C++14 spelling alongside, so a
C++14 project can follow every rule as written. C++20's `std::span` replaces
pointer-plus-size spellings without changing any rule below.

---

## Parameter Roles: in, out, inout

Default strength: default.

Caught by: review — hidden `inout` behavior has no dependable static check; the signature convention makes it catchable by humans. Unsynchronized argument-keyed cache mutation surfaces under TSan.

**FN-1.** Every parameter plays exactly one role, readable off the declaration — through type and qualifiers — not off the body.

| Role | Signature | Contract |
|------|-----------|----------|
| **FN-2** `in` | `T` (cheap copy), `const T&`, `std::string_view` (C++17; C++14: `const std::string&`), `std::span<const T>` (C++20; C++14: `const T*` + size) | Callee reads; copies anything it stores |
| **FN-3** `out` | Return value | `T&` reserved for a genuine second output |
| **FN-4** `inout` | `T&` | Reads and overwrites; the name states the transformation |
| **FN-5** will-move-from | `T&&` plus `std::move` | Consuming sinks only |
| **FN-6 (hard)** forward | Template `TP&&` plus `std::forward` | Generic plumbing only — every static path forwards exactly once, piecewise per member if needed (`F.19`) |

```cpp
// C++17
// compiles; UB at runtime
// Wrong: three behaviors behind one signature; every call site is a guess.
void process(std::string text, std::vector<int>& items, Stats& stats);

// Right: roles visible at the call site.
Stats process(std::string_view text);        // in -> out
void append_ids(std::vector<int>& items);    // inout: appends, preserves existing
```

Rules:

- **FN-7.** An `out` value returns as the return value (`F.20`); when two results genuinely exist, return a struct (`F.21`) instead of stacking a second `T&`.
- **FN-8.** An `inout` parameter's name declares the transformation: `normalize_path(p)`, `merge_into(acc)` — never a generic `update` (`F.17`).
- **FN-9 (hard).** Mutating through a `const T&` — a `const_cast` or any write to the referent — turns an advertised `in` into a hidden `inout`. Forbidden.
- **FN-10 (hard).** A mutable cache keyed on a `const T&` argument is not a hidden `inout`: the parameter itself is never written. This is accepted logical constness under two obligations — the cache is documented as such (`mutable` members carry the name), and its thread safety is settled: guarded access, or confinement to one thread.
- **FN-11.** Unused parameters stay unnamed, or — when conditionally dead, template dispatch especially (`F.9`) — are silenced with a `(void)p;` statement. **C++17:** `[[maybe_unused]]` marks them without the cast. A named parameter claims a purpose it does not have.

---

## Value versus Const Reference

Default strength: default.

Caught by: clang-tidy `performance-unnecessary-value-param` catches sinks missing their move; needless `const T&` on scalars is a review item.

**FN-12.** Copy cost decides, not habit (`F.16`). These tables are the project's spelling of the Guidelines' conventional-passing advice (`F.15`); anything cleverer than the rows below owes a measurement plus a comment. Indirection is not free either: a `const T&` bound to a `double` costs more than copying eight bytes. The full parameter-kind mapping — views, sinks, out-params, optionality — lives in the Pass-by Rules section of [Memory and Ownership](./memory-and-ownership.md).

| Argument situation | Pass | Why |
|--------------------|------|-----|
| **FN-13** Scalar or two-word trivial type | By value | Copy beats aliasing machinery |
| **FN-14** Class instance, read-only | `const T&` | Skips an expensive copy |
| **FN-15** Text, read-only | `std::string_view` (C++17; C++14: `const std::string&`) by value (`SL.str.12`) | Literals and substrings arrive without conversion |
| **FN-16** Sequence, read-only | `std::span<const T>` (`F.24`; C++20; C++14: `const T*` + size) | One spelling for arrays, vectors, slices |
| **FN-17** Sink storing the argument | By value, then `std::move` | One copy at the provable last use |
| **FN-18** Consumed inside generic code | `T&&` plus `std::move` (`F.18`) | Consumption stated explicitly |
| **FN-19** Presence varies | `const T*`, documented nullable (`F.22`) | Optionality encoded in the type |

These rows and the parameter-roles table above agree: by value is the default sink spelling — the copy lands at the call boundary, the move at the provable last use — while `T&&` is reserved for sinks that must reject lvalue callers or forward into generic code.

Wrong:

```cpp
// compiles; UB at runtime
void add_user(const User& u) {
    users_.push_back(u);          // one copy: argument -> vector — const& cannot move, so rvalue callers copy too
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

Hot paths measuring differently may revert a sink to `const T&` plus an explicit copy, the measurement recorded in the comment — pricing such changes is measurement-first territory ([Performance](./performance.md), `Per.6`).

**FN-20.** Ownership and absence change the calculus. A smart-pointer parameter exists to transfer or share ownership — never to borrow; a copyable smart pointer that is only dereferenced restricts callers for no benefit (`F.7`; the ownership ladder lives in [Memory and Ownership](./memory-and-ownership.md)).

**FN-21.** When "no object" is a valid input, say so with `T*`; when absence is impossible, `T&` is simpler and often faster (`F.60`).

**FN-22.** Deviation from `F.23`: the Guidelines spell non-null parameters with GSL `not_null<T>`; we keep native forms — documented `const T*` for may-be-null, `T&` for cannot-be-null — because GSL vocabulary does not cross project APIs.

---

## View Inputs Borrow, Never Store

Default strength: default.

Caught by: ASan flags use-after-free when a stored view outlives its owner; review catches the boundary case earlier.

**FN-23.** Read-only text and sequences enter without copying caller data — on C++14 as `const std::string&` (or `const char*`) and pointer-plus-size pairs; **C++17:** `std::string_view` / `std::span<const T>` spell the borrow in the type (`SL.str.12`, `F.24`). A view is a borrow: read it during the call; copy anything kept.

```cpp
// C++17
#include "result.h"

// compiles; UB at runtime
Result<Record, Error> find_record(const std::string& key);   // Wrong: literal callers pay an allocation
Result<Record, Error> find_record(std::string_view key);     // Right: views flow inward
```

Arrays never arrive as a bare decayed pointer — size travels with the elements (`I.13`).

```cpp
// C++20: std::span
// compiles; UB at runtime
void checksum(const uint8_t* data, size_t len);   // Wrong: pointer and length drift apart
void checksum(std::span<const uint8_t> data); // Right: length travels with the bytes
```

**FN-24 (hard).** At untrusted-input boundaries (config load, IPC, deserialization), validate and re-own first. Lifetime traps for stored views are cataloged in [Memory and Ownership](./memory-and-ownership.md).

```cpp
// C++17
// compiles; UB at runtime
class Cache {                                 // Wrong: stored view dangles when caller dies
public:
    void put(std::string_view key, Entry e) { index_[key] = std::move(e); }
private:
    std::map<std::string_view, Entry> index_;
};

class OwnedCache {                            // Right: storage boundaries re-own
public:
    void put(std::string key, Entry e) { index_[key] = std::move(e); }
private:
    std::map<std::string, Entry> index_;
};
```

**FN-25.** Zero-terminated spellings survive at C interop seams only, where null termination is part of the wire contract — and even there they imply no ownership. Deviation from `F.25`: the Guidelines name C-style strings `zstring`/`czstring`; we spell them plain `const char*` with the null-termination expectation documented, since GSL vocabulary does not cross project APIs.

---

## Results Return by Value

On C++14 a returned value is moved (NRVO eliding the move when the compiler can), and containers being filled pre-size with `reserve`; since C++17 the prvalue is constructed directly in the destination (guaranteed elision). Returning by value is the cheapest correct spelling either way, and it composes.

Default strength: hard.

Caught by: GCC 13+ `-Wdangling-reference` for simple cases, ASan on first use otherwise; clang-tidy flags `std::move` in return statements.

- **FN-26.** Build the result locally, `return local;` — never `return std::move(local);`, which changes the expression type and defeats NRVO (`F.48`).

```cpp
// C++17
// compiles; UB at runtime
std::vector<Token> tokenize(std::string_view src) {
    std::vector<Token> out;
    // ...
    return std::move(out);        // Wrong: defeats NRVO, returns reference-shaped thing
}
```

```cpp
// C++17
std::vector<Token> tokenize(std::string_view src) {
    std::vector<Token> out;
    // ...
    return out;                   // Right: NRVO constructs in place at the call site
}
```

- **FN-27.** Never return a pointer or reference to a local (`F.43`); on C++14 the string-copy case returns `std::string` by value. **C++17:** a `string_view`/`span` return promises memory that outlives the call — a callee-owned cache or static storage qualifies; who owns the backing bytes is a separate, documented question — and a local wrapped in a view is the same bug.

```cpp
// C++17
// compiles; UB at runtime
std::string_view trim_prefix(std::string_view s) {
    std::string buf(s.substr(PREFIX_LEN));
    return buf;                   // Wrong: buf dies here; caller gets a dangling view
}
```

```cpp
// C++17
std::string_view trim_prefix(std::string_view s) {
    return s.substr(PREFIX_LEN);  // Right: view into the caller's argument, which outlives the call
}
```

- **FN-28.** Never return `T&&` — it invites dangling temporaries and buys nothing over by-value (`F.45`).

- **FN-29.** Multiple results travel as a named struct (`F.21`).

```cpp
// C++17
// compiles; UB at runtime
void parse(std::string_view src, AST& ast, size_t& consumed);   // Wrong: results stacked as out-params

struct ParseOutcome {             // Right: multiple results, self-documenting, grows safely
    AST ast;
    size_t bytes_consumed;
};
ParseOutcome parse(std::string_view src);

Amount& ledger_total(Ledger& l);  // Fine: referent is a member that outlives the call (F.44)
```

- **FN-30.** A returned `T*` promises a position, possibly none — finders may return nullable positions, never ownership; deletion rights stay with the owner (`F.42`).

- **FN-31.** Assignment operators assign and return non-`const` `*this`, as the ints do and the standard library does; the historical `const T&` advice solved a problem nobody had (`F.47`).

```cpp
// compiles; UB at runtime
class BufferBad {
public:
    const BufferBad& operator=(const BufferBad& o) { return *this; }   // Wrong: const *this suppresses move-assignment (F.47)
};

class Buffer {
public:
    Buffer& operator=(const Buffer&) = default;   // Right: non-const *this, like the ints (F.47)
};
```

- **FN-32.** Do not return `const T`: the top-level qualifier blocks a rare accidental temporary write but suppresses move semantics on every extraction (`F.49`).

```cpp
// compiles; UB at runtime
const std::string render_name();   // Wrong: top-level const suppresses move-out (F.49)
std::string render_title();        // Right: movable, writable result
```

- **FN-33.** `main` returns `int` and may omit the `return`; `void main()` is a compiler extension, not C++, and costs portability (`F.46`).

```cpp
void main();                       // Wrong: a compiler extension, not C++ (F.46)
// compile-error: '::main' must return 'int'
int main();                        // Right: int; the return statement is optional (F.46)
```

Ownership transfer and sharing through returned pointers route through [Memory and Ownership](./memory-and-ownership.md) (`F.26`, `F.27`): transferring means returning `std::unique_ptr<T>` — never a locally allocated raw pointer — while `shared_ptr` is reserved for genuinely shared lifetimes with a written justification, prefers `unique_ptr` when one owner at a time suffices, and breaks cycles through `weak_ptr`. A returned `T&` is the spelling for results where copying is undesirable and "no object" cannot happen (`F.44`) — accessors into members that outlive the call, like `ledger_total` above; a returned reference never transfers ownership.

---

## `[[nodiscard]]`: Results That Must Not Vanish

Discarding a computed answer or status is a bug wearing an optimization hat. On C++14, must-check results carry a `/* must-check */` comment on the declaration and a dropped result is a review finding; **C++17:** `[[nodiscard]]` hands enforcement to the compiler. Policy:

Default strength: hard.

Caught by: `-Wunused-result` via the attribute (C++17; the C++14 comment marking is review-enforced); review for categories the attribute cannot see.

| Category | Must-check marking |
|----------|-----------------|
| **FN-34** Status/result returns (`Result<T,E>`, `optional` (C++17; C++14: status enum), predicates) | Always |
| **FN-35** Pure computation where the result is the point; factories and builders | Yes |
| **FN-36** Effect-only procedures (logging, duplicate-tolerant inserts) | No |

```cpp
// C++17
#include "result.h"

// compiles; UB at runtime
// Wrong: compiles; failure swallowed
Result<Config, Error> load_config(std::string_view path);
load_config("app.conf");

// Right: handled, not dropped
[[nodiscard]] Result<Config, Error> load_config(std::string_view path);

auto cfg = load_config("app.conf");
if (!cfg) return cfg.error();
```

**FN-37.** The marking also applies at type level: tag a status/`Result` type once — the `/* must-check */` comment on C++14, **C++17:** the `[[nodiscard]]` attribute — and every function returning it is covered, no per-function decoration to forget.

This extends `F.20`: once outputs travel as values, a discarded result is a visible defect at every call site — **C++17:** the attribute turns it into a compile error. Treat new violations as merge blockers.

---

## Function Design

Default strength: default.

Caught by: review — no automated detector.

### One Operation, Small Body

**FN-38.** A function performs one logical operation (`F.2`), fits on one screen (`F.3`), and earns a name that says exactly that (`F.1`); nesting past three levels triggers extraction.

```cpp
// C++20: std::span
// compiles; UB at runtime
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

**FN-39.** Prefer pure functions — same input, same output, no hidden state (`F.8`); push I/O, locking, and globals to the edges.

Guard clauses, early returns, and merged compound conditions are flow style owned by [Expressions and Flow](./expressions-and-flow.md) (`F.56`).

### Default Arguments Beat Overload Pyramids

**FN-40.** Collapse same-behavior overloads into default arguments (`F.51`). Separate overloads exist only where parameter types differ in behavior, not spelling.

```cpp
// C++20: std::span
// compiles; UB at runtime
// Wrong: three spellings, one behavior.
std::string join(const std::vector<std::string>& parts);
std::string join(const std::vector<std::string>& parts, const std::string& sep);

// Right: one knob, one default argument.
std::string join(std::span<const std::string> parts, std::string_view sep = ", ");
```

**FN-41.** Keep argument lists short — aim under four (`I.23`): a long list usually means a missing abstraction or two jobs wearing one name. One knob takes a default argument; an options struct earns its place when knobs multiply, because fields added later extend the interface without breaking existing call sites.

```cpp
// C++20: std::span
// compiles; UB at runtime
// Wrong: knobs multiplied onto one signature — every call site repeats them.
std::string join(std::span<const std::string> parts, std::string_view sep = ", ", bool dedupe = false);

// Right: knobs multiplied — options struct; a new field breaks no call site.
struct JoinOptions { std::string_view sep = ", "; bool dedupe = false; };
std::string join(std::span<const std::string> parts, JoinOptions opts = {});
```

One cost to know: a default argument's value is baked into each call site, so changing a published default reaches only callers that recompile — already-built binaries keep passing the old value.

### `noexcept` on Narrow Interfaces

**FN-42.** Leaf accessors and swaps that provably cannot throw carry `noexcept` (`F.6`).

**FN-43 (hard).** Anything allocating, formatting, logging, or calling unknown code must not be `noexcept`.

```cpp
// C++17
class Ring {
public:
    [[nodiscard]] bool empty() const noexcept { return head_ == tail_; }  // narrow: holds
    void push(int value);                                                 // allocates: not noexcept
private:
    std::size_t head_ = 0;
    std::size_t tail_ = 0;
};
```

[Error Handling](./error-handling.md) owns the full discipline.

### `inline` Is a Measured Hint, Not Decoration

**FN-44.** `inline` manages duplicate definitions; as a speed tool it is a measured hint for very small, time-critical functions (`F.5`). In-class definitions and templates are inline regardless.

**FN-45 (hard).** Anything meant as a stable binary surface stays out-of-line — an inline body is part of the ABI.

### No `va_arg` Argument Passing

**FN-46 (hard).** Reading varargs trusts caller discipline the type system cannot verify, so mismatches are undefined behavior (`F.55`). Variadic templates cover the real cases — recursion or `std::index_sequence` on C++14; **C++17:** fold expressions collapse the recursion. A bare `...` used only to close an overload set stays acceptable.

---

## Lambdas and Captures

Default strength: default.

Caught by: review — no automated detector.

**FN-47.** Reach for a lambda only where a plain function will not do — capturing locals, or definition genuinely at local scope (`F.50`); lambdas cannot overload, and generic lambdas are the one concise exception. A simple function object needed in exactly one place stays an unnamed lambda at the call site; identical or near-identical lambdas graduate into a named function, because an operation worth reusing earns a name (`F.10`, `F.11`).

```cpp
// compiles; UB at runtime
// Wrong: a comparison policy living inline — and duplicated at the next call site.
auto cmp = [](const Entry& a, const Entry& b) {
    /* normalization, tie-breaks, twelve lines */
};

// Right: the operation earned a name; call sites stay glue-thin.
bool entry_less(const Entry& a, const Entry& b);
```

**FN-48.** Lambdas used locally — including passed to parallel algorithms that join before returning — capture by reference (`F.52`): cheaper than copies and preserving intended side effects on the caller's objects.

**FN-49 (hard).** A lambda that escapes its scope — queued to another thread, stored, returned — captures by value, with any needed non-local pointer owned (`unique_ptr`) and whole-object snapshots captured by copy — `[snapshot = *this]` on C++14; **C++17:** `[*this]` spells the same in one token. Deviation from `F.53`: upstream avoids escaping by-reference captures where lifetimes can be proven; we make by-value unconditional, because proving a referenced object outlives another thread is exactly the review burden the rule exists to remove — mirroring the borrowed-view rules above and in [Memory and Ownership](./memory-and-ownership.md).

**FN-50 (hard).** `[this]` stays a borrow: it is safe only where the lambda cannot outlive the owner — synchronous call sites, or a queue proven to join before the owner dies.

```cpp
// C++17
// compiles; UB at runtime
class Poller {
public:
    void schedule(TaskQueue& q) {
        q.push([this] { poll(); });   // Wrong here: queued — borrowed this dangles unless the queue joins before this Poller dies
        q.push([*this] mutable { poll(); });  // Right: queued — true snapshot; [this] is for synchronous call sites
    }
private:
    void poll();
};
```

**FN-51 (hard).** Never `[=]` inside a member function (`F.54`): it captures `this` by value, so members arrive by reference wearing a value-capture costume. Write `[this]` (or `[i, this]`) explicitly; for a true snapshot, `[snapshot = *this]` on C++14 — **C++17:** `[*this]`.

```cpp
// C++17
// compiles; UB at runtime
class Poller {
public:
    void schedule(TaskQueue& q) {
        q.push([=] { poll(); });      // Wrong: [=] smuggles this; members arrive by reference
        q.push([*this] mutable { poll(); });  // Right: explicit capture — a true snapshot
    }
private:
    void poll();
};
```

---

## Interface Intent

Default strength: default.

Caught by: review — no automated detector.

### Explicit Constructors

**FN-52 (hard).** Single-argument constructors are `explicit` by default (`C.46`); implicit conversion is reserved for value types where it reads naturally, decided deliberately.

```cpp
// compiles; UB at runtime
// Wrong: any integer silently becomes a Port
class Port {
public:
    Port(uint16_t n) : n_(n) {}
private:
    uint16_t n_;
};
void bind(Port p);
bind(port_count() * scale());      // binds a nonsense port without a peep

// Right: intent at every call site
class StrictPort {
public:
    explicit StrictPort(uint16_t n) : n_(n) {}
private:
    uint16_t n_;
};
```

### Named Constants, Not Magic Numbers

**FN-53.** Meaningful literals get names (`Enum.2`): `constexpr` for single constants (`Con.5`), `enum class` for related sets (`Enum.1`). Loose booleans cluster into `enum class` parameters — `open(file, true, false)` is unreadable.

```cpp
// compiles; UB at runtime
if (attempts > 3) return false;                        // Wrong: what is 3?
std::this_thread::sleep_for(std::chrono::milliseconds(500));

constexpr int kMaxAttempts = 3;                        // Right
constexpr auto kRetryBackoff = std::chrono::milliseconds{500};
enum class Mode { Truncate, Append };                  // flag soup becomes names
```

**FN-54.** Functions whose bodies are naturally constant-evaluable take `constexpr` — without contorting logic to earn the keyword; `constexpr` permits compile-time evaluation, it does not force it (`F.4`; compile-time discipline lives in [Quality Guidelines](./quality-guidelines.md)).

### Const as Documentation

Caught by: compiler diagnostics — const-correctness is enforced at compile time; review for intent.

**FN-55.** Default to immutability (`P.10`): something constant cannot change unexpectedly, cannot race, and optimizes better, so mutability has to justify itself at review.

**FN-56.** Objects whose values never change after construction are declared `const` (`Con.4`) — a non-`const` local forces every reader to assume it mutates somewhere below, making unmodified non-`const` variables cleanup fodder. Objects that need not change stay `const` (`Con.1`), observing member functions are `const` (`Con.2`), inputs arrive as `const` references (`Con.3`). Const-correctness lets the compiler prove the read-only half of every contract above.

```cpp
// C++17
class Ledger {
public:
    [[nodiscard]] std::optional<Amount> balance(Account id) const;  // observes
    Amount post(Account id, Amount delta);                          // mutates
};
```

---

## Interface Design

Default strength: hard.

Caught by: review — no automated detector.

**FN-57.** An interface is everything a caller can know without reading the body, so signatures carry the behavior: no call modes read from namespace-scope variables, no results reported through side channels a caller can forget to check — failures throw or return checked statuses (`I.1`).

### Strongly Typed Inputs

**FN-58 (default).** Interfaces are precisely and strongly typed (`I.4`) — largely enforced above through views over raw sequences (or their C++14 pointer-plus-size spellings), option structs over flag soup, named constants over magic numbers, and units carried by types such as durations. Push toward static type safety (`P.4`): on C++14 a raw union becomes a tagged struct and array decay becomes a pointer-plus-size pair; **C++17:** unions become `variant`; **C++20:** decay becomes `span`. Narrowing conversions plus casual casts stay banned — the conversion and initialization rules live in [Expressions and Flow](./expressions-and-flow.md).

**FN-59.** Adjacent same-type parameters invocable with the same arguments in either order are defect bait — `copy_n(p, q, n)` reads three ways (`I.24`); mark the source `const`, pass pointer-plus-size pairs (`std::span` on C++20), or bundle into named fields. Order-insensitive pairs like `max(a, b)` are exempt.

```cpp
// C++20: std::span
// compiles; UB at runtime
void copy_n(char* p, char* q, size_t n);   // Wrong: which is source, which is sink?

// Right: const answers the question
void copy_n(std::span<const char> src,
            std::span<char> dst);
```

**FN-60.** Non-null parameters say so in the signature. Deviation from `I.12`: we do not adopt the GSL `not_null<T>` wrapper — `T&` or a documented non-null `T*` gives reviewers the same guarantee in native spelling, matching the `F.23` rationale above.

### Global State and Singletons

**FN-61.** Mutable namespace-scope state hides dependencies, initializes in unspecified order, and invites data races — every pointer or reference to mutable non-local data is a candidate race (`I.2`). It needs review justification; global constants stay welcome.

**FN-62.** Avoid singletons (`I.3`): they are complicated globals in disguise. The acceptable form is a function-local static accessor for initialization on first use, kept simple enough that its destruction needs no synchronization.

**FN-63.** One global's initializer never reads another — constexpr initialization where possible, accessor functions otherwise ([Quality Guidelines](./quality-guidelines.md), `I.22`).

### Preconditions and Postconditions

**FN-64 (default).** State every precondition the type system cannot express (`I.5`), preferably as a dedicated spelling rather than ad-hoc `if`s buried in the body (`I.6`). Deviation from `I.5`: GSL `Expects()` is not adopted — preconditions are spelled `assert` for programmer errors plus a comment naming the constraint (the failure taxonomy lives in [Error Handling](./error-handling.md)), and a class invariant is established once by the constructor, not restated per member. Deviation from `I.6`: likewise no dedicated precondition macro — `assert` with the naming comment plays that role, and `unsigned` types are not the fix for non-negativity.

```cpp
Rect intersect(Rect a, Rect b) {
    assert(a.width >= 0 && a.height >= 0);   // precondition: programmer error if violated
    // ...
}
```

**FN-65 (default).** State postconditions too — especially effects invisible in the return value, such as "the mutex is released on exit" (`I.7`). Deviation from `I.7`: resource-release postconditions are enforced structurally by RAII rather than remembered by hand — a scoped guard cannot be forgotten the way a comment can. Deviation from `I.8`: likewise no `Ensures()`; remaining postconditions become asserts or contract comments.

### Failures Are Unignorable

**FN-66.** A failure to perform a required task must be impossible to ignore. Deviation from `I.10`: upstream routes required-task failures through exceptions; our response splits — programmer errors assert, expected recoverable failures return checked statuses, rare failures throw ([Error Handling](./error-handling.md)) — and `errno`-style codes survive only at ABI edges.

### Abstraction Boundaries

**FN-67.** Ugly but necessary techniques get wrapped once behind a clean interface, the suppression commented inside the abstraction (`I.30`); raw allocation, pointer arithmetic, and casting stay inside implementations — the standard library is the model, and low-level mess outside abstraction implementations is a review finding (`P.11`).

**FN-68.** Rule violations must never leak through an API into user code (the deviation-comment policy lives in [the Core Guidelines disposition](./core-guidelines-disposition.md)).

**FN-69 (default).** Module edges are the one boundary where the interface surface shrinks. Deviation from `I.26`: cross-compiler ABI compatibility is not a project target, so full C++ interfaces are fine in-process; the C-style subset discipline applies only at genuine module edges — total catches translating to status codes in [Error Handling](./error-handling.md), ABI-stable headers in [Quality Guidelines](./quality-guidelines.md).

Template parameters document themselves — a `static_assert` over standard traits (`std::is_integral<T>::value`) on C++14; **C++17:** the `_v` variable-template spelling; **C++20:** a named concept ([Templates and Generics](./templates-and-generics.md), `I.9`). Protocol interfaces stay pure — no data members, virtual destructor, deleted copies ([Classes and Hierarchies](./classes-and-hierarchies.md), `I.25`) — and headers distributed as binaries use Pimpl with an out-of-line destructor and move operations ([Quality Guidelines](./quality-guidelines.md), `I.27`).

---

## Quality Check

Gates before merging interface work: format-clean (`clang-format --dry-run`) and tidy-clean on changed sources, and the unit suite green.

Review checklist:

- [ ] Every parameter's role is readable from type and name; scalars by value, objects by `const T&`
- [ ] Text and sequences enter as views (C++17; C++14: `const std::string&` / pointer + size); nothing borrowed is stored without a documented owner
- [ ] Sinks take by value and `std::move`; no parallel view/non-view overloads
- [ ] No `return std::move(local)`; no pointer, reference, or view into a local escapes
- [ ] Multi-part results return structs; must-check marking (`[[nodiscard]]` on C++17) on every status/computation/factory
- [ ] Functions do one operation, fit a screen, keep impure effects at the edge
- [ ] Same-shape overloads collapsed into default arguments; `noexcept` only on proven-narrow interfaces
- [ ] Single-argument constructors `explicit` unless conversion is the design
- [ ] Magic numbers replaced by `constexpr`/`enum class`; observers are `const`

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
