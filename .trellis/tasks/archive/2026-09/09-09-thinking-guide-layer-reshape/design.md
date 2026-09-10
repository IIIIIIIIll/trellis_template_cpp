# Design (child 1): Reshape cpp thinking-guide layer

> Inputs: parent decision set, `prd.md` (this task), family evidence in
> parent `discussion.md` + parent `research/`. Zero ` ```cpp ` fences
> everywhere; bash fences legal.

## Row redistribution map (survival proof)

| Current home (single file) | New home | Notes |
|---|---|---|
| Frontmatter `description:` + `paths:` | `index.md` frontmatter (kept path) | description rewritten for router role |
| Overview (routing-vs-method division) | Router overview | now states: task-type routing lives in `cpp/index.md`; this layer = risk-shaped method + symptom entry; method rows live in the three phase guides |
| Design table rows 1–5 | `design-thinking-guide.md` rows 1–5 | verbatim survival: cue + canonical failure + read-first |
| (Revision-1 dropped row) | `design-thinking-guide.md` row 6 | restored: cue verbatim from archived Revision-1 PRD ("Can any other call invalidate this parameter/return value while the caller still holds it?"); canonical failure "use-after-invalidation the compiler does not flag"; read-first Functions and Interfaces + Ownership Design |
| Implementation rows 1–6 | `implementation-thinking-guide.md` rows 1–6 | verbatim survival |
| Verification rows 1–3 | `verification-thinking-guide.md` rows 1–3 | verbatim survival |
| Cross-Cutting Interactions (4 spans) | Router, section 8 | layer-level; signatures intact |
| "How to use it" prose | Router overview + phase-guide intros | split: entry-time vs in-procedure guidance |

## Per-file skeletons

### `index.md` (router, edited in place, ≤ 9 KB)

Sections in family order (PRD §Router). Content sources:

- Philosophy/Why: family-standard framing, C++-ized failure list (write
  fresh; do not copy stock text — AGPL-relevant? Stock is our upstream
  template family; paraphrase anyway, house rule: own prose).
- Quick Reference checkboxes: symptom-phrased triggers. Draft set (from
  `research/symptom-cue-drafts.md`, deduped against rows):
  - Cross-layer/boundary: sanitizer output naming frees/races outside this
    diff; `-O0` vs `-O2` divergence; behavior differs across STL builds.
  - Before writing code: a stored view/reference about to outlive its
    statement; a header about to enter a widely-included file; a template
    about to gain its first concrete caller. (Symptom-phrased; full draft
    set in parent `research/symptom-cue-drafts.md`; hand-review against
    `cpp/index.md` rows per implement Step 2.)
  - After fixing bugs: bug took >30 min; bug class no detector flagged;
    similar bug before.
  - Reuse: similar code exists; same constant in multiple TUs.
  Each bullet maps to one guide via arrow line (family pattern).
- Pre-Modification Rule: `rg "value_to_change" --type cpp` + second command
  grepping the rule corpus (`rg "AREA-" .trellis/spec/cpp/` shape — verify
  consumer path: post-install it is `.trellis/spec/cpp/`; in-repo preview is
  `specs/cpp/cpp/`. Fence comment must use the POST-INSTALL path since the
  guide ships to consumers).
- Layer diagram: ASCII, family style:
  ```
  Headers (widely-included, ABI)
      |
      v
  Translation Units (ODR, initialization order)
      |
      v
  Link (ABI surface, symbol visibility)
      |
      v
  Runtime (ownership, invalidation, races, unwinding)
  ```
  with per-boundary bug sources as bullet list.
- Cross-Cutting Interactions: current 4-span table verbatim.
- Core Principles: 5 numbered (Search Before Write · Name the Failure in the
  Signature · One Owner per Object · Detector per Bug Class · Learn From
  Bugs). DEFERRED to child 2: the big-question markdown link — child 1
  writes the prose name only.
- big-question pointer: DEFERRED to child 2 — child 1 writes none (merged
  states must stay gate-green). No Contributing section in the router
  (scoped growth, parent decision 2).

### Phase guides (each ≤ 9 KB, frontmatter + shared C++ paths glob)

`design-thinking-guide.md` / `implementation-thinking-guide.md` /
`verification-thinking-guide.md`:

1. Frontmatter: `description:` (phase-specific, one line) + shared C++
   `paths:` globs (same list; testing-scoped extras NOT added — guides are
   phase-method, not testing docs).
2. `# Title` + purpose blockquote (family voice).
3. `## Why This Phase` — prose: what this phase decides, what skipping costs
   (paraphrase of the phase's canonical failures; no rule IDs).
4. `## The Procedure` — the 5-column table; rows in order (row order IS the
   procedure). Read-first links use `../cpp/<phase>/<doc>.md` relative form
   (resolves in-repo and post-install).
5. `## Before Leaving This Phase` — checkbox list, one item per row,
   question-phrased from the row's cue (e.g. "☐ Every pointer/reference
   crossing the boundary has a one-line ownership arrow").
6. Language-only footer.

### Family-standard guides (each ≤ 9 KB)

- `pre-implementation-checklist.md`: frontmatter + blockquote + sections:
  Search First (rg fences: existing types/utilities; rule corpus); Map the
  Ownership Arrow; Price the Header; Decide the Failure Representation;
  checkbox checklist; footer. Links into `../cpp/` guides for depth.
- `code-reuse-thinking-guide.md`: frontmatter (`description:` + shared C++
  `paths:` glob) + sections: Search Before Creating; What Makes a New
  Template Justified (single concrete caller smell); Algorithms vs
  Hand-Rolled Loops; Constants Across TUs; checklist; footer.
- `bug-root-cause-thinking-guide.md`: frontmatter (`description:` + shared
  C++ `paths:` glob) + sections: Reproduce Then Minimize; Classify the
  Root Cause (which guide owns the class); Name the Missing Detector; Add
  the Test; Record the Incident (names `big-question/` in prose; the
  `../big-question/index.md` link is DEFERRED to child 2); checklist;
  footer.

## Contract rewrite spec (`guideline-authoring.md`)

Replace the Thinking-Guide Layer section bullets with:

1. Multi-file layer inventory (router + 3 phase guides + 3 family-standard
   guides) with one-line roles.
2. Injection contract: frontmatter + shared C++ glob on every injected file;
   per-file ≤ 9 KB budget (default `max_spec_chars: 9400`).
3. Fence policy: zero ` ```cpp ` fences under `guides/` and
   `big-question/`; bash fences legal; validators stay blind (outside
   DEFAULT_DIR; no DOC_PREFIX entry; relative-link check + hand review are
   the gates).
4. Growth, scoped: `big-question/` is the consumer scar home (contributing
   format, severity index, incident files without frontmatter; index.md with
   frontmatter). `guides/` ships curated — no append instructions.
5. **Supersession paragraph**: references archived
   `09-08-thinking-guide-layer/discussion.md` resolution (2026-09-09),
   names the changed circumstance (every ecosystem trellis project ships a
   consumer growth path; ours shipped none), and states what survives
   (template-side curation through releases).
7. Links preserved and extended: repo-relative `../cpp/<phase>/<doc>.md`
   (in-repo + post-install) stays binding for all phase rows; document the
   `../big-question/index.md` pointer pattern for the two deferred pointers
   (child 2 lands them).
8. Sync obligations: add "any file added/removed under `guides/` or
   `big-question/` updates `specs/cpp/README.md` tables + layout trees" to
   the existing list.

## Budget accounting (targets, all ≤ 9 KB)

| File | Current | Target |
|------|---------|--------|
| `index.md` | 8,680 B | ≤ 8,600 B (binding: compress prose before trimming links; drop one Quick-Ref bullet group if over) |
| phase guides ×3 | — | 3,500–5,000 B each |
| family-standard ×3 | — | 2,500–4,000 B each |

Headroom check per file at write time; compress prose before trimming links.

## Cutover / orphan analysis

- `index.md`: edited in place at the same path — pristine consumers refresh
  silently; locally-modified consumers get the "Modified by you" prompt.
- All other files: pure additions — install additively, no cleanup.
- No renames, no moves → zero orphans, `USAGE.md` stays true unchanged.
- `cpp/index.md` checklist row: verify the Unsure-which-guide row still
  resolves to `../guides/index.md`; no edit.

## Risks

- **Duplication with `cpp/index.md` Pre-Development Checklist**: mitigated —
  Quick Reference is symptom-phrased; the router overview states the
  division; hand review compares both files' trigger sets.
- **Injection crowd-out**: 7 files × C++ glob = more injected bytes per C++
  touch. Mitigation: per-file ≤ 9 KB budget; `description:` lines carry the
  index; if budget degrades FULL blocks, that is per-consumer config
  (`max_spec_chars`), documented, not ours to fix here.
- **Stock text copying**: paraphrase all family boilerplate; house rule
  (own prose, CG-citation rule analog).
- **big-question pointer before child 2 lands**: router points at
  `../big-question/index.md` which does not exist until child 2 — the
  relative-link gate would fail. Sequencing: child 2 lands in the same
  integration window; child 1 must not merge to `main` alone (ordered:
  reshape → scar-home → gates), or the pointer line lands with child 2.
  DECISION: child 1 does NOT add the router pointer line; child 2's change
  adds it (keeps every merged state gate-green).
