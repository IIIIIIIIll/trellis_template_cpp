# C++ Development Guidelines

> Best practices for native C++ development in this project.

---

## Overview

This directory contains the guidelines for C++ development. They are
opinionated defaults targeting a C++14 baseline, with C++17/20 additions
(`std::string_view`, `std::optional`, `if constexpr`, `[[nodiscard]]`,
`std::span`) called out as marked upgrades where they change a
recommendation. Treat them as the starting point to adapt: record what your
project actually enforces, not aspirations nobody checks.

---

## Guidelines Index

| Guide | Description |
|-------|-------------|
| [Memory and Ownership](./memory-and-ownership.md) | RAII invariant, ownership ladder, pass-by conventions, iterator invalidation and other lifetime pitfalls |
| [Error Handling](./error-handling.md) | Exceptions versus `expected`/error-code policy, failure contracts across API boundaries |
| [Quality Guidelines](./quality-guidelines.md) | Naming, header hygiene, ODR and ABI pitfalls |
| [Testing Conventions](./testing-conventions.md) | Test framework and layout, test naming, what deserves a test |
| [Functions and Interfaces](./functions-and-interfaces.md) | Function signature design, parameter and return-value conventions at API boundaries |
| [Classes and Hierarchies](./classes-and-hierarchies.md) | Class design and inheritance: invariants, composition versus virtual dispatch |
| [Templates and Generics](./templates-and-generics.md) | Templates, concepts, and generic library design |
| [Concurrency](./concurrency.md) | Threads and shared state, synchronization discipline, data-race prevention |
| [Expressions and Flow](./expressions-and-flow.md) | Expression-level correctness, initialization, conversions, control flow |
| [Performance](./performance.md) | Optimization work guided by measurement: hot paths, allocation pressure |
| [Core Guidelines Disposition](./core-guidelines-disposition.md) | Project stance toward the ISO C++ Core Guidelines: per-section disposition, residual ledger, deviation recording, adoption process, safety profiles |

---

## Adapting These Guidelines

These documents ship with concrete defaults so a new repository starts consistent instead of empty:

1. Keep the **structure** (sections, tables, wrong-vs-right examples) and replace specifics that conflict with your project's reality
2. Document **actual** conventions, not ideals; a rule nobody enforces is worse than no rule
3. Add **common mistakes** your team has made, pairing each pitfall with the tool that catches it
4. When a rule stops being enforced by tooling or review, either restore enforcement or delete the rule

---

## Stance Vocabulary

The [Core Guidelines Disposition](./core-guidelines-disposition.md) and every deviation note in the guides use this fixed vocabulary:

| Stance | Meaning |
|--------|---------|
| Adopt | Followed as written; where a guide owns the rule, the guide adds enforcement detail |
| Adapt | Followed in intent; where a guide owns the rule, the documented difference is spelled out there, otherwise the disposition itself records it |
| Adopt selectively | Adopted for the rules named in the disposition; the rest of the section is not adopted |
| Covered elsewhere | The substance already lives in one of our guides under different organization and is applied inline there |

---

## Pre-Development Checklist

Before writing code, route the task through the relevant guide:

| Task involves | Read first |
|---------------|------------|
| Raw pointers, resource handles, container lifetime questions | [Memory and Ownership](./memory-and-ownership.md) |
| Reporting failures, designing error paths across APIs | [Error Handling](./error-handling.md) |
| New headers or files, public API surface, naming decisions | [Quality Guidelines](./quality-guidelines.md) |
| Adding or vetting a third-party dependency | [Quality Guidelines](./quality-guidelines.md) |
| Writing, changing, or removing tests | [Testing Conventions](./testing-conventions.md) |
| Function signatures or API design at module boundaries | [Functions and Interfaces](./functions-and-interfaces.md) |
| Class design, inheritance, or object lifecycle decisions | [Classes and Hierarchies](./classes-and-hierarchies.md) |
| Templates, concepts, or generic code | [Templates and Generics](./templates-and-generics.md) |
| Threading, atomics, mutexes, or shared state | [Concurrency](./concurrency.md) |
| Expression-level correctness or control flow changes | [Expressions and Flow](./expressions-and-flow.md) |
| Optimization or hot-path work | [Performance](./performance.md) |
| Adopting a Core Guidelines rule, or deviating from an adopted one | [Core Guidelines Disposition](./core-guidelines-disposition.md) |

A change touching several rows above should skim every listed guide before starting — the expensive C++ mistakes are cross-cutting.

---

## Quality Check

Run the full gate before declaring any change complete:

- **Format-clean** — `clang-format --dry-run` reports no diffs on the sources you touched.
- **Tidy-clean** — the curated clang-tidy checks run on changed sources; findings are fixed or silenced with an inline justification.
- **Tests green** — the unit suite passes plain, then again under an ASan+UBSan build whenever the change touches allocation, containers, or object lifetime.
- **ThreadSanitizer** — threading changes additionally pass a TSan build.

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
