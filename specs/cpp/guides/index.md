---
description: The C++ thinking method — ordered per-phase steps fired by diff cues, each naming the failure you buy by skipping it
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# C++ Thinking Guides

> A procedure for thinking through C++ changes: ordered steps per phase, each
> fired by the shapes you see in a diff, and each naming the failure you buy
> by skipping it.

---

## Overview

The [C++ guideline layer](../cpp/index.md) routes by **task type** — its
Pre-Development Checklist maps "you are touching X" to "read Y" — and its
fourteen guides own every normative rule, one home per rule. This layer is a
**method**, not a rulebook: for each phase it fixes an ordered procedure whose
steps are keyed to the shapes you see in a diff. It exists for what task-type
routing misses — the change whose owning guide is not obvious from the task
description ("add a config field" can still carry an ownership or
failure-representation question), and the risk spanning several guides (the
cross-cutting spans below).

How to use it: when starting a change, run the phase procedure from row 1;
when a cue appears mid-work, stop and follow that row; the canonical-failure
column is the price of skipping the step. This layer holds no rules — every
step's answer, with its enforcement, lives behind the link.

---

## Design — Before Writing the Signature

| # | Step | Fires when you see | Canonical failure | Read first |
|---|------|--------------------|-------------------|------------|
| 1 | Draw the ownership arrow: for every object crossing the boundary, who creates it, who holds it, who destroys it, on which thread. If it needs more than one line per object, the design is not done. | A new parameter, return, or member of pointer, reference, or resource-handle type | Use-after-free or double-free from two owners — ASan's most common catch | [Ownership Design](../cpp/design/ownership-design.md); body-side rules in [Memory Discipline](../cpp/implement/memory-discipline.md) |
| 2 | Name the invariant: what holds after construction, after every public call, and at every failure point mid-operation. | A class gaining a second field, or a public method that mutates in several steps | Half-updated object observable after a throw from mid-operation | [Classes and Hierarchies](../cpp/design/classes-and-hierarchies.md); failure semantics in [Error Contracts](../cpp/design/error-contracts.md) |
| 3 | Put the failure mode in the signature before writing the body. | A function that can fail but returns `void` or a bare pointer, or reports failure only in a comment | `assert` evaporating under `NDEBUG`; a status code nobody checks | [Error Contracts](../cpp/design/error-contracts.md) |
| 4 | Price the header: what every translation unit including it pays, and whether this type's layout is now ABI. | A new include or inline method in a widely-included header; a new public value type | Recompile-the-world edits; layout change breaking deployed binaries | [Headers and Dependencies](../cpp/design/headers-and-dependencies.md) |
| 5 | Justify the template against the concrete use it replaces. | `template<typename T>` appearing for a single concrete caller | Unconstrained template instantiating nonsense at a distant use site, with the error pointed at the caller, not the template | [Templates and Generics](../cpp/design/templates-and-generics.md) |

---

## Implementation — While Writing the Body

| # | Step | Fires when you see | Canonical failure | Read first |
|---|------|--------------------|-------------------|------------|
| 1 | Walk every allocation site and say how it unwinds on every early exit. | `new`, `make_unique`, or container growth inside a loop, hot path, or function with several returns | Leak on the early return nobody traced; allocation pressure found only under profiling | [Memory Discipline](../cpp/implement/memory-discipline.md); measurement gates in [Performance](../cpp/implement/performance.md) |
| 2 | Check every stored reference, view, iterator, or raw pointer against the owner's mutation surface — for the whole life of the store. | A reference, `string_view`, iterator, or raw pointer stored beyond the current statement, or handed to a longer-lived object | Invalidation on growth: the dangling `string_view` after `push_back`. ASan flags the use, never the store — the store is the review moment | [Memory Discipline](../cpp/implement/memory-discipline.md); range-for extension in [Expressions and Flow](../cpp/implement/expressions-and-flow.md) |
| 3 | Name the guard for every shared access, and draw the lock order before taking a second lock while holding one. | A member written from two threads; a second mutex acquisition under a held lock; `volatile` anywhere near threading | A race whose interleaving the test run never triggers; deadlock from lock-order inversion | [Concurrency](../cpp/implement/concurrency.md) |
| 4 | Walk every error path to its end: destructors run, rollback happens, rethrow carries context. | A `catch` returning a status; an early return after acquiring a resource; log-then-continue | Leak during unwinding; log-and-swallow; double-close on the retry path | [Error Propagation](../cpp/implement/error-propagation.md); leak rules in [Memory Discipline](../cpp/implement/memory-discipline.md) |
| 5 | Commit each expression to one signedness and one initialization path. | Mixed signed/unsigned comparison; unbraced narrowing; member-init order differing from declaration order; namespace-scope objects across translation units | Silent wrap in the comparison; `-Wreorder` and the static-initialization-order fiasco | [Expressions and Flow](../cpp/implement/expressions-and-flow.md) |
| 6 | Make the name keep its promise. | A `get_` that mutates, a `find` that throws, a `size` that is O(n) | The caller who believed the name | [Naming and Constants](../cpp/implement/naming-and-constants.md) |

---

## Verification — Before Declaring Done

| # | Step | Fires when you see | Canonical failure | Read first |
|---|------|--------------------|-------------------|------------|
| 1 | For every mistake this diff invites, name the detector that catches it — or add the check or the review gate. | A diff whose bug class has no entry in the curated clang-tidy/compiler-warning set | The class re-offending silently next quarter | [Static Analysis](../cpp/verification/static-analysis.md) |
| 2 | Say which sanitizer catches it, and which interleaving triggers it. If no interleaving does, the design rule was the only defense. | Threading, allocation, or lifetime touched by the diff | Green tests, racy program | [Testing Conventions](../cpp/verification/testing-conventions.md); sanitizer gates in the [layer index](../cpp/index.md) |
| 3 | Name the test that fails when this breaks, and what it fails for. | A bug fix without a regression test | Re-offense after the next refactor | [Testing Conventions](../cpp/verification/testing-conventions.md) |

---

## Cross-Cutting Interactions

These spans are why this layer exists: each crosses guides from different
phases, and no single guide owns the combined risk.

| Span | Classic signature | Read first |
|------|-------------------|------------|
| Ownership × concurrency: freeing on another thread; lock lifetime versus object lifetime | LSan leak dump pointing at both ends of a mutual `shared_ptr` cycle; use-after-free from a queue holding the last reference | [Concurrency](../cpp/implement/concurrency.md) + [Ownership Design](../cpp/design/ownership-design.md) + [Memory Discipline](../cpp/implement/memory-discipline.md) |
| Exceptions × templates: a generic's failure contract instantiates at every use site | `noexcept` move falling back to a copying move during container growth; the throw surfacing at a use site that cannot handle it | [Error Contracts](../cpp/design/error-contracts.md) + [Templates and Generics](../cpp/design/templates-and-generics.md) |
| Performance × correctness: UB that happens to be fast | The uninitialized read that "works" at `-O0` and misbehaves at `-O2`; the dangling reference read inside a hot loop | [Performance](../cpp/implement/performance.md) + [Expressions and Flow](../cpp/implement/expressions-and-flow.md) + [Memory Discipline](../cpp/implement/memory-discipline.md) |
| Headers × evolution: changing a header recompiles the world; changing layout breaks binaries | The inline function whose behavior changed for binaries built against the old header | [Headers and Dependencies](../cpp/design/headers-and-dependencies.md) |

---

**Language**: All documentation should be written in **English**.
