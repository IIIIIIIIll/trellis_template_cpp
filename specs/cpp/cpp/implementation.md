---
description: Implementation-phase C++ reading path: coding discipline for bodies, allocation, and concurrency
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Implementation Phase

> Discipline inside function bodies — how objects are owned and passed, how
> failures travel, what names and constants look like, how expressions and
> control flow stay correct, how shared state stays synchronized, and when
> optimization is allowed at all.

---

## Overview

The implementation phase decides how bodies behave day to day: which handle
owns each resource and who may hold a reference, how an error raised at one
edge reaches another, what a name says and what a constant computes, which
conversions and initializations slip through silently, which thread touches
which state, and when a hot path may spend effort on speed. Enter this phase
when writing or reviewing the inside of a function — allocation, error
plumbing, naming, expressions, synchronization, or measured optimization.
The failure mechanisms and ownership boundaries these bodies work within
were fixed in the [design phase](./design.md); the guides below
operationalize them, they do not renegotiate them.

---

## Reading Path

1. **[Memory Discipline](./implement/memory-discipline.md)** — any body that allocates, passes, or outlives objects: RAII, pass-by rules, lifetime and invalidation pitfalls.
2. **[Error Propagation](./implement/error-propagation.md)** — plumbing failures through a body: `noexcept` discipline, propagation across module boundaries, logging versus handling.
3. **[Naming and Constants](./implement/naming-and-constants.md)** — adding names, enumerations, or compile-time constants.
4. **[Expressions and Flow](./implement/expressions-and-flow.md)** — writing or reviewing expressions and control flow: initialization, conversions.
5. **[Concurrency](./implement/concurrency.md)** — a body that touches threads, atomics, or shared state.
6. **[Performance](./implement/performance.md)** — optimization work: hot paths and allocation pressure, measured first.

---

## Phase Checklist

- Is every resource in the body owned by an RAII handle, with no bare `new`/`delete` and no borrowed reference outliving its owner?
- Does each failure path propagate by the mechanism the interface already promised, with `noexcept` used deliberately rather than by accident?
- Do new names, enumerators, and constants follow the project's conventions instead of the author's habits?
- Is every variable initialized at declaration, and is every conversion checked for narrowing?
- Is all shared state synchronized, and could a reviewer rule out a data race from the code alone?
- Is every optimization backed by a measurement taken before the change, not a hunch after it?

---

## Cross-Phase Pointers

- The contracts these bodies implement — failure mechanisms, ownership at
  API edges, header surfaces — were established in the design-phase guides:
  start from [Design Phase](./design.md) whenever a body change would need
  to renegotiate one.

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
