---
description: Verification-phase C++ reading path: tests, sanitizers, static analysis, and measurement gates
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Verification Phase

> How the project proves a change behaves: what deserves a test and how it
> is named, which static-analysis checks run and why, and the sanitizer,
> thread-checking, and measurement gates a change must clear before it
> counts as done.

---

## Overview

The verification phase decides what counts as evidence: which behavior gets
a test and where that test lives, which static-analysis checks guard the
sources and how the check set itself is curated, and which automated gates —
sanitizer builds, thread checking, performance measurement — a change must
pass before anyone calls it done. Enter this phase when writing, changing,
or removing tests, when touching the analysis check set, or when a change
claims to be fast, safe, or race-free and that claim needs machinery behind
it. The guides here are deliberately few: most verification teeth live in
gates defined by the implementation-phase guides, and this phase routes to
them rather than restating them.

---

## Reading Path

1. **[Testing Conventions](./verification/testing-conventions.md)** — writing, changing, or removing tests: framework and layout, test naming, what deserves a test.
2. **[Static Analysis](./verification/static-analysis.md)** — curating the project's check set: adding, removing, or justifying a check.

---

## Phase Checklist

- Does the change carry a test for behavior a plausible regression would break, named and placed per convention?
- Do the changed sources pass the curated static-analysis set, with every suppression carrying its justification?
- Would the ASan+UBSan build pass whenever allocation, containers, or object lifetime changed?
- Would the TSan build pass for threading changes?
- Is every performance claim backed by the measurement gate that guards it?
- Are sanitizer or analysis findings triaged to a cause rather than silenced?

---

## Cross-Phase Pointers

The verification gates themselves are defined where the behavior lives:

- Measurement gates PERF-1 through PERF-6 — measure first, hot-path and
  allocation budgets — live in [Performance](./implement/performance.md).
- The ThreadSanitizer gate for threading changes lives in
  [Concurrency](./implement/concurrency.md).
- Sanitizer expectations — what ASan/UBSan catch and what the
  container-invalidation table must cover deterministically — live in
  [Memory Discipline](./implement/memory-discipline.md).

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
