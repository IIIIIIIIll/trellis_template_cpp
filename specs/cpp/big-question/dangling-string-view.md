# Dangling View After Owner Mutation

*Format exemplar for a canonical C++ incident class — not project history.*

> A view stored beyond the statement that created it — `std::string_view`, a
> reference, a pointer, an iterator — points into a container that later
> mutated; the read lands after the storage moved or died.

## Problem

A sanitizer reports a use-after-free **read** in code far from the store — a
lookup, a log line, a comparison — and the reader has no mutation in sight.
The store passed review too: nothing there writes.

Signatures:

- The fault lands at the read, never at the store; the stack trace names a
  consumer, not the code that owns the memory.
- Intermittent until it is not: small-string optimization, `reserve`
  decisions, and allocator sizes decide whether the read lands in freed
  memory or in plausible leftovers.
- A reproduction appears or vanishes with input size — the short input fits
  existing capacity, the long one forces reallocation.

## Root Cause

`string_view`, references, pointers, and iterators are non-owning: they
borrow storage and extend no lifetime. The owner's mutation surface decides
when the borrow dies:

- **Growth** — `push_back` or `insert` past capacity reallocates and moves
  every element, so views and iterators into the old buffer dangle.
- **Erase** — for `vector` or `string`, invalidates the erased element and
  everything after it; for node-based containers, only the erased element.
- **Rehash** — `unordered_*` growth moves elements; references to elements
  survive, iterators do not.
- **Assignment, move, destruction** — replace or release the viewed storage.
- **Temporary materialization** — a view into a temporary dies at the end of
  the full expression; a chained range-init extends only the final range
  expression, leaving intermediates dead while the loop views them.

The trap is structural: the store and the mutation usually live in different
functions, and neither alone looks wrong. The mutation may be another call
on the owner — a cache fill, a config reload — or the owner's scope ending
first.

## Solution

Treat every stored view as a claim about the owner's mutation surface for
the whole life of the store, and make the claim explicit:

- **Store by value unless the owner provably outlives the store.** Copying a
  string is cheap next to the class of bug it removes.
- **If a view must be stored, name the owner at the declaration** — the
  comment is the contract a reviewer checks.
- **Keep views inside the statement that uses them.** Once a view becomes a
  member or long-lived local, the lifetime question belongs to the design.
- **Reserve up front where growth is predictable** — it removes the
  reallocation path, not the need to check the remaining mutations.
- **Own the outer object of a chained range-init** rather than viewing into
  temporaries that die at the end of the full expression.

Topic layer: [Memory Discipline](../cpp/implement/memory-discipline.md) owns
the pass-by table, the invalidation table, the containers-of-views rules, and
the stored-view moment;
[Expressions and Flow](../cpp/implement/expressions-and-flow.md) owns the
range-for lifetime-extension rule and mutation during iteration.

## Key Takeaways

- A sanitizer flags the use, never the store — the store is the review
  moment, however harmless it looks.
- The store looks harmless because the mutation that kills it lives in a
  later call, on another path.
- Intermittency here is a size or capacity artifact, not flakiness: treat
  the first sighting as a real bug.
- A view parameter asserts that the caller's storage outlives the call; when
  the value must outlive it, copy deliberately.

## Read first

- [Memory Discipline](../cpp/implement/memory-discipline.md) — stored-view
  rules, the invalidation table, views versus owners.
- [Expressions and Flow](../cpp/implement/expressions-and-flow.md) —
  range-for lifetime extension, mutation during iteration.

---

**Language**: All documentation should be written in **English**.
