---
description: The implementation phase as an ordered procedure — allocation unwinding, store lifetimes, guards and lock order, complete error paths, signedness, names that keep their promises
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Implementation Thinking Guide

> While the body is being written, every allocation, stored reference,
> guard, and error path is a decision with a failure attached. Run these
> steps in order; when a cue fires, stop and read the owning guide before
> continuing.

---

## Why This Phase

The design says who owns what; the body decides whether that promise
survives contact with early returns, exceptions, container growth, and
second threads. Nothing here is exotic: a leak lives on the one early exit
nobody traced, a dangling view is created by a `push_back` two functions
away, a race needs an interleaving the test run never produced, a
log-then-continue hands a failure to nobody, a mixed signed comparison wraps
silently, and a name that lies costs every future reader a misread.

Each row below fires on a shape you can see while typing — allocation
sites, a stored reference, a second lock, a catch that returns a status. The
canonical-failure column is what the reader pays when the step is skipped.

---

## The Procedure

| # | Step | Fires when you see | Canonical failure | Read first |
|---|------|--------------------|-------------------|------------|
| 1 | Walk every allocation site and say how it unwinds on every early exit. | `new`, `make_unique`, or container growth inside a loop, hot path, or function with several returns | Leak on the early return nobody traced; allocation pressure found only under profiling | [Memory Discipline](../cpp/implement/memory-discipline.md); measurement gates in [Performance](../cpp/implement/performance.md) |
| 2 | Check every stored reference, view, iterator, or raw pointer against the owner's mutation surface — for the whole life of the store. | A reference, `string_view`, iterator, or raw pointer stored beyond the current statement, or handed to a longer-lived object | Invalidation on growth: the dangling `string_view` after `push_back`. ASan flags the use, never the store — the store is the review moment | [Memory Discipline](../cpp/implement/memory-discipline.md); range-for extension in [Expressions and Flow](../cpp/implement/expressions-and-flow.md) |
| 3 | Name the guard for every shared access, and draw the lock order before taking a second lock while holding one. | A member written from two threads; a second mutex acquisition under a held lock; `volatile` anywhere near threading | A race whose interleaving the test run never triggers; deadlock from lock-order inversion | [Concurrency](../cpp/implement/concurrency.md) |
| 4 | Walk every error path to its end: destructors run, rollback happens, rethrow carries context. | A `catch` returning a status; an early return after acquiring a resource; log-then-continue | Leak during unwinding; log-and-swallow; double-close on the retry path | [Error Propagation](../cpp/implement/error-propagation.md); leak rules in [Memory Discipline](../cpp/implement/memory-discipline.md) |
| 5 | Commit each expression to one signedness and one initialization path. | Mixed signed/unsigned comparison; unbraced narrowing; member-init order differing from declaration order; namespace-scope objects across translation units | Silent wrap in the comparison; `-Wreorder` and the static-initialization-order fiasco | [Expressions and Flow](../cpp/implement/expressions-and-flow.md) |
| 6 | Make the name keep its promise. | A `get_` that mutates, a `find` that throws, a `size` that is O(n) | The caller who believed the name | [Naming and Constants](../cpp/implement/naming-and-constants.md) |

---

## Before Leaving This Phase

- [ ] Does every allocation site have a stated way to unwind on each early exit?
- [ ] Is every stored reference, view, iterator, and raw pointer safe against the owner's mutations for as long as it lives?
- [ ] Does every shared access have a named guard, and is the lock order written down before a second lock is taken?
- [ ] Does every error path reach its end — destructors run, rollback happens, and context survives the rethrow?
- [ ] Is each expression committed to one signedness and one initialization path?
- [ ] Does each name describe what the code actually does?

---

**Language**: All documentation should be written in **English**.
