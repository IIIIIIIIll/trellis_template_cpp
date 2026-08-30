# Machine-Consumable Rule Structure for cpp Guidelines

## Goal

The `specs/cpp/cpp/**` guidelines are consumed primarily by LLM sessions injected
through the Trellis workflow. This task restructures them for that consumer:
stable rule identities, per-rule strength markers, a parseable rule-block
format with a validator, a generated machine digest for cheap session routing,
a routing-only index, and a compile gate that keeps code examples honest.

## Developer decisions (2026-08-30, from review discussion)

1. **Examples stay** (deletion rejected): Wrong/Right pairs are the most
   token-efficient rule encoding for an LLM. Corrosion risk is answered by a
   snippet-compile gate, not deletion.
2. **index.md keeps routing only**: Overview, Guidelines Index, Pre-Development
   Checklist, Quality Check, stance vocabulary, footer. The governance
   machinery (disposition-by-section table, residual ledger, adoption/demotion
   process, upkeep, profiles) moves to a new document loaded on demand.
3. **Local rule IDs for every rule** (developer will add more of their own
   over time): a rule's identity is its local `AREA-n` ID; Core Guidelines
   IDs remain in the text as cross-reference anchors only.
4. **Per-rule strength markers** (not an overview-level convention): every rule
   individually marked hard or default.
5. **Unified parseable format** so validation, splitting, and extraction can be
   coded later; markdown stays the single source of truth, machine views are
   generated from it.

## Scope

- `specs/cpp/cpp/*.md` — all 11 existing docs + 1 new disposition doc
- `specs/cpp/README.md`, top-level `README.md` — file-set sync
- `.trellis/spec/registry/guideline-authoring.md` — contract update
- `.trellis/spec/registry/index.md` — Quality Check gate additions
- New `tools/` directory — validator, digest extractor, snippet harness
  (stdlib Python only; no new runtime dependencies)

## Out of scope

- No rule-substance edits (advice content is frozen from the 08-30 editorial
  pass; only structure/markers change).
- No consumer-side Trellis platform changes — injection granularity belongs to
  the platform; this task only makes the content mechanically addressable.

## Acceptance criteria

- [ ] Every normative rule in the 11 docs carries a unique local `AREA-n` ID
      and a per-rule `(hard|default)` strength marker; local IDs unique,
      stable, append-only; Core Guidelines IDs remain in text as
      cross-reference anchors only.
- [ ] Validator passes repo-wide: closed strength vocabulary; every rule has a
      detector or an explicit "no detector" statement; Wrong/Right pairs
      complete; footers intact; four-way file-set invariant holds including
      the new 12th file.
- [ ] `index.md` is routing-only; disposition machinery lives in the new doc;
      all sync points (guidelines index table, README table, README tree, top
      README tree) updated.
- [ ] `rules.json` digest is generated from source by the extractor (never
      hand-edited) and regenerates byte-identical on a no-change rerun.
- [ ] Snippet gate: every fenced ```cpp block compiles under
      `g++ -std=c++17 -Wall -Wextra`; Right examples compile clean; Wrong
      examples either fail compilation exactly at their annotated construct or
      carry an explicit compiles-but-UB marker; gate wired into the registry
      Quality Check.
- [ ] `guideline-authoring.md` documents the rule-block grammar, ID allocation,
      strength vocabulary, digest-regeneration obligation, and the new file's
      sync duties.
