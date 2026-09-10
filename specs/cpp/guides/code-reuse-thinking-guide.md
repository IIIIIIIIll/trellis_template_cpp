---
description: Code reuse thinking guide — search before creating, justify templates against a concrete caller, prefer algorithms to hand-rolled loops, and keep one home per constant
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Code Reuse Thinking Guide

> Every new helper, template, and constant is a bet that nothing existing
> already covers the need. This is the pass that collects on that bet before
> the second copy exists and the two can drift apart.

---

## Search Before Creating

```bash
# By name — yours, and the synonyms an earlier author may have chosen
rg "trim|strip|sanitize" -g '*.{cpp,cc,cxx,hpp,hh,h,inl,ipp}'

# By need — who already solves the shape of problem you are about to write
rg "find_first_not_of|is_space" -g '*.{cpp,cc,cxx,hpp,hh,h,inl,ipp}'
```

Search before the editor opens, not after a reviewer asks. Search by the name
you would give it and by the need it serves — an existing utility rarely
carries your wording. A hit within 80% of the need is an extension, not a
fork: a default argument or an overload keeps one home for the next fix.

## What Justifies a New Template

Three smells say the template is not yet earned:

- **One concrete caller** — a template with one instantiation is a concrete
  function in disguise: the type error the compiler would have shown at the
  definition appears at the call site instead.
- **No stated requirements** — a template that fails, somewhere in its body,
  for the types it never meant to accept hands the caller an error attributed
  to their own call; if the requirements are real, state them at the
  interface.
- **Reuse that does not exist yet** — a template justified by a hypothetical
  second caller is speculative; write it when that caller arrives.

Depth: [Templates and Generics](../cpp/design/templates-and-generics.md).

## Algorithms vs Hand-Rolled Loops

A hand-rolled index loop re-implements a subset of the standard vocabulary —
a search, an any-of, a transform, an accumulation — with its own off-by-one,
signedness, and early-exit mistakes. Before typing the loop, name the
algorithm it implements; if the library has it, use it. If the loop must stay
hand-rolled, write down why (an early exit the algorithm cannot express, the
index is needed, measured cost). Swapping a loop for an algorithm is a
correctness edit, not automatically a speed edit: measure before claiming
faster. Depth: [Expressions and Flow](../cpp/implement/expressions-and-flow.md);
[Performance](../cpp/implement/performance.md).

## Duplication Thresholds and Shared Constants

- **Second copy with divergence risk** — extract now: two copies of one
  behavior are already two definitions of it, and the next fix lands in one.
- **Third copy of anything non-trivial** — extract, regardless of risk.
- **Trivial one-liner with one use** — leave it; an abstraction more complex
  than the duplication it removes is a new bug source.

The same threshold governs constants: the same literal or default in two
translation units is a drift bug waiting. Search for the value before writing
it; when it exists twice, consolidate into one named home instead of adding a
third copy; when it is a default, the interface owner names it. Depth:
[Naming and Constants](../cpp/implement/naming-and-constants.md); linkage in
[Headers and Dependencies](../cpp/design/headers-and-dependencies.md).

## Before Writing It Yourself

- [ ] Searched by name and by need; the hit, or the empty result, is written down
- [ ] Extended the existing utility instead of writing a sibling within 80% of it
- [ ] The house rules were checked before a new name or constant home was invented
- [ ] A template has a concrete caller today and states its requirements at the interface
- [ ] Each hand-rolled loop names the algorithm it implements, or why it cannot be one
- [ ] No literal, default, or table was copied into a second translation unit

---

**Language**: All documentation should be written in **English**.
