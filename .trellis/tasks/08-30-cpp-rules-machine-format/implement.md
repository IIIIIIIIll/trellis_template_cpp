# Implementation Plan

Order matters: contract first, then restructure, then bulk marking, then
tooling gates. Each phase ends committed; gates re-run at every phase boundary.

## Phase 1 — Contract and skeleton

- Update `.trellis/spec/registry/guideline-authoring.md`: rule-block grammar,
  ID allocation table, strength vocabulary, per-rule marking duty, digest
  regeneration obligation on rule changes, new doc's sync duties.
- Scaffold `tools/` (`validate_rules.py`, `extract_rules.py`,
  `check_snippets.py`, `stubs/`) — parsing logic first, gate wiring last.
- Gate: tools run (may report thousands of violations — expected pre-marking).

## Phase 2 — Index split

- Create `specs/cpp/cpp/core-guidelines-disposition.md` from the disposition
  body; slim `index.md` to routing + stance vocabulary.
- Sync: index table (+1 row), README table/tree, top README tree
  ("eleven" → "twelve"), authoring-contract counts and retargets, registry
  index counts (lines 22/51), the moved body's self-references, and the
  functions-guide deviation-policy link (full list: design.md, Index split).
- Gate: four-way invariant + link check green; index ≤120 lines.

## Phase 3 — ID + strength marking pass (parallel, per-doc-pair slices)

Six editors mirroring the review pairing (memory+error, quality+testing,
functions+classes, templates+concurrency, expressions+performance; index has
no rules). Each: convert prose rules to the block grammar, assign IDs from the
allocation table, mark strength per rule, normalize `Caught by:` lines, tag
table rows carrying claims, tag Wrong/Right fences and compiles-but-UB Wrong
examples. No rule-substance edits; wording shifts limited to what the grammar
requires (e.g. splitting a paragraph that fuses two rules into two blocks).

Editors flag (do not resolve) any rule whose strength they cannot judge —
decisions surface to the developer at phase end.

Authorized within "no substance edits": adding `Caught by:` lines where a doc
has none (naming an existing detector is bookkeeping; where nothing applies,
the explicit no-detector statement is added).

Sixth slice, in parallel with the five content slices: implement
`validate_rules.py` + `extract_rules.py` to green against the marked output
as it lands (PlanCheck A5).

- Gate: validator green repo-wide; `rules.json` generated and committed.

## Phase 4 — Snippet harness to green

- Author stubs per doc as needed; compile every fenced block; fix docs where
  examples predate the gate (compile fixes only — substance frozen; a failing
  example that is *substantively* wrong goes back to the developer, it does
  not get silently rewritten).
- Emit the "compiles; UB at runtime" inventory for the manual-review list.
- Gate: `check_snippets.py` clean; wired into registry index Quality Check
  alongside the JSON/link gates.

## Phase 5 — Closeout

- Full structural gate suite (manifest, links, footers, four-way invariant,
  validator, digest determinism, snippet gate).
- `findings.md` records the conversion decisions (ID assignments, flagged
  strengths, stub inventory).
- Commits per phase: `feat(tools): ...` for tooling, `refactor(specs): ...`
  for doc restructure, matching repo commit style.

## Validation plan

- Validator + harness are the regression nets; run on every phase boundary.
- Digest determinism: regenerate twice, diff must be empty.
- Spot-check by reading one converted doc end-to-end before fanning out the
  other five slices (pattern must be right once, then applied in parallel).
