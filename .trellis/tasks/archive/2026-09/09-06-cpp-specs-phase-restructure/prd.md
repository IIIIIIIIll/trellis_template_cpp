# PRD: Phase-oriented restructuring of C++ guideline specs

## Goal

Restructure `specs/cpp/cpp/` around three development lifecycle phases —
Design / Implementation / Verification — with every rule doc filed under
exactly one phase, and per-task context injection smaller and more precise,
without breaking rule contracts (stable IDs, one home per rule, Caught-by
pairing, generated `rules.json`).

## Background

The cpp guideline template ships 10 topic docs (4628 lines total; FN 621,
CLS 569, QUAL 567, ERR 493, EXPR 460, TPL 440, CONC 359, TEST 312, MEM 297,
PERF 291). Readers consume them through the layer index, not the file tree,
and injection is file-granular: `spec_match.py` selects specs by
frontmatter `paths:` globs (`rglob("*.md")` over `.trellis/spec/**`,
line 346) and `spec_inject.py` injects whole files (FULL block, sha-pinned,
budgeted; overflow degrades to description-only index lines). Only 2 files
in the repo carry `paths:` frontmatter — zero cpp docs — so today's set is
both ungated and fat per read. Subdirectories inside a layer are discovered
(rglob), making phase filing mechanically safe.

## Decisions (all user-approved, 2026-09-06)

- D1: Rule docs are **filed under exactly one phase** — phase-centering
  applies to entries AND filing, not tags alone.
- D2: Existing docs **may be split**; for straddling docs (ERR, QUAL, MEM)
  splits are load-bearing — they are what makes one-phase filing honest.
- D3: `core-guidelines-disposition.md` stays put, phase-neutral — core
  group, never a phase member.
- D4: Filing mechanism = **phase subdirectories inside the single `cpp/`
  layer** (`design/`, `implement/`, `verification/`); template manifest and
  layer identity unchanged.
- D5: The proposed doc → phase mapping and split set is approved as
  tabled in `design.md` (14 rule docs + 3 routers; dirs named
  design/implement/verification).

## Requirements

- R1 (→ D1, D4, D5): Every rule doc filed under exactly one phase per the
  approved mapping; layer-root `index.md` regrouped into Design /
  Implementation / Verification / Alignment & Governance groups.
- R2 (→ D5): Three phase router docs (`design.md`, `implementation.md`,
  `verification.md`) at layer root owning zero rules; registered per sync
  obligations.
- R3: `paths:` frontmatter on all cpp-layer docs except `index.md`
  (shared C++ glob list; test-scoped extras on testing docs) — the
  injection selection mechanism.
- R4 (→ D2): Splits only at the verified self-contained seams (ERR cut at
  section line 301; MEM at 61/181; QUAL at 112/186/443); each part gets
  full doc shape; Caught-by scope re-established and `validate_rules.py`
  run after each split, not at the end.
- R5: Same-change sync obligations per stage: tools rebindings
  (validate_rules / extract_rules / check_snippets), `rules.json`
  regeneration, `specs/cpp/README.md` table + tree, registry `README.md`
  layout tree, `USAGE.md` claims, disposition routing links, guide
  cross-links, guideline-authoring prefix table.

## Out of Scope

- Moving `core-guidelines-disposition.md` into a phase (D3).
- Renumbering or retiring rule IDs.
- Reorganizing rule *content* by phase beyond the verified seam splits.
- Splitting FN/CLS/TPL/PERF (rejected: honestly single-phase or too-thin
  halves; recorded in design.md trade-offs).

## Acceptance Criteria

- A1 (R1): Actual tree matches the design.md target exactly; every rule
  doc lives under exactly one phase directory; the four listing places
  (cpp/index.md both tables, specs/cpp/README.md, registry README.md tree,
  actual tree) cover the identical file set.
- A2 (R2): Each phase router reaches every rule doc of its phase; routers
  contain no rule text; each is a registered file in the sync surfaces.
- A3 (R3): Every cpp-layer doc except index.md declares valid `paths:`
  frontmatter; a consumer-simulation check (`specs/cpp` installed into a
  temp `.trellis/spec/`) shows all 18 content docs selected with
  descriptions for a `.cpp` probe and `index.md` correctly excluded.
- A4 (R4): `python3 tools/validate_rules.py` passes; every split part
  carries its sections' Caught-by lines (no EXPR-26-class detector
  inheritance loss — verified by the regenerated `rules.json` detector
  columns, not just markdown).
- A5 (R5): Digest determinism check passes (two consecutive
  `extract_rules.py` runs byte-identical); `python3 tools/check_snippets.py`
  passes; the specs link check reports zero broken links; no rule ID
  changed (git diff of ID sets is empty).
