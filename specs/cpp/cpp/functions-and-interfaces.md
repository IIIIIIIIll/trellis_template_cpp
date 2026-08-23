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

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
