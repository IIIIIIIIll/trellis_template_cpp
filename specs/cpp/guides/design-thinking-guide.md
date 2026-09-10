---
description: The design phase as an ordered procedure — ownership arrows, invariants, failure in the signature, header price, template justification, invalidation windows
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Design Thinking Guide

> Settle the expensive decisions before the first line of the body exists:
> who owns what, what stays true, how failure comes back, and what the
> interface costs everyone who includes it.

---

## Why This Phase

Design answers the questions a debugger cannot: it fixes the object graph,
the invariants, and the failure representation while they are still cheap to
change. Every C++ failure class that survives review traces back to an
interface decision made in a hurry — two owners for one resource, a
half-updated object nobody can observe safely, a failure that only a comment
records, a header whose blast radius was never counted, a template that
instantiates nonsense at a distant call site, a value that dies while its
caller still holds it.

Skipping this phase does not remove the work; it moves it into the debugger,
where the same question ("who destroys this?") costs hours instead of
minutes. Run the rows below in order. Each one is fired by a shape you can
see in the diff, and each names the failure that shape buys when the step is
skipped.

---

## The Procedure

| # | Step | Fires when you see | Canonical failure | Read first |
|---|------|--------------------|-------------------|------------|
| 1 | Draw the ownership arrow: for every object crossing the boundary, who creates it, who holds it, who destroys it, on which thread. If it needs more than one line per object, the design is not done. | A new parameter, return, or member of pointer, reference, or resource-handle type | Use-after-free or double-free from two owners — ASan's most common catch | [Ownership Design](../cpp/design/ownership-design.md); body-side rules in [Memory Discipline](../cpp/implement/memory-discipline.md) |
| 2 | Name the invariant: what holds after construction, after every public call, and at every failure point mid-operation. | A class gaining a second field, or a public method that mutates in several steps | Half-updated object observable after a throw from mid-operation | [Classes and Hierarchies](../cpp/design/classes-and-hierarchies.md); failure semantics in [Error Contracts](../cpp/design/error-contracts.md) |
| 3 | Put the failure mode in the signature before writing the body. | A function that can fail but returns `void` or a bare pointer, or reports failure only in a comment | `assert` evaporating under `NDEBUG`; a status code nobody checks | [Error Contracts](../cpp/design/error-contracts.md) |
| 4 | Price the header: what every translation unit including it pays, and whether this type's layout is now ABI. | A new include or inline method in a widely-included header; a new public value type | Recompile-the-world edits; layout change breaking deployed binaries | [Headers and Dependencies](../cpp/design/headers-and-dependencies.md) |
| 5 | Justify the template against the concrete use it replaces. | `template<typename T>` appearing for a single concrete caller | Unconstrained template instantiating nonsense at a distant use site, with the error pointed at the caller, not the template | [Templates and Generics](../cpp/design/templates-and-generics.md) |
| 6 | Check the invalidation window: for every parameter or return value the caller keeps, name the calls that can invalidate it before the caller is finished with it — then narrow the interface or document the window. | Can any other call invalidate this parameter/return value while the caller still holds it? | use-after-invalidation the compiler does not flag | [Functions and Interfaces](../cpp/design/functions-and-interfaces.md); invalidation surface in [Memory Discipline](../cpp/implement/memory-discipline.md); ownership depth in [Ownership Design](../cpp/design/ownership-design.md) |

---

## Before Leaving This Phase

- [ ] Does every object crossing the boundary have a one-line ownership arrow — creator, holder, destroyer, thread?
- [ ] Is the invariant written down for construction, for every public call, and for a failure mid-operation?
- [ ] Can a caller tell from the signature alone that the operation can fail, and how?
- [ ] Have you priced the header — includes, inline bodies, and whether this layout is now ABI?
- [ ] Is the template justified by a concrete caller, with its type requirements stated at the interface?
- [ ] Can any other call invalidate this parameter or return value while the caller still holds it?

---

**Language**: All documentation should be written in **English**.
