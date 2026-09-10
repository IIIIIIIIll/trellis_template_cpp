# PRD (child 1): Reshape cpp thinking-guide layer to family shape

> Parent: `09-09-thinking-guide-improvement` (decision set and evidence base
> live there). Sequenced first; the scar-home child consumes this child's
> contract text and router pointer.

## Problem

The thinking-guide layer (`specs/cpp/guides/index.md`, 8.7 KB single file)
diverges from the trellis family on every axis: no router semantics, no
symptom checklists, no philosophy framing, no pre-modification rule, no
layer diagram, no growth path. The developer wants the family shape,
C++-ized, with the existing curated method re-homed intact.

## Goal

Reshape `specs/cpp/guides/` into the family structure — router + phase-named
narrative guides + family-standard files — under fence policy α (zero
` ```cpp `), with the shape contract rewritten in
`.trellis/spec/registry/guideline-authoring.md` (including the supersession
of the 2026-09-09 no-growth resolution and the `big-question/` contract that
child 2 fills in), and all file-set syncs in the same change.

## Requirements

### File set (7 files, all in `specs/cpp/guides/`)

| File | Status | Role |
|------|--------|------|
| `index.md` | edited in place (path preserved) | Family router |
| `design-thinking-guide.md` | new | Design-phase procedure (6 rows) |
| `implementation-thinking-guide.md` | new | Implementation-phase procedure (6 rows) |
| `verification-thinking-guide.md` | new | Verification-phase procedure (3 rows) |
| `pre-implementation-checklist.md` | new | Family-standard: before writing code |
| `code-reuse-thinking-guide.md` | new | Family-standard: reuse thinking, C++-ized |
| `bug-root-cause-thinking-guide.md` | new | Family-standard: post-incident method; bridges to `big-question/` |

### Router (`index.md`) — family sections, in family order

1. Frontmatter: keep `paths:` (shared C++ glob); update `description:` (it is
   the injected index line).
2. `# C++ Thinking Guides` + blockquote + **Core Philosophy** line ("30
   minutes of thinking saves 3 hours of debugging" — family-standard).
3. **Why Thinking Guides?** — C++-ized "didn't think of that" list (layer
   boundaries → TU/link; ownership across calls → use-after-free; evaluation
   order → miscompiles; invariants → half-updated objects).
4. **Available Guides** table (6 guides; NO `big-question/` pointer row in
   this child — every `../big-question/index.md` pointer is child-2 scope).
5. **Quick Reference: When to Use Which Guide** — checkbox trigger lists per
   guide, **symptom-phrased** (observed signals: sanitizer output naming
   frees outside the diff; `-O0`-works/`-O2`-breaks; bug class no detector
   flagged; dangling view after growth), NOT task-type phrasing (that is
   `cpp/index.md`'s job; no duplication).
6. **Pre-Modification Rule (CRITICAL)** — search-before-change with an `rg`
   bash fence; C++-specific second command (rule/grep the rule set).
7. **C++-Specific Layers** — layer diagram (Headers → Translation Units →
   Link → Runtime) + per-boundary bug sources (ODR/ABI, serialization at
   module edges, initialization order, async destruction).
8. **Cross-Cutting Interactions** — the existing 4-span table re-homed here
   (layer-level, not phase-owned), signatures intact.
9. **Core Principles** — 4–5 numbered, C++-ized (Search Before Write, Name
   the Failure in the Signature, Walk the Error Path, Detector per Bug
   Class, Learn From Bugs). The Learn From Bugs line NAMES `big-question/`
   in prose only — NO markdown link in this child (child 2 adds
   `[big-question/](../big-question/index.md)`).
10. RESERVED for child 2: the one-line pointer to `big-question/`
    (deferred — child 1 keeps every merged state gate-green; no
    Contributing section in the router, parent decision 2).
11. Footer: **Language** line only (unchanged convention).

### Phase guides (design / implementation / verification)

Each: frontmatter (`description:` + shared C++ `paths:` glob), `# Title` +
purpose blockquote, **Why This Phase** prose (family voice, C++-specific),
the phase's rows as the **ordered procedure table** (same 5 columns:
`# | Step | Fires when you see | Canonical failure | Read first`; row order
IS the procedure), a **Before Leaving This Phase** checkbox checklist
(derived from the rows — each row becomes one checkable question),
Language-only footer.

Row survival: design 5 existing rows + 1 restored Revision-1 row (cue
verbatim from the archived Revision-1 PRD: "Can any other call invalidate
this parameter/return value while the caller still holds it?"; canonical
failure: "use-after-invalidation the compiler does not flag"; read-first:
Functions and Interfaces + Ownership Design); implementation 6;
verification 3. Cues, canonical failures, and read-first links carried
over unchanged except where the restored row is added.

### Family-standard guides

- `pre-implementation-checklist.md`: search-first for existing
  types/utilities/rule coverage; includes-and-header-cost sketch; ownership
  arrow sketch; failure-representation decision. Checkbox-driven.
- `code-reuse-thinking-guide.md`: C++ reuse thinking — search before new
  utility, templates vs copy-paste (unconstrained template smell), std
  algorithms vs hand-rolled loops, duplication thresholds, constant
  duplication across TUs. Checkbox-driven.
- `bug-root-cause-thinking-guide.md`: post-incident method — reproduce,
  minimize, classify the root cause, name the detector that should have
  caught it, add the test/detector, record the incident in `big-question/`
  (this file is the growth loop's entry point). Names `big-question/` in
  prose WITHOUT a markdown link; child 2 adds the link in Record the
  Incident.

### Contract rewrite (`guideline-authoring.md`, Thinking-Guide Layer section)

Rewrite to govern the new shape, in one edit with the file changes:

- Multi-file layer: router + phase guides + family-standard files.
- Per-file ≤ 9 KB with frontmatter (`description:` + shared C++ `paths:`
  glob) for every injected file.
- Fence policy: zero ` ```cpp ` fences in `guides/` and `big-question/`;
  bash fences legal (not compiled, not examples); validators stay blind
  (guides/ outside DEFAULT_DIR; relative-link check + hand review only).
- Growth, scoped: `big-question/` is the consumer scar home with a
  contributing format; `guides/` ships curated, no append instructions.
- **Supersession record**: cite the 2026-09-09 resolution (archived
  `09-08-thinking-guide-layer/discussion.md`), state the new circumstance
  (every trellis project in the ecosystem ships a consumer growth path; ours
  shipped none), and state what survives (template-side curation).
- Links preserved: repo-relative `../cpp/<phase>/<doc>.md` resolving
  in-repo and post-install stays binding for all phase rows; document the
  `../big-question/index.md` pointer pattern for the two deferred pointers
  (child 2 lands them).
- `big-question/` contract: layer directory of the template root
  (`specs/cpp/big-question/` → consumer `.trellis/spec/big-question/`);
  severity-index + contributing format; incident files carry **no
  frontmatter** (not injected; found via the index); index.md carries
  frontmatter + C++ globs (injected).

### Sync set (same change, verified against `research/sync-set-inventory.md`)

1. `specs/cpp/README.md` — layout tree `guides/` section lists the 7 files;
   Thinking Guides file-table section gains rows.
2. Root `README.md` — layout tree line for `guides/` (update file count if
   enumerated; currently non-enumerating — expect no diff; verify).
3. `USAGE.md`, `index.json` — no change (verify: additive install + in-place
   edit covered by existing wording; manifest pins the root).
4. `specs/cpp/cpp/index.md` — no change (checklist row keeps resolving).
5. Router keeps linking every `cpp/` topic guide — citation invariant: all
   14 reachable (the restored row closes `functions-and-interfaces.md`).

## Acceptance criteria

- All parent cross-child criteria hold (gates green, links resolve,
  14-guide citation coverage, 19 rows intact, ≤ 9 KB injected files, sync
  complete, zero ` ```cpp ` under `guides/`, supersession recorded).
- Router is recognizable family shape: philosophy framing, Available-Guides
  table, symptom-phrased checkbox Quick Reference, Pre-Modification Rule,
  layer diagram, Core Principles — all present; the big-question pointer is
  ABSENT in this child (deferred to child 2).
- No rule blocks (`**ID-n**`) anywhere in the layer; no cpp fences; no
  Contributing section in the router.
- Quick Reference triggers are symptom-phrased and do not duplicate
  `cpp/index.md` Pre-Development Checklist rows (task-type vs risk-shape
  division stated in the router overview).
- `git status` touches only: `specs/cpp/guides/**` (7 files),
  `specs/cpp/README.md`, `README.md`,
  `.trellis/spec/registry/guideline-authoring.md`.

---

**Language**: All documentation should be written in **English**.
