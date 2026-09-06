# PRD: Fix expressions-and-flow review findings

## Background

Full review of `specs/cpp/cpp/expressions-and-flow.md` against
`.trellis/spec/registry/guideline-authoring.md` and upstream Core Guidelines
(Jun 14, 2026 master) found contract defects and factual marker errors. All
three mechanical gates passed, so every defect below is review-only.

## Requirements

1. **EXPR-26 digest defect**: `rules.json` records detector
   `clang-tidy modernize-use-nullptr` for EXPR-26 — inherited from EXPR-25's
   own Caught-by line via nearest-preceding inheritance. Give EXPR-26 its own
   `Caught by: review — no automated detector.` line.
2. **EXPR-40 baseline violation**: prescribes `[[fallthrough]]`
   (C++17-only attribute) in a C++14-baseline guide without the required
   `**C++17:**` upgrade marking. State the C++14 spelling first, then the
   bold upgrade note (EXPR-9 is the in-file model).
3. **False `// compiles; UB at runtime` markers** on four fences:
   - EXPR-3: shown early-return path never reads `out`; restructure the Wrong
     so the early return reads `out` before any assignment (marker becomes
     true). Keep encoding 3 (`**Wrong**`/`**Right**` prose leads).
   - EXPR-10, EXPR-16, EXPR-37: compile, no UB, no runtime misbehavior —
     style-only anti-patterns → re-encode as encoding 4 (one fence,
     `// Bad:` / `// Good:` comments). No registry vocabulary change
     (boring conforming option; `-Wshadow` for EXPR-10 stays in its
     Caught-by line).
4. **Citation precision**:
   - EXPR-4 table row: `ES.74` → `ES.5` (ES.74 is about for-initializer loop
     variables, not body-local helpers).
   - EXPR-34: move the `ES.41` anchor onto the parenthesization clause;
     the assignment-placement stance stands unanchored.
   - EXPR-26 wording: relational comparison across arrays is unspecified
     ([expr.rel]); subtraction is undefined ([expr.add]) — split the two.
   - EXPR-42: "binds its variable by reference" is meaningless for an index
     loop counter — reword to element access through a reference.
5. **EXPR-27 Wrong**: move the ~240-char inline for-line comment to a
   preceding comment line.
6. Regenerate `specs/cpp/cpp/rules.json` with `tools/extract_rules.py` in the
   same change (digest is derived, never hand-edited).
7. Registry spec update (Phase 3.3): add a caught-by inheritance caution to
   `guideline-authoring.md` — a rule following one with its own detector
   silently inherits that detector; restate the fallback explicitly.

## Constraints

- Baseline C++14; closed marker vocabulary unchanged (`ub` / `compile-error`
  / Good-Bad encoding 4); stance vocabulary unchanged.
- House style: exactly one Wrong and one Right (or one Bad and one Good) per
  example group; wrong example names what a reviewer would flag.
- Rule IDs append-only: no IDs added, removed, or renumbered.
- `[[fallthrough]]` stays in prose only (no fence), so no dialect marker on
  any fence is required.

## Acceptance criteria

- `tools/validate_rules.py`: 0 violations on `specs/cpp/cpp/`.
- `tools/check_snippets.py --path specs/cpp/cpp/expressions-and-flow.md`:
  0 violations; EXPR-10/16/37 fences classified clean; EXPR-3 Wrong still
  compiles as `[ub]` with a now-true UB claim.
- `tools/extract_rules.py` regen byte-identical to the committed digest;
  EXPR-26 detector is `review` in `rules.json`.
- Git diff of `expressions-and-flow.md` shows exactly the changes above.
