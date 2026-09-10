# Discussion: grilling interview log (2026-09-09)

> Record of the requirements interview that produced the parent PRD decision
> set. Compressed from the live session; decisions are binding, not this
> narrative.

## Round 1 — driver

Asked what drives "improve": concrete incident / coverage gap / usability /
reopen growth decision / just noticing divergence from stock trellis guides.
Answer: none of the named ones — "I do notice it is different from the
default thinking guides that ships with trellis." Contract boundary and
acceptance bar left open ("dunno"). Task creation consented (yes).

## Round 2 — evidence challenge

User pushed: check the stock guides AND other language templates; check the
GitHub. Result: stock = 4 generic files (read); marketplace submodule
cloned — 3 official templates, all TypeScript-family, NO Python template
exists. All siblings share one family shape; ours matches none of it. New
facts: scar separation (`big-question/` in all three), symptom-phrased cue
ontology (ours: diff shapes; spans table already mixed), Contributing
sections everywhere, no official Python template.

## Round 3 — narrowed ontology

Finding persisted: our guide is already mixed-ontology (phase tables = diff
shapes; cross-cutting spans = symptom signatures). Symptom-cue candidates
drafted in `research/symptom-cue-drafts.md`; two of three fit the 748-byte
headroom.

## Round 4 — convergence pinned

User: "I think for Q1 that is all of them like I want exactly what trellis
already ships say in python but targeting cpp instead." Corrected: no Python
template; target = marketplace-family shape. Questions elaborated; user
accepted all recommendations:

1. Variant (b): family shape + `big-question/` scar home.
2. Reverse the 2026-09-09 no-growth resolution — scoped to `big-question/`
   (method stays curated; router carries only a pointer).
3. Fence policy (α): zero ` ```cpp ` fences in `guides/` and
   `big-question/`; bash fences legal; no harness extension.
4. Guide set (a): phase-named guides re-homing the 18 rows 1:1 + restored
   invalidation row (→ `functions-and-interfaces.md`) + family-standard
   files.
5. Parent + two children.

Shared understanding confirmed by the developer; planning proceeded to
artifacts.

Provenance note: PRD decision 6 (sync mechanics — keep `guides/index.md`
path, pure additions, no `index.json`/`USAGE.md` change) derives from
`research/sync-set-inventory.md`, not from interview answers.
