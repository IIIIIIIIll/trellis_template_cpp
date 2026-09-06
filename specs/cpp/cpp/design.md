---
description: Design-phase C++ reading path: API, class, template, and contract decisions
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Design Phase

> What the code promises before any body exists: signatures, class shape,
> generic abstractions, failure contracts, ownership at API edges, and the
> header surface. These are the decisions that are expensive to reverse, so
> the guides that govern them are read in a fixed order — this router is
> that order.

---

## Overview

The design phase decides how code looks from the outside: what a function is
called and what it guarantees, how a class holds its invariants, where a
template earns its abstraction, what happens when an operation fails, who
owns a resource the interface hands around, and which headers a translation
unit pulls in. Enter this phase before writing or changing a public
interface, a class with invariants, a template, a failure contract, an
ownership boundary, or an include set. The terms fixed here bind the
[implementation](./implementation.md) and [verification](./verification.md)
phases that follow — most C++ rework traces back to a boundary decided in a
hurry at this stage.

---

## Reading Path

1. **[Functions and Interfaces](./design/functions-and-interfaces.md)** — any signature at an API boundary: parameters, return values, calling conventions.
2. **[Classes and Hierarchies](./design/classes-and-hierarchies.md)** — designing a class: invariants, composition versus virtual dispatch, object lifecycle.
3. **[Templates and Generics](./design/templates-and-generics.md)** — writing or reviewing generic code: concepts, constraints, library shape.
4. **[Error Contracts](./design/error-contracts.md)** — deciding how an API reports failure: exceptions versus status returns versus asserts.
5. **[Ownership Design](./design/ownership-design.md)** — interfaces that hand resources around: the ownership ladder and smart pointers at API edges.
6. **[Headers and Dependencies](./design/headers-and-dependencies.md)** — creating headers, managing includes, vetting third-party dependencies: hygiene, ODR, ABI.

---

## Phase Checklist

- Does every new or changed signature communicate ownership and failure at the boundary without reading the body?
- Is each class's invariant established by construction, with no member reachable in an invalid state?
- Does every template earn its abstraction over the concrete alternative, or is it indirection without payoff?
- Is there one agreed failure mechanism per API edge, and does it hold when the call crosses a module or ABI boundary?
- Does every resource hand-off follow the ownership ladder, with no raw pointer quietly pretending to own?
- Can each new header stand alone, and is every third-party dependency vetted rather than accumulated?

---

## Cross-Phase Pointers

- Performance-shaped design — a PERF-2-style design-for-later-optimization,
  keeping boundaries clean so a hot path can be tuned after measurement —
  lives with the implementation phase in
  [Performance](./implement/performance.md).

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
