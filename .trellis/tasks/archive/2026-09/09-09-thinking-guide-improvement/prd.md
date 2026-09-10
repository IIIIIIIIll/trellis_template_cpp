# PRD (parent): Converge cpp thinking-guide layer with trellis family shape

## Problem

`specs/cpp/guides/index.md` is a different species from everything trellis
ships: a single 8.7 KB dense-method file with no router, no symptom
family-style checkbox Quick Reference / Available-Guides table, no growth
path, and no scar home. Verified against the stock
layer (`@mindfoldhq/trellis` `dist/templates/markdown/spec/guides/`) and all
three official marketplace templates (`mindfold-ai/marketplace`:
electron-fullstack, nextjs-fullstack, cf-workers-fullstack) — the family
shape is: router `guides/index.md` (philosophy framing, Available-Guides
table, checkbox Quick Reference, Pre-Modification Rule, stack layer diagram,
Core Principles, Contributing) + narrative topic guides (4–15 KB each) +
separate `big-question/` scar directory (severity-indexed incident deep-dives
with a contributing format). Consumers of our template have nowhere to record
incident lessons, unlike every other trellis project.

## Driver (interview outcome, 2026-09-09)

Developer decision, confirmed round 4: full convergence — "exactly what
trellis already ships … targeting cpp instead." Not driven by a concrete
incident or by the known coverage asymmetry; those are absorbed as side
effects. Grilling interview notes: `discussion.md` in this task directory.

## Decision set (all confirmed by the developer)

1. **Variant (b):** marketplace-family shape + `big-question/` scar home.
2. **Resolution reversal, scoped:** the 2026-09-09 no-growth resolution
   (archived `09-08-thinking-guide-layer/discussion.md`) is superseded —
   growth instructions ship, but scoped to `big-question/` (contributing
   format there; the guides router carries at most a one-line pointer). The
   resolution's actual rationale — curation of the method — is preserved:
   template-shipped `guides/` content stays curated through releases.
   Superseding circumstance: marketplace evidence — 3/3 siblings ship
   `big-question/` + Contributing; this template shipped no consumer growth
   path. Scope narrowing: `guides/` stays project-independent and
   maintainer-authored; consumer scar authorship lives ONLY in
   `big-question/` via its Contributing format.
3. **Fence policy (α):** zero ` ```cpp ` fences anywhere in `guides/` or
   `big-question/`; bash fences remain legal. Code depth stays one link away
   in the 14 `cpp/` guides (one home per rule). No `check_snippets.py`
   extension in this effort.
4. **Guide set (a):** phase-named C++ guides re-homing the existing 14
   phase rows (5 design + 6 implementation + 3 verification) and the 4
   cross-cutting spans 1:1, plus family-standard files; plus one restored
   Revision-1 row (parameter invalidation → `functions-and-interfaces.md`),
   closing the only coverage gap (19 items total: 15 phase rows + 4
   spans). File set: `guides/index.md` (router, path kept) +
   `design-thinking-guide.md` + `implementation-thinking-guide.md` +
   `verification-thinking-guide.md` + `pre-implementation-checklist.md` +
   `code-reuse-thinking-guide.md` + `bug-root-cause-thinking-guide.md`.
5. **Structure (b):** parent task + two children (this task is the parent).
6. **Sync mechanics:** keep `guides/index.md` as the router path (edited in
   place); all other files are pure additions — orphan-free update path,
   no `index.json` change (manifest pins `specs/cpp` root), no `USAGE.md`
   change (additive behavior already documented).

## Task map

| Child | Deliverable | Sequence |
|-------|-------------|----------|
| `09-09-thinking-guide-layer-reshape` | Contract rewrite (`guideline-authoring.md` Thinking-Guide Layer section, including the big-question/ contract and the supersession record) + router + 6 narrative guides + README file-table/layout syncs | First |
| `09-09-big-question-scaffold` | `specs/cpp/big-question/` layer: severity index + contributing format + 3 seeded incident narratives linking into compiled `cpp/` examples; README syncs | After reshape (consumes its contract text; adds the one-line router pointer) |

Sequencing + ownership rules: child 1 MUST NOT add the router pointer to
`../big-question/index.md` (it would break the relative-link gate before
child 2 lands); child 1 owns the README table structure + guides rows;
child 2 appends big-question rows in its own change; the parent verifies
the union.

Cross-child integration (parent's job): both children's file sets appear in
the same README tables consistently; gates green on the union; citation
coverage and row-survival invariants hold across the whole layer.

## Cross-child acceptance

- All gates green from repo root (manifest check, relative-link check,
  `validate_rules.py`, digest determinism, `check_snippets.py`).
- Every relative link in `guides/` and `big-question/` resolves in-repo and
  post-install (`../cpp/…` pattern).
- Every one of the 14 `cpp/` topic guides is reachable from the
  thinking-guide layer (closes the `functions-and-interfaces.md` gap).
- Method survival: 15 phase rows (6 design incl. restored invalidation
  row, 6 implementation, 3 verification) + 4 cross-cutting spans = 19
  items; spans live in the router. Every row keeps cue, canonical
  failure, and read-first link; row order within a phase remains the
  procedure.
- Per-file ≤ 9 KB with frontmatter (`description:` + shared C++ `paths:`
  glob) for every injected file. Seeded big-question incident narratives
  carry NO frontmatter (not injected); frontmatter required on the router,
  narrative guides, and `big-question/index.md` only.
- File-set sync: `specs/cpp/README.md` (layout tree + file tables), root
  `README.md` (layout tree), `guideline-authoring.md` contract — all in the
  same changes as the files they describe.
- Zero ` ```cpp ` fences under `specs/cpp/guides/` and `specs/cpp/big-question/`.
- Supersession recorded: new contract text references the 2026-09-09
  resolution and states the new circumstance instead of silently replacing.

## Non-goals

- Zero content changes to the 14 `cpp/` topic guides — their rules are
  cited, not edited.
- No `check_snippets.py` extension (fence policy α).
- No `index.json` change; no `USAGE.md` change.
- No change to this repo's local tombstone (`.trellis/spec/guides/`).
- No new rule blocks anywhere in the new files (one home per rule).
- No fabricated "scar tissue": seeded big-question incidents are canonical
  C++ incident classes drawn from the existing canonical-failure vocabulary,
  explicitly presented as exemplars of the format.

## Evidence base

Clones at `/tmp/trellis-src` (Trellis) and `/tmp/trellis-marketplace`
(marketplace submodule) were read on 2026-09-09: stock 4 guide files (index
read fully, cross-layer 123/327 lines, headings of code-reuse and
cross-platform), all 3 marketplace `guides/index.md` files, nextjs
`big-question/index.md` (the contributing format), electron/nextjs/cf-workers
guide file lists and sizes. Details: `research/symptom-cue-drafts.md`,
`research/sync-set-inventory.md` in this directory.

---

**Language**: All documentation should be written in **English**.
