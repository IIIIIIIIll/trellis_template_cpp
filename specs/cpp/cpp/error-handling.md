# Error Handling

> How errors are signaled, propagated, and handled in C++ code: choosing between exceptions, status returns, and asserts; `noexcept` discipline; and keeping failures contained at module boundaries.

---

## Overview

Every failure path uses exactly one of four mechanisms, picked by the *kind* of failure, not by author preference. The baseline is **C++17**; deviations relevant to C++20/23 are called out inline.

The core split:

1. **Programmer errors** (violated invariants, impossible states) are bugs. Use `assert`; do not design error paths for them.
2. **Expected, recoverable failures** (parse errors, missing config, full queue) are part of the function's contract. Return a status or an expected-like result.
3. **Rare failures the caller must react to** (allocation failure mid-operation, socket reset) throw exceptions.
4. **Unrecoverable corruption** terminates. Do not catch it into a "graceful" path.

---

## Choosing a Mechanism

| Situation | Mechanism | Example |
|-----------|-----------|---------|
| Violated internal invariant ("cannot happen") | `assert` (active in debug; gone under `NDEBUG`) | internal lookup table index out of range |
| Invalid input from *outside* the trust boundary | Status return or expected-style result | malformed user-supplied config value |
| Anticipated failure the caller routinely handles | Status return or expected-style result | key not found in cache; end-of-input |
| Rare failure, no local recovery possible, stack unwinding useful | Exception | `std::bad_alloc`, connection dropped mid-request |
| Object/state corrupted beyond repair | Terminate (default: let it escape) | heap corruption detected by allocator |

```cpp
// Wrong: exceptions for ordinary control flow
Item find(const Map& m, Key k) {
    try {
        return m.at(k);
    } catch (const std::out_of_range&) {
        return Item{};              // miss is normal, not exceptional
    }
}

// Wrong: error codes for genuine invariants
int slot = table_index(key);        // returns -1 on "impossible" state
if (slot < 0) return FAIL;          // hides a bug instead of surfacing it

// Right: misses are values, bugs are asserts
std::optional<Item> find(const Map& m, Key k) { return m.lookup(k); }

void put(Table& t, Key key, Value v) {
    int slot = table_index(key);
    assert(slot >= 0 && "hash invariant violated");   // bug, not input problem
    t[slot] = std::move(v);
}
```

Never validate external input with `assert`: under `NDEBUG` the check vanishes and malformed input walks straight into memory-unsafe code.

---

## C++17 Baseline: `std::expected` Is C++23

`std::expected<T, E>` arrived in **C++23**. On a C++17 codebase, pick one of, in order of preference:

1. **`tl::expected`** — drop-in, API-compatible with `std::expected`. Preferred whenever a vetted third-party header-only dependency is acceptable.
2. **A local `Result<T, E>` alias** — minimal sum-type wrapper with `has_value()`, `value()`, `error()`.
3. **Status enum + out-parameter** — mandatory at ABI/module edges regardless of dialect (see below).

Centralize the choice behind one alias so migration is mechanical:

```cpp
// result.h — single point of definition
#include <tl/expected.hpp>

template <typename T, typename E>
using Result = tl::expected<T, E>;

inline std::error_code make_error(ParseErr e) { return std::error_code{e}; }
```

```cpp
// Usage — identical shape to std::expected, so the C++23 migration is a
// one-line change in result.h plus deleting the alias
Result<Config, std::error_code> load_config(std::string_view path);

auto cfg = load_config(path);
if (!cfg) {
    return cfg.error();
}
use(cfg.value());
```

Migration path: when the toolchain moves to C++23, replace `tl::expected` with `<expected>` and re-point the alias. Call sites do not change. Do **not** hand-roll monadic `.and_then()` chains in C++17 wrappers; keep the wrapper surface minimal so the future swap stays trivial.

---

## Exceptions Policy

### Throw by Value, Catch by Const Reference

Throw temporaries; catch by `const&`. Catching by value slices derived types down to the handler's static type; catching by pointer invites lifetime questions and leaks.

```cpp
// Wrong: slicing — handler sees only ValidationError, loses SqlError fields
try {
    run();
} catch (ValidationError e) {          // by value
    log(e.code());
}

// Wrong: pointer ownership ambiguity
catch (const std::exception* e) { delete e; }

// Right
try {
    run();
} catch (const ValidationError& e) {
    log(e.code());
} catch (const std::exception& e) {
    log(e.what());
}
```

### Exception Types

- All thrown types derive from a **single project base** deriving from `std::exception`.
- Throw the most specific type; catch the most general type you can actually act on.
- Never throw non-`std::exception` types (ints, pointers, strings) — they bypass every `catch (const std::exception&)` safety net.

### Which Failures Are Worth Throwing vs Asserting

| Condition | Tool | Rationale |
|-----------|------|-----------|
| Caller passed garbage across a public API boundary | Throw (`std::invalid_argument` or domain type) | Caller error is runtime reality; must be catchable |
| Internal invariant broke | `assert` | It is a bug; unwinding cannot fix it, reporting should be loud and cheap |
| Resource exhaustion (`bad_alloc`) | Let it propagate | Usually fatal; only unwind if a top level genuinely frees memory and retries |
| Timeout / transient I/O failure | Domain exception or status | Depends on whether callers routinely branch on it (see decision table) |

### Nothrow Move and Swap Are Part of the Contract

Types stored in containers must have `noexcept` move operations. `std::vector` growth moves elements only when the move constructor is `noexcept`; otherwise it falls back to copying — a silent, per-type performance cliff.

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

A moved-from object must be destructible and assignable; its other state is valid-but-unspecified. Document that on the type.

---

## `noexcept` Discipline

Mark `noexcept` **only** what truly cannot throw — the specifier is a contract, and violating it calls `std::terminate()`.

| Function | `noexcept`? | Why |
|----------|-------------|-----|
| Move constructor / move assignment | Yes (when no allocation) | Container growth depends on it |
| `swap` | Yes | Same; enables the move-assign idiom |
| Destructors | Implicitly yes | Never allow an exception to leave a destructor |
| Leaf accessors provably free of throwing calls | Yes, optionally | Documents intent; enables optimizations |
| Anything that allocates, logs, locks, formats, or calls unknown code | No | `std::bad_alloc` and friends would terminate |

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

// Right: conditional specification when delegating
template <typename T>
void chain(T&& next) noexcept(noexcept(next.step())) {
    next.step();
}
```

Before marking, walk the callee tree mentally: a `noexcept` function that calls one logging helper that allocates is a latent crash. If unsure, leave it off — correctness first, then measure.

---

## Propagation Across Module Boundaries

**C++ exceptions never cross ABI boundaries**: not out of a shared library, not into it from a callback, not across an `extern "C"` edge. Different compilers, STL versions, or build flags produce incompatible exception representations; letting one fly across such an edge is undefined behavior, not a caught error.

Rules at every module edge (shared library, plugin, C API shim):

1. Public entry points catch everything and translate to **status codes or POD error structs**.
2. Callbacks invoked *by* the foreign side wrap their body in a total catch before returning.
3. Do not pass live STL objects (strings, vectors, exceptions) across the edge; pass buffers and plain structs.

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

The same rule applies between modules built with the *same* compiler when flags differ (e.g., `_GLIBCXX_USE_CXX11_ABI` mismatches): treat any independently deployed binary as a foreign world.

---

## Logging vs Handling

A `catch` block does exactly **one** of three things:

1. **Handles** — recovers and continues, having full context.
2. **Annotates and rethrows** — adds information, preserves the cause.
3. **Deliberately ignores** — with a comment stating why silence is safe.

Logging *and then* swallowing is forbidden: it reports failure to whoever reads logs while telling the caller (via return value) that everything succeeded.

```cpp
// Wrong: log-and-swallow — caller sees success, ops sees a scary line
} catch (const std::exception& e) {
    LOG(ERROR) << "save failed: " << e.what();
}

// Wrong: rethrow by value — slices and loses the derived type
} catch (const std::exception& e) {
    throw e;
}

// Right: annotate with context, preserve the original via nesting
} catch (const std::exception& e) {
    std::throw_with_nested(std::runtime_error(
        std::string{"loading config '"} + path_ + "': " + e.what()));
}

// Right: handle where the retry loop lives
} catch (const TransientError&) {
    schedule_retry(attempt_++);
}

// Right: deliberate ignore, documented
try {
    legacy_file.close();
} catch (const std::exception&) {
    // Best-effort cleanup during shutdown; nothing actionable remains.
}
```

Log a given failure **once**, at the layer that finally handles it (or at the top-level sink). Annotation layers add context via nested exceptions, not duplicate log lines. Use bare `throw;` to rethrow; `throw_with_nested` (not manual nested-type conventions) to wrap.

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

## Complete Coverage: E

Census of the remaining ISO C++ Core Guidelines error-handling rules, each given an explicit disposition. Section-level stance comes from [Core Guidelines Alignment](./core-guidelines-alignment.md): the Guidelines' exception-centric default is adapted to this project's four-mechanism split wherever the two disagree.

| Rule | Stance | Disposition |
|------|--------|-------------|
| `E.1` | Adopt | An error-handling strategy cannot be retrofitted onto finished interfaces; fix the assert-versus-status-versus-throw split from the decision table at design time, before signatures hard-code a mechanism. |
| `E.2` | Adapt | A function that cannot perform its task must report it, but the signal follows the failure kind here: rare caller-reactable failures throw, internal bugs assert, and routine misses return as statuses — never one blanket answer. |
| `E.3` | Adopt | Exceptions carry failures, never ordinary control flow: loop termination and cache misses are normal outcomes, and implementations optimize on exactly that assumption. |
| `E.4` | Adopt | Invariants decide what counts as an error; design handling so that after recovery every surviving object is valid again, which is why the constructor-establishes-invariant discipline feeds straight into error paths. |
| `E.5` | Adopt | A constructor either establishes the class invariant or throws — no half-built objects callers must remember to check; the class-design side of invariant discipline lives in Classes and Hierarchies. |
| `E.7` | Adopt | State preconditions at the boundary so interface misuse is visible, and route violations through the decision table: internal assumptions become asserts, externally supplied values get checked status returns, because `NDEBUG` erases asserts from release builds. |
| `E.8` | Adopt | State postconditions so callers need no defensive re-checks; the guarantee travels in the signature and documentation, and verifying it follows the same trust-boundary logic as preconditions. |
| `E.12` | Adopt | Reserve `noexcept` for functions where exiting by a throw is impossible or unacceptable — the `noexcept` Discipline table operationalizes this, including the walk-the-callee-tree check before marking. |
| `E.13` | Adopt | Throwing while directly owning a bare resource is a leak; the ownership ladder dissolves the hazard structurally — allocations live in RAII owners whose destructors run during unwinding, and stray cleanup happens before the throw or via a scoped guard. |
| `E.14` | Adapt | Stricter than the rule: every thrown type derives from the single project base under `std::exception`, so built-in-type throws and free-floating enum values — tolerated upstream — are banned for bypassing generic `catch (const std::exception&)` handlers. |
| `E.15` | Adopt | Throw temporaries, catch by `const&`: catching by value slices, catching by pointer invites lifetime questions, and rethrows use bare `throw;` so the original dynamic type survives. |
| `E.16` | Adopt | Destructors, deallocation functions, `swap`, and the copy/move constructors of thrown types must never exit by an exception — standard-library basic guarantees assume it, and the `noexcept` table plus the container-move requirement enforce it. |
| `E.17` | Adopt | Catch only where meaningful recovery exists; everywhere else let the exception propagate while RAII unwinds cleanup, and log the failure once, at the layer that finally handles it. |
| `E.18` | Adopt | Each `try` block earns its place by handling, annotating-and-rethrowing, or deliberately ignoring; resource cleanup belongs in RAII objects, and the sanctioned dense-catch zone is the total catch at module edges. |
| `E.19` | Covered elsewhere | Cleanup when no suitable resource handle exists maps to the small scoped guards of [Memory and Ownership](./memory-and-ownership.md) — a last resort beneath real RAII types, never a replacement for them. |
| `E.25` | Adapt | This codebase runs exceptions by default, so the `valid()`-checking simulation stays hypothetical; its live residue is the module-edge policy, where RAII results are translated to status codes instead of being carried across ABI. |
| `E.26` | Adapt | Failing fast survives only for unrecoverable corruption — terminate, or abort inside edge shims; allocation exhaustion is not failed fast, because `bad_alloc` propagates so a top level can decide whether a retry is real. |
| `E.27` | Adapt | Systematic error codes are adopted beyond the rule's no-exceptions premise: expected-style status results are the standing mechanism for anticipated failures and the mandatory currency at ABI edges, centralized behind the `Result` alias so handling stays uniform. |
| `E.28` | Adapt | Failures travel with the return value, never in `errno`-style global flags; the one deliberate difference is the module-edge shim's documented thread-local message buffer, which supplements — never replaces — the status code. |
| `E.30` | Adopt | Dynamic exception specifications (`throw(X, Y)`) were removed from the language because library changes bubbled into crashes up long call chains; express the impossible case with `noexcept` instead. |
| `E.31` | Adopt | Handlers match in source order, so order catches most-derived-first and put `catch (...)` last — a hidden handler is dead code that quietly changes behavior. |

---

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
