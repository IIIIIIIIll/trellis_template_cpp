---
description: Curating the project's static-analysis check set
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp, **/test*/**, **/*_test.*, **/*Test.*, **/tests/**]
---

# Static Analysis

> A clang-tidy configuration is a maintained artifact: checks earn their place by measured yield on this codebase and lose it when noise buries signal.

---

## Overview

Static analysis is curated, never dumped: categories are not enabled wholesale, and `cppcoreguidelines-*` checks are adopted one by one, evaluated against this codebase, or skipped — each with the reason written down so the question is answered once. The check set changes with the rules it backs: an enable or a rejection lands in `.clang-tidy` (or here) in the same change that adopts or rejects the corresponding rule. Curation beats coverage — a check nobody reads is negative value.

---

## Static Analysis Curation

Default strength: default.

Caught by: review — no automated detector.

**QUAL-25.** clang-tidy earns its keep on changed sources only when curated — wholesale category dumps bury signal under hundreds of hits.

Worth enabling (low noise, high yield):

| Checks | Why |
|--------|-----|
| `bugprone-*` | Real defect patterns: use-after-move, dangling references, suspicious casts |
| `performance-*` | Unnecessary copies, pass-by-value misses, inefficient calls |
| `modernize-*` | Mechanical language hygiene (`use-override`, `use-nullptr`, `use-emplace`) |
| Selected `misc-*` (`misc-unused-*`) | Dead declarations and parameters |

**QUAL-26.** Individual `cppcoreguidelines-*` checks follow the same discipline — curated one by one, never enabled as a family.

Enable first — low noise, direct defect yield:

| Check | Guards against | Related rules |
|-------|----------------|---------------|
| `cppcoreguidelines-slicing` | Derived-to-base copies silently dropping the dynamic type | `C.67` |
| `cppcoreguidelines-init-variables` | Uninitialized locals | `ES.20` |
| `cppcoreguidelines-narrowing-conversions` | Lossy implicit conversions | `ES.46` |
| `cppcoreguidelines-pro-type-member-init` | Members left uninitialized | `C.48` |
| `cppcoreguidelines-special-member-functions` | Half-defined copy/move/destroy sets | `C.21` |
| `cppcoreguidelines-prefer-member-initializer` | Constructor-body assignments that belong in the init list | `C.49` |
| `cppcoreguidelines-pro-type-cstyle-cast` | C-style casts bypass every access check; named casts state intent | `ES.49` |

Slicing deserves the example: the compiler stays happy while behavior vanishes:

```cpp
// QUAL-26: borrow by const reference avoids slicing
// compiles; UB at runtime
// Wrong: HttpHandler sliced into Base on the way in; dispatch and fields gone.
void install(Base handler);
install(HttpHandler{});

// Right (C.67): borrow the object; storage decisions belong to the owner.
void install(const Base& handler);
```

Second wave — evaluate against your codebase before enabling:

| Check | Notes |
|-------|-------|
| `cppcoreguidelines-virtual-class-destructor` | Polymorphic bases need virtual destructors; noisy only where protected non-virtual destructors are deliberate |
| `cppcoreguidelines-no-malloc` | Flags `malloc`/`free`/`calloc`/`realloc`; aligns with the ownership ladder — drop the check if C interop dominates the tree |
| `cppcoreguidelines-pro-type-static-cast-downcast` | Unsound downcasts; the kind-tag dispatch under ODR and ABI Pitfalls below makes most of them unnecessary anyway |
| `cppcoreguidelines-avoid-non-const-global-variables` | Mutable globals are review bait; expect findings in legacy glue and fix or justify each one |
| `cppcoreguidelines-rvalue-reference-param-never-moved` | Sink parameters declared but never moved from; pairs with the pass-by rules in [Memory Discipline](../implement/memory-discipline.md) |

Skip with a written reason, not by omission:

| Check | Why skipped here |
|-------|------------------|
| `cppcoreguidelines-owning-memory` | Models `gsl::owner`; owning raw pointers are banned outright, so its findings duplicate review rules instead of adding yield |
| `cppcoreguidelines-avoid-magic-numbers` | High churn, low signal alongside normal review |

Leave off by default:

| Checks | Why off |
|--------|---------|
| `bugprone-easily-swappable-parameters` | Notoriously noisy; the parameter-role contract in [Functions and Interfaces](../design/functions-and-interfaces.md) fixes the design instead |
| `modernize-use-trailing-return-type` | Style churn; the local return-type convention already decides |
| `readability-identifier-naming` without a committed config | Churn generator unless the naming table ships beside the repo (see Naming Conventions above) |
| House-style families (`llvm-*`, `fuchsia-*`, ...) | Someone else's conventions; mechanical style belongs to clang-format |

**QUAL-27.** When a check lands in `.clang-tidy`, record it in the same change that adopts the corresponding rule; when a check is rejected, leave the reason here so the question is answered once.

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
