# Align quality-guidelines with the authoring spec

## Background

2026-09-05 review of `specs/cpp/cpp/quality-guidelines.md` against
`.trellis/spec/registry/guideline-authoring.md`. All mechanical gates passed
(`validate_rules.py`, `check_snippets.py`, digest determinism). Findings: one
encoding gap the tooling cannot flag, plus four tolerated style nits. User
approved fixing all of them.

## Requirements

1. **Spec amendment** (`guideline-authoring.md`): the QUAL-63/64 example uses
   `// Good:` / `// Bad:` labels — outside the three sanctioned Wrong/Right
   encodings, and impossible to express as `// Wrong:` because every Wrong
   block must declare a mechanical class (`compile-error` /
   `compiles; UB at runtime`), which a style-only anti-pattern (compiles, no
   runtime misbehavior) cannot state. Bless this as encoding 4.
2. **Nit A**: drop the non-canonical prose "Purely a review matter — no tool
   can catch a bad comment." under Comment Discipline; QUAL-11–13 already
   inherit the section-level caught-by line.
3. **Nit B**: add `Default strength: default.` to the Enumerations section
   for uniformity with the other seven sections (inert — all six rules carry
   explicit strengths).
4. **Nit C**: the QUAL-48 fence carries a third segment
   (`// Best when expressible:`) beyond the one-Wrong/one-Right pair; fold it
   into the Right group as a lowercase continuation comment.
5. **Nit D**: QUAL-57's `// does not compile` annotation reads as a
   non-canonical `// compile-error` lookalike; rephrase to
   `// rejected: no implicit conversion to int`.

## Constraints

- No rule text, IDs, numbering, or strengths change (QUAL-1..64 intact) —
  the `rules.json` digest must stay byte-identical.
- `// compile-error` must NOT be introduced into the QUAL-57 fence
  (`MARKER_COMPILE_ERROR_RE` would flip the commented line into a must-fail
  section that compiles — false violation).

## Acceptance criteria

- Full registry quality gate green (`.trellis/spec/registry/index.md`):
  manifest check, relative-link check, `validate_rules.py`,
  digest determinism (`extract_rules.py` + `cmp`), `check_snippets.py`.
- Post-change `rules.json` byte-identical to the pre-change digest.
- One commit covering both edited files.
