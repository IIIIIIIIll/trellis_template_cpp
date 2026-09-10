---
description: Pre-implementation checklist — search first, draw the ownership arrow, price the header, and fix the failure representation before the first edit
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Pre-Implementation Checklist

> The minutes before the first edit are the cheapest attention this change
> will ever get: find what already exists, say who owns what, count what the
> interface costs, and decide how failure comes back. Every item below is a
> minute now and a rewrite later.

---

## Search First

```bash
# Does a type, helper, or constant already do most of this?
rg "Cache|normalize|kTimeout" -g '*.{cpp,cc,cxx,hpp,hh,h,inl,ipp}'

# Which rules already govern the area? (run from the project root; the installed
# corpus lives under .trellis/spec/cpp/)
rg -i "ownership|invalidation|naming" .trellis/spec/cpp/
```

A hit decides the shape of the change: extend what exists instead of writing
a sibling next to it, and cite the owning rule rather than deciding the
question a second time. No hit is also a result — say "searched for X, found
nothing" where the change is reviewed, so the next reader knows the reuse
question was asked rather than skipped. Reuse reasoning lives in the
[Code Reuse Thinking Guide](./code-reuse-thinking-guide.md).

## Map the Ownership Arrow

For every object the new boundary carries — parameter, return value, member,
queue entry — write one line: who creates it, who holds it, who destroys it,
on which thread. A sketch needing more than one line per object is telling
you the interface is not decided yet; return a value instead of a handle, or
split the ownership. Depth: [Ownership Design](../cpp/design/ownership-design.md),
with the body-side rules in [Memory Discipline](../cpp/implement/memory-discipline.md).

## Price the Header

Before adding an include, an inline body, or a public value type, count what
every translation unit that pulls the header in will pay: compile time,
instantiation, and whether the layout is now part of the ABI. Prefer a
forward declaration or an out-of-line body when the interface allows it.
Depth: [Headers and Dependencies](../cpp/design/headers-and-dependencies.md).

## Decide the Failure Representation

Fix how failure leaves the new code before writing a line of it: status,
exception, `optional` (C++17; C++14: a sentinel or a status type), or a
documented precondition. A caller must be able to
tell from the signature that the operation can fail and what it must do
about it — a comment is not an interface. Depth:
[Error Contracts](../cpp/design/error-contracts.md) for the design choice,
[Error Propagation](../cpp/implement/error-propagation.md) for the path out.

## Before the First Edit

- [ ] The search ran; the reuse candidate, or the "nothing exists" note, is written down
- [ ] The owning rule for each decision is named by ID, or the gap is named as a gap
- [ ] Every object crossing the boundary has one ownership line — creator, holder, destroyer, thread
- [ ] The header price is counted, and ABI exposure is a decision rather than a side effect
- [ ] Failure has a representation in the signature, not only in a comment
- [ ] The feature that would make this header or template justified is named, or the simpler form is chosen

---

**Language**: All documentation should be written in **English**.
