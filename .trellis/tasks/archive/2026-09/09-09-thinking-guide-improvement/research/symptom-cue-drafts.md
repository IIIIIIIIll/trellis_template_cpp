# Research: symptom-cue candidates for option (a)

> Draft option material — NOT a decision. Produced while awaiting the
> developer's round-3 axis selection (2026-09-09).

## Finding: the guide is already mixed-ontology

- Phase tables (Design/Implementation/Verification): cues are **diff shapes**
  ("a new parameter, return, or member of pointer, reference, or
  resource-handle type").
- Cross-Cutting Interactions: cues are **observed symptoms** ("LSan leak dump
  pointing at both ends of a mutual `shared_ptr` cycle"; "the uninitialized
  read that 'works' at `-O0` and misbehaves at `-O2`").
- The ecosystem siblings (all four) cue on symptoms throughout.

So option (a) = make the existing mix systematic, not add a new ontology.

## Draft symptom cues (candidates, byte costs estimated from row stats ~280 B each)

Derived from canonical failures already in the file — no new claims:

1. Fires when you OBSERVE: sanitizer output (ASan/LSan/TSan) naming a
   free/use/race whose allocation or creation site is not in this diff.
   → Links: Ownership Design + Concurrency. (Complements Design row 1 /
   Implementation row 3; catches the "bug shipped earlier, surfaces now"
   moment.)
2. Fires when you OBSERVE: behavior that differs between `-O0` and `-O2`, or
   between two compilers/STL implementations. → Expressions and Flow +
   Memory Discipline. (UB signature; currently only stated inside the
   Performance × correctness span.)
3. Fires when you OBSERVE: a bug class with no detector that flagged it
   (no clang-tidy check, no warning, no sanitizer, no test). → Static
   Analysis. (Inverse of Verification row 1: that row is diff-side, this is
   incident-side.)

## Budget

Headroom ≈ 748 B (≈720 chars; difference is rounding/units). Three rows
≈ 840 B — over budget. Two rows ≈ 560 B fits.
Compression levers: shorter "Read first" cell, merge into one row with three
symptom bullets, or trim Overview prose (932 B) by the same amount.

## Non-candidates (per interview round 2/3 recommendations)

- Philosophy/framing section, pre-modification rule: cosmetic conformity.
- Narrative form, multi-file split: contract change; depth already lives in
  the 14 `cpp/` guides (one home per rule).
- Growth/Contributing, `big-question/` scaffold: contradicts the 2026-09-09
  resolution; if wanted, separate task with its own decision record.

Superseded by parent PRD decisions 2/4 (2026-09-09 round 4): the parent
task IS the separate decision record, and child 1 IS the contract change.
Retained as history, not a directive.
