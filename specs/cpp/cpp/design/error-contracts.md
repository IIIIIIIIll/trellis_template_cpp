---
description: Choosing between exceptions, status returns, and asserts; failure contracts at API boundaries
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Error Contracts

> How failures are signaled at design time: choosing between exceptions, status returns, and asserts; stating invariants, preconditions, and postconditions; and keeping expected-style results centralized so the C++23 migration stays mechanical.

---

## Overview

Mechanism choice is a design-time, one-way decision: an error-handling strategy cannot be retrofitted onto finished interfaces, so the assert-versus-status-versus-throw split is fixed while signatures are still fluid. The choice follows the *kind* of failure, never author preference — internal invariant violations are bugs that assert, anticipated failures are part of the contract and return a status or expected-style result, rare caller-reactable failures throw, and corruption beyond repair terminates. Contracts carry the same weight as mechanisms: a constructor either establishes the class invariant or throws, preconditions are stated at the boundary so misuse is visible, and postconditions are promised with equal care. Expected-style results are centralized behind one `Result` alias from day one, thrown types form a single hierarchy under `std::exception`, and every handler catches by `const&` — the failure contract at an API boundary is as much a part of the signature as its parameters. The implementation half — `noexcept` discipline, propagation across module boundaries, and logging versus handling — lives in [Error Propagation](../implement/error-propagation.md).

---

## Choosing a Mechanism

Caught by: review — no automated detector for mechanism choice.

Default strength: hard.

| Situation | Mechanism | Example |
|-----------|-----------|---------|
| **ERR-1** Violated internal invariant ("cannot happen") | `assert` (active in debug; gone under `NDEBUG`) | internal lookup table index out of range |
| **ERR-2** Invalid input from *outside* the trust boundary | Status return or expected-style result | malformed user-supplied config value |
| **ERR-3** Anticipated failure the caller routinely handles | Status return or expected-style result | key not found in cache; end-of-input |
| **ERR-4** Rare failure, no local recovery possible, stack unwinding useful | Exception | `std::bad_alloc`; a control-channel drop with no retry path |
| **ERR-5** Object/state corrupted beyond repair | Terminate (default: let it escape) | heap corruption detected by allocator |

The exception row is for failures the caller cannot meaningfully branch on: allocation exhaustion, a control-channel drop with no retry path. Routine I/O failures — timeouts, transient resets on data paths callers already retry — are anticipated failures and default to the status row.

Two design-time corollaries keep this table honest.

**ERR-6.** An error-handling strategy cannot be retrofitted onto finished interfaces (`E.1`): fix the assert-versus-status-versus-throw split while signatures are still fluid, before callers hard-code a mechanism.

**ERR-7.** Exceptions carry failures, never ordinary control flow (`E.3`): loop termination and cache misses are normal outcomes, and implementations optimize on exactly that assumption.

The cost shape justifies the split: a non-throwing path is effectively free under table-driven unwinding, while a thrown exception typically costs three to four orders of magnitude more than a status check. On a hot loop a throw on any foreseeable failure dominates the budget — [Performance](../implement/performance.md)'s measurement discipline (`PERF-1`) decides where that cost is acceptable.

```cpp
// C++17
// ERR-7: exceptions never carry ordinary control flow
// compiles; UB at runtime
// Wrong: exceptions for ordinary control flow
Item find(const Map& m, Key k) {
    try {
        return m.at(k);
    } catch (const std::out_of_range&) {
        return Item{};              // miss is normal, not exceptional
    }
}

// Right: misses are values
std::optional<Item> find(const Map& m, Key k) { return m.lookup(k); }
```

**ERR-8.** Never validate external input with `assert`: under `NDEBUG` the check vanishes and malformed input walks straight into memory-unsafe code.

```cpp
// ERR-8: assert internal invariants, never external input
// compiles; UB at runtime
// Wrong: error codes for genuine invariants
int slot = table_index(key);        // returns -1 on "impossible" state
if (slot < 0) return FAIL;          // hides a bug instead of surfacing it

// Right: bugs are asserts
void put(Table& t, Key key, Value v) {
    int slot = table_index(key);
    assert(slot >= 0 && "hash invariant violated");   // bug, not input problem
    t[slot] = std::move(v);
}
```

**ERR-9.** Assert expressions must be side-effect free for the same reason — the whole expression vanishes under `NDEBUG`, so `assert(flush_cache())` silently stops flushing in release builds.

Deviation from `E.2`: upstream says a function that cannot perform its assigned task throws. Here the signal follows the failure kind instead — rare caller-reactable failures throw, internal bugs assert, routine misses return statuses — never one blanket answer.

**ERR-10.** Failing fast belongs to the last row only (`E.26`; upstream frames it for builds without exceptions — the principle transfers verbatim): corruption beyond repair terminates immediately — inside module-edge shims, abort rather than translate. Allocation exhaustion deliberately does *not* fail fast: `std::bad_alloc` propagates so a top level that genuinely frees memory can decide whether a retry is real.

---

## Contracts: Invariants, Preconditions, Postconditions

Caught by: review — no automated detector.

Default strength: hard.

**ERR-11.** The decision table classifies failures; contracts decide what counts as one (`E.4`). Design each type around invariants, and design handling so that after recovery every surviving object is valid again — which is why the constructor-establishes-invariant discipline feeds straight into error paths.

**ERR-12.** A constructor either establishes the class invariant or throws (`E.5`); there are no half-built objects callers must remember to check. The class-design side of invariant discipline lives in [Classes and Hierarchies](./classes-and-hierarchies.md).

```cpp
// ERR-12: constructor establishes the invariant or throws
// compiles; UB at runtime
// Wrong: a half-built object the caller must remember to check
Session s;
if (!s.init(cfg)) { /* hope every caller notices */ }

// Right: establishes the invariant or throws
Session s{cfg};   // usable, or never existed
```

**ERR-13.** State preconditions at the boundary so interface misuse is visible (`E.7`). Violations route through the decision table: internal assumptions become asserts; externally supplied values get checked status returns, because `NDEBUG` erases asserts from release builds.

**ERR-14 (default).** State postconditions with equal care (`E.8`): callers need no defensive re-checks, the guarantee travels in the signature and documentation, and verifying it follows the same trust-boundary logic as preconditions.

---

## `std::expected` Is C++23

Caught by: review — no automated detector.

Default strength: hard.

**ERR-15.** Expected-style results are not a C++23 luxury — on the C++14
baseline, pick one of, in order of preference, centralized behind one alias
so migration is mechanical:

1. **`tl::expected`** — drop-in, API-compatible with `std::expected`, and
   runs on C++14 toolchains. Preferred whenever a vetted third-party
   header-only dependency is acceptable.
2. **A local `Result<T, E>` alias** — minimal sum-type wrapper with `has_value()`, `value()`, `error()`.
3. **Status enum + out-parameter** — the dependency-free C++14 spelling, and
   mandatory at ABI/module edges regardless of dialect (see below).

```cpp
// C++17
// result.h — single point of definition
#include <tl/expected.hpp>

template <typename T, typename E>
using Result = tl::expected<T, E>;

// Enum-backed error codes need the standard traits hook before the line
// above compiles: specialize std::is_error_code_enum<ParseErr> and provide
// an error_category. Keep that wiring beside Result, never at call sites.

// Error construction funnels through make_error: the C++23 swap re-points
// this one body to std::unexpected, and no call site learns either spelling.
template <typename E>
auto make_error(E&& e) {
    return tl::make_unexpected(std::forward<E>(e));
}
```

```cpp
// C++17
// Usage — inspection shape identical to std::expected; errors are built by
// make_error in result.h, so the C++23 migration is a one-file change there
// plus deleting the alias
#include "result.h"

Result<Config, std::error_code> load_config(std::string_view path);

auto cfg = load_config(path);
if (!cfg) {
    return cfg.error();
}
use(cfg.value());
```

**ERR-16.** Every error construction routes through `make_error` in result.h — the C++23 migration stays a one-file change.

Migration path: when the toolchain moves to C++23, replace `tl::expected` with `<expected>` and re-point the alias. *Inspection* call sites (`has_value()`, `value()`, `error()`, `operator*`) do not change; *error-construction* call sites do — `tl::make_unexpected` becomes `std::unexpected`/`std::unexpect`, and the monadic combinators carry different names. That is exactly why every construction routes through `make_error` in result.h: the difference lives in one function body, and the swap stays a one-file change.

**ERR-17 (default).** Do **not** hand-roll monadic `.and_then()` chains in expected-style wrappers; keep the wrapper surface minimal so the future swap stays trivial.

Deviation from `E.27`: the rule scopes systematic error codes to codebases that cannot throw exceptions; this project adopts them past that premise. Expected-style status results remain the standing mechanism for anticipated failures and the mandatory currency at ABI edges, centralized behind the `Result` alias above so handling stays uniform.

---

## Exceptions Policy

Caught by: review — no automated detector.

Default strength: hard.

### Throw by Value, Catch by Const Reference

**ERR-18.** Throw temporaries, catch by `const&` (`E.15`). Catching by value slices derived types down to the handler's static type; catching by pointer invites lifetime questions and leaks. Rethrow with bare `throw;` so the original dynamic type survives — `throw e;` slices.

```cpp
// ERR-18: catch by const reference avoids slicing
// compiles; UB at runtime
// Wrong: slicing — handler sees only ValidationError, loses SqlError fields
try {
    run();
} catch (ValidationError e) {          // by value
    log(e.code());
}

// Right
try {
    run();
} catch (const ValidationError& e) {
    log(e.code());
} catch (const std::exception& e) {
    log(e.what());
}
```

The pointer form:

```cpp
// ERR-18: catch by reference, never by pointer
// compiles; UB at runtime
// Wrong: pointer ownership ambiguity
try {
    run();
} catch (const std::exception* e) { delete e; }

// Right
try {
    run();
} catch (const std::exception& e) {
    log(e.what());
}
```

**ERR-19.** Handler order is part of the contract (`E.31`): clauses match in source order, so catch most-derived first and put `catch (...)` last — the snippets above follow exactly that shape, since an earlier hidden handler is dead code that quietly changes behavior.

### Exception Types

- **ERR-20.** All thrown types derive from a **single project base** deriving from `std::exception`.
- **ERR-21 (default).** Throw the most specific type; catch the most general type you can actually act on.
- **ERR-22.** Never throw non-`std::exception` types (ints, pointers, strings) — they bypass every `catch (const std::exception&)` safety net.

Deviation from `E.14`: stricter than the rule — every thrown type derives from the single project base under `std::exception`; built-in-type throws and free-floating enum values, tolerated upstream, are banned here for bypassing every generic `catch (const std::exception&)` safety net.

### Throwing Without Leaking

**ERR-23.** Never throw while being the direct owner of a bare resource (`E.13`): the handle leaks unless unwinding can reach its manager. The ownership ladder dissolves this hazard structurally — allocations live in RAII owners whose destructors run during unwinding, and any stray cleanup happens before the throw or via a scoped guard.

Caught by: ASan's LeakSanitizer — the handle leaks during unwinding.

**ERR-24 (default).** Where no suitable resource handle exists, wrap the cleanup in a small scoped guard (`E.19` — covered in [Memory Discipline](../implement/memory-discipline.md)): a last resort beneath real RAII types, never a replacement for them.

Caught by: review — no automated detector.

### Which Failures Are Worth Throwing vs Asserting

| Condition | Tool | Rationale |
|-----------|------|-----------|
| **ERR-25** Caller passed garbage across a public API boundary | Throw (`std::invalid_argument` or domain type) | Caller error is runtime reality; must be catchable |
| **ERR-26** Internal invariant broke | `assert` | It is a bug; unwinding cannot fix it, reporting should be loud and cheap |
| **ERR-27** Resource exhaustion (`bad_alloc`) | Let it propagate | Usually fatal; only unwind if a top level genuinely frees memory and retries |
| **ERR-28 (default)** Timeout / transient I/O failure | Domain exception or status | Depends on whether callers routinely branch on it (see decision table) |

### Nothrow Move and Swap Are Part of the Contract

Caught by: clang-tidy `performance-noexcept-move` (moves and swap); review elsewhere.

**ERR-29.** Types stored in containers must have `noexcept` move operations. `std::vector` growth moves elements only when the move constructor is `noexcept`; otherwise it falls back to copying — a silent, per-type performance cliff.

```cpp
// ERR-29: mark move operations noexcept for reallocation
// compiles; UB at runtime
// Wrong: vector<Buffer> will COPY on reallocation
class Buffer {
public:
    Buffer(Buffer&& other)                 // not noexcept
        : data_(std::exchange(other.data_, nullptr)) {}
private:
    uint8_t* data_;
};

// Right
class Buffer {
public:
    Buffer(Buffer&& other) noexcept
        : data_(std::exchange(other.data_, nullptr)) {}
    Buffer& operator=(Buffer&& other) noexcept {
        Buffer tmp(std::move(other));
        swap(tmp);
        return *this;
    }
    void swap(Buffer& other) noexcept { std::swap(data_, other.data_); }
private:
    uint8_t* data_;
};
```

**ERR-30.** A moved-from object must be destructible and assignable; its other state is valid-but-unspecified. Document that on the type.

**ERR-31.** `E.16` extends the same demand across the machinery: destructors, deallocation functions, `swap`, and the copy/move constructors of thrown types must never exit by an exception — standard-library basic guarantees assume it. The `noexcept` Discipline table below plus the container-move requirement above enforce it.

---

## Quality Check

Before merging error-contract decisions, confirm:

- [ ] Each failure uses the mechanism matching its row in the decision table
- [ ] `assert` never validates external input; throws never report internal bugs
- [ ] All thrown types derive from the project base; all catches are `const&`

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
