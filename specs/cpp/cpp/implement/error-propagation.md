---
description: noexcept discipline, propagation across module boundaries, logging versus handling
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Error Propagation

> How failures travel through running code: `noexcept` discipline, propagation across module and ABI boundaries, and the logging-versus-handling rules that keep every failure reported exactly once.

---

## Overview

Once a mechanism is chosen — the decision table lives in [Error Contracts](../design/error-contracts.md) — failures must travel without leaking resources, terminating innocents, or being reported twice. `noexcept` is a contract measured against the callee tree, not decoration: it belongs on move operations, `swap`, and provably-throw-free leaf accessors, and stays off anything that allocates, logs, locks, or calls unknown code, because a violated specifier calls `std::terminate()`. At module edges, exceptions never cross ABI boundaries: exported entry points and callback trampolines run a total catch and translate to status codes or POD error structs, and that dense-catch zone is the one sanctioned home for wide handlers. A `catch` block does exactly one of three things — handles, annotates and rethrows, or documents why silence is safe — because logging-then-swallowing lies to both the caller and the on-call, and every failure is logged exactly once, at the layer that finally handles it.

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
// ERR-38: reserve noexcept for functions that cannot throw
// compiles; UB at runtime
// Wrong: terminate() at runtime — push_back can throw bad_alloc
std::vector<int> snapshot() noexcept {          // NO
    std::vector<int> v;
    v.reserve(size());
    // ...
    return v;
}

// Right: reserve the specifier for what holds
struct Stats {
    bool empty() const noexcept { return count_ == 0; }
    void clear() noexcept;

private:
    std::size_t count_ = 0;
};
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
// C++17
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
// ERR-47: handle failures, never log and swallow
// compiles; UB at runtime
// Wrong: log-and-swallow — caller sees success, ops sees a scary line
try {
    save_document();
} catch (const std::exception& e) {
    LOG(ERROR) << "save failed: " << e.what();
}

// Right: handle where the retry loop lives
try {
    save_document();
} catch (const TransientError&) {
    schedule_retry(attempt_++);
}
```

**ERR-48 (hard).** Catch only where meaningful recovery exists (`E.17`); everywhere else let the exception propagate while RAII unwinds cleanup.

**ERR-49 (default).** Minimize explicit `try`/`catch` (`E.18`): resource cleanup belongs in RAII objects, and the sanctioned dense-catch zone is the total catch at module edges.

**ERR-50 (default).** Log a given failure **once**, at the layer that finally handles it (or at the top-level sink). Annotation layers add context via nested exceptions, not duplicate log lines.

**ERR-51 (hard).** Use bare `throw;` to rethrow; `throw_with_nested` (not manual nested-type conventions) to wrap.

```cpp
// ERR-51: bare throw rethrows, throw_with_nested wraps
// compiles; UB at runtime
// Wrong: rethrow by value — slices and loses the derived type
try {
    load();
} catch (const std::exception& e) {
    throw e;
}

// Right: annotate with context, preserve the original via nesting
try {
    load();
} catch (const std::exception& e) {
    std::throw_with_nested(std::runtime_error(
        std::string{"loading config '"} + path_ + "': " + e.what()));
}
```

**ERR-52 (default).** The annotation path only delivers its context if the top-level sink unwinds it: walk the chain with `std::rethrow_if_nested` and print each layer's `what()` — an annotation nobody unwinds is context written and never read.

## Quality Check

Before merging error-propagation code, confirm:

- [ ] Move constructor, move assignment, and `swap` are `noexcept` where claimed
- [ ] No `noexcept` on any function whose callees can allocate, log, or format
- [ ] Every exported module function and callback trampoline has a total catch translating to status codes
- [ ] Every `catch` handles, annotates-and-rethrows (`throw;`), or documents the ignore
- [ ] Each failure is logged exactly once, at the layer that handles it

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
