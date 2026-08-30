# Error Handling

> How errors are signaled, propagated, and handled in C++ code: choosing between exceptions, status returns, and asserts; `noexcept` discipline; and keeping failures contained at module boundaries.

---

## Overview

Every failure path uses exactly one of four mechanisms, picked by the *kind* of failure, not by author preference. The baseline is **C++17**; deviations relevant to C++20/23 are called out inline.

The core split:

1. **Programmer errors** (violated *internal* invariants, impossible states) are bugs. Use `assert`; do not design error paths for them.
2. **Expected, recoverable failures** (parse errors, missing config, full queue) are part of the function's contract. Return a status or an expected-like result.
3. **Rare failures the caller must react to** (allocation failure mid-operation, socket reset) throw exceptions.
4. **Unrecoverable corruption** terminates. Do not catch it into a "graceful" path.

One refinement keeps the rows honest: misuse by an in-process *public-API caller* throws a domain exception (see the worth-throwing table under Exceptions Policy) — catchable, not an assert, not a status. Asserts answer for the module's internal invariants only.

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

```cpp
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
// Wrong: a half-built object the caller must remember to check
Session s;
if (!s.init(cfg)) { /* hope every caller notices */ }

// Right: establishes the invariant or throws
Session s{cfg};   // usable, or never existed
```

**ERR-13.** State preconditions at the boundary so interface misuse is visible (`E.7`). Violations route through the decision table: internal assumptions become asserts; externally supplied values get checked status returns, because `NDEBUG` erases asserts from release builds.

**ERR-14 (default).** State postconditions with equal care (`E.8`): callers need no defensive re-checks, the guarantee travels in the signature and documentation, and verifying it follows the same trust-boundary logic as preconditions.

---

## C++17 Baseline: `std::expected` Is C++23

Caught by: review — no automated detector.

Default strength: hard.

**ERR-15.** On a C++17 codebase, pick one of, in order of preference — centralized behind one alias so migration is mechanical:

1. **`tl::expected`** — drop-in, API-compatible with `std::expected`. Preferred whenever a vetted third-party header-only dependency is acceptable.
2. **A local `Result<T, E>` alias** — minimal sum-type wrapper with `has_value()`, `value()`, `error()`.
3. **Status enum + out-parameter** — mandatory at ABI/module edges regardless of dialect (see below).

```cpp
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
// Usage — inspection shape identical to std::expected; errors are built by
// make_error in result.h, so the C++23 migration is a one-file change there
// plus deleting the alias
Result<Config, std::error_code> load_config(std::string_view path);

auto cfg = load_config(path);
if (!cfg) {
    return cfg.error();
}
use(cfg.value());
```

**ERR-16.** Every error construction routes through `make_error` in result.h — the C++23 migration stays a one-file change.

Migration path: when the toolchain moves to C++23, replace `tl::expected` with `<expected>` and re-point the alias. *Inspection* call sites (`has_value()`, `value()`, `error()`, `operator*`) do not change; *error-construction* call sites do — `tl::make_unexpected` becomes `std::unexpected`/`std::unexpect`, and the monadic combinators carry different names. That is exactly why every construction routes through `make_error` in result.h: the difference lives in one function body, and the swap stays a one-file change.

**ERR-17 (default).** Do **not** hand-roll monadic `.and_then()` chains in C++17 wrappers; keep the wrapper surface minimal so the future swap stays trivial.

Deviation from `E.27`: the rule scopes systematic error codes to codebases that cannot throw exceptions; this project adopts them past that premise. Expected-style status results remain the standing mechanism for anticipated failures and the mandatory currency at ABI edges, centralized behind the `Result` alias above so handling stays uniform.

---

## Exceptions Policy

Caught by: review — no automated detector.

Default strength: hard.

### Throw by Value, Catch by Const Reference

**ERR-18.** Throw temporaries, catch by `const&` (`E.15`). Catching by value slices derived types down to the handler's static type; catching by pointer invites lifetime questions and leaks. Rethrow with bare `throw;` so the original dynamic type survives — `throw e;` slices.

```cpp
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
// Wrong: pointer ownership ambiguity
catch (const std::exception* e) { delete e; }

// Right
catch (const std::exception& e) {
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

**ERR-24 (default).** Where no suitable resource handle exists, wrap the cleanup in a small scoped guard (`E.19` — covered in [Memory and Ownership](./memory-and-ownership.md)): a last resort beneath real RAII types, never a replacement for them.

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

## `noexcept` Discipline

Caught by: clang-tidy `performance-noexcept-move` (moves, swap); `bugprone-exception-escape` (noexcept bodies and destructors).

Default strength: hard.

**ERR-32.** Reserve `noexcept` for functions where exiting by a throw is impossible or unacceptable (`E.12`) — the specifier is a contract, and violating it calls `std::terminate()`.

| Function | `noexcept`? | Why |
|----------|-------------|-----|
| **ERR-33** Move constructor / move assignment | Yes (when no allocation) | Container growth depends on it |
| **ERR-34** `swap` | Yes | Same; enables the move-assign idiom |
| **ERR-35** Destructors | Implicitly yes | Never allow an exception to leave a destructor |
| **ERR-36 (default)** Leaf accessors provably free of throwing calls | Yes, optionally | Documents intent; enables optimizations |
| **ERR-37** Anything that allocates, logs, locks, formats, or calls unknown code | No | `std::bad_alloc` and friends would terminate |

**ERR-38.** Before marking, walk the callee tree mentally: a `noexcept` function that calls one logging helper that allocates is a latent crash. If unsure, leave it off — correctness first, then measure.

```cpp
// Wrong: terminate() at runtime — push_back can throw bad_alloc
std::vector<int> snapshot() noexcept {          // NO
    std::vector<int> v;
    v.reserve(size());
    // ...
    return v;
}

// Right: reserve the specifier for what holds
bool empty() const noexcept { return count_ == 0; }
void clear() noexcept;
```

```cpp
// Conditional specification when delegating
template <typename T>
void chain(T&& next) noexcept(noexcept(next.step())) {
    next.step();
}
```

**ERR-39.** Express "this cannot throw" with `noexcept` (or conditional `noexcept(expr)`), never with a `throw(...)` list.

Historical footnote (`E.30`): dynamic exception specifications (`throw(X, Y)`) were removed from the language because library changes bubbled into crashes up long call chains.

Caught by: the compiler — dynamic exception specifications are ill-formed in C++17.

---

## Propagation Across Module Boundaries

Caught by: review — no automated detector at module edges.

Default strength: hard.

**ERR-40.** C++ exceptions never cross ABI boundaries: not out of a shared library, not into it from a callback, not across an `extern "C"` edge. Different compilers, STL versions, or build flags produce incompatible exception representations; letting one fly across such an edge is undefined behavior, not a caught error.

- **ERR-41.** Public entry points catch everything and translate to **status codes or POD error structs**.
- **ERR-42.** Callbacks invoked *by* the foreign side wrap their body in a total catch before returning.
- **ERR-43.** Do not pass live STL objects (strings, vectors, exceptions) across the edge; pass buffers and plain structs.

```cpp
// module_api.cpp — compiled inside the shared library
extern "C" int mylib_parse(const char* bytes, size_t len, MylibDoc** out) {
    try {
        auto doc = parse_doc(std::string_view{bytes, len});
        *out = release_to_c(doc);
        return MYLIB_OK;
    } catch (const std::bad_alloc&) {
        return MYLIB_OUT_OF_MEMORY;
    } catch (const ParseError& e) {
        set_last_error(e.what());      // thread-local message buffer
        return MYLIB_PARSE_ERROR;
    } catch (const std::exception& e) {
        set_last_error(e.what());
        return MYLIB_ERROR;
    } catch (...) {
        return MYLIB_UNKNOWN;          // foreign exceptions stop HERE
    }
}

// callback.cpp — host calls INTO us; exceptions must not leak upward
extern "C" int trampoline(void* ctx, const Event* ev) {
    try {
        static_cast<Handler*>(ctx)->on_event(*ev);
        return 0;
    } catch (...) {
        return 1;
    }
}
```

**ERR-44.** The same rule applies between modules built with the *same* compiler when flags differ (e.g., `_GLIBCXX_USE_CXX11_ABI` mismatches): treat any independently deployed binary as a foreign world.

Deviation from `E.25`: the rule addresses builds where exceptions are unavailable, simulating RAII behind `valid()` checks. This codebase runs exceptions by default, so that simulation stays hypothetical; its live residue is precisely this policy — RAII-managed results are translated to status codes at the edge rather than carried across the ABI.

**ERR-45.** Failures travel with the return value everywhere, never in `errno`-style global flags (`E.28`). The one deliberate difference: the shim's `set_last_error` thread-local message buffer above supplements the status code for diagnostics — it never replaces the code as the success/failure signal.

---

## Logging vs Handling

Caught by: review — no automated detector.

**ERR-46 (hard).** A `catch` block does exactly **one** of three things:

1. **Handles** — recovers and continues, having full context.
2. **Annotates and rethrows** — adds information, preserves the cause.
3. **Deliberately ignores** — with a comment stating why silence is safe.

```cpp
// Deliberate ignore, documented — the third sanctioned behavior
try {
    legacy_file.close();
} catch (const std::exception&) {
    // Best-effort cleanup during shutdown; nothing actionable remains.
}
```

**ERR-47 (hard).** Logging *and then* swallowing is forbidden: it reports failure to whoever reads logs while telling the caller (via return value) that everything succeeded.

```cpp
// Wrong: log-and-swallow — caller sees success, ops sees a scary line
} catch (const std::exception& e) {
    LOG(ERROR) << "save failed: " << e.what();
}

// Right: handle where the retry loop lives
} catch (const TransientError&) {
    schedule_retry(attempt_++);
}
```

**ERR-48 (hard).** Catch only where meaningful recovery exists (`E.17`); everywhere else let the exception propagate while RAII unwinds cleanup.

**ERR-49 (default).** Minimize explicit `try`/`catch` (`E.18`): resource cleanup belongs in RAII objects, and the sanctioned dense-catch zone is the total catch at module edges.

**ERR-50 (default).** Log a given failure **once**, at the layer that finally handles it (or at the top-level sink). Annotation layers add context via nested exceptions, not duplicate log lines.

**ERR-51 (hard).** Use bare `throw;` to rethrow; `throw_with_nested` (not manual nested-type conventions) to wrap.

```cpp
// Wrong: rethrow by value — slices and loses the derived type
} catch (const std::exception& e) {
    throw e;
}

// Right: annotate with context, preserve the original via nesting
} catch (const std::exception& e) {
    std::throw_with_nested(std::runtime_error(
        std::string{"loading config '"} + path_ + "': " + e.what()));
}
```

**ERR-52 (default).** The annotation path only delivers its context if the top-level sink unwinds it: walk the chain with `std::rethrow_if_nested` and print each layer's `what()` — an annotation nobody unwinds is context written and never read.

## Quality Check

Before merging error-handling code, confirm:

- [ ] Each failure uses the mechanism matching its row in the decision table
- [ ] `assert` never validates external input; throws never report internal bugs
- [ ] All thrown types derive from the project base; all catches are `const&`
- [ ] Move constructor, move assignment, and `swap` are `noexcept` where claimed
- [ ] No `noexcept` on any function whose callees can allocate, log, or format
- [ ] Every exported module function and callback trampoline has a total catch translating to status codes
- [ ] Every `catch` handles, annotates-and-rethrows (`throw;`), or documents the ignore
- [ ] Each failure is logged exactly once, at the layer that handles it

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
