# Design: Phase-oriented restructuring of C++ guideline specs

## Target Architecture

```
specs/cpp/
├── README.md                           ← table + tree updated (final state)
└── cpp/                                ← single layer, identity unchanged
    ├── index.md                        ← phase-grouped tables + Alignment & Governance
    ├── core-guidelines-disposition.md  ← unmoved (D3)
    ├── design.md                       ← router, owns no rules
    ├── implementation.md               ← router, owns no rules
    ├── verification.md                 ← router, owns no rules
    ├── design/
    │   ├── functions-and-interfaces.md      whole (621)
    │   ├── classes-and-hierarchies.md       whole (569)
    │   ├── templates-and-generics.md        whole (440)
    │   ├── error-contracts.md               ← ERR split A: sections "Choosing a Mechanism"
    │   │                                      → "Exceptions Policy" (28–300)
    │   ├── ownership-design.md              ← MEM split A: "The Ownership Ladder" (61–93)
    │   │                                      + "Smart Pointers in Signatures" (159–180)
    │   └── headers-and-dependencies.md      ← QUAL split A: "Header Hygiene" (186–334)
    │                                          + "ODR and ABI Pitfalls" (335–442)
    │                                          + "Third-Party Dependencies" (443–460)
    ├── implement/
    │   ├── memory-discipline.md             ← MEM split B: "RAII Is Non-Negotiable" (20–60)
    │   │                                      + "Pass-by Rules" (94–158)
    │   │                                      + "Lifetime Pitfalls" (181–280)
    │   ├── error-propagation.md             ← ERR split B: "noexcept Discipline" (301–355)
    │   │                                      + "Propagation Across Module Boundaries"
    │   │                                      (356–407) + "Logging vs Handling" (408–475)
    │   ├── naming-and-constants.md          ← QUAL split B: "Naming Conventions" (19–111)
    │   │                                      + "Enumerations" (461–497)
    │   │                                      + "Compile-Time Discipline" (498–545)
    │   ├── expressions-and-flow.md          whole (460)
    │   ├── concurrency.md                   whole (359)
    │   └── performance.md                   whole (291)
    └── verification/
        ├── testing-conventions.md           whole (312)
        └── static-analysis.md               ← QUAL split C: "Static Analysis Curation"
                                               (112–185)
```

19 files: 12 → 14 rule docs + 3 new routers; `index.md` and the disposition
never move. Routers sit at layer root, not `<phase>/index.md`, to avoid any
ambiguity with layer-index discovery conventions.

## Contracts

### Injection contract (frontmatter, R3)

`spec_match.py` selects specs by frontmatter `paths:` globs against the
touched file (`rglob("*.md")` over `.trellis/spec/`, line 346); a doc
without `paths:` is never injected through this path. Therefore:

- **All 14 rule docs + 3 routers + disposition** declare the shared C++
  glob list: `**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h,
  **/*.inl, **/*.ipp`.
- **testing-conventions.md and static-analysis.md** additionally declare
  test-scoped globs (`**/test*/**`, `**/*_test.*`, `**/*Test.*`,
  `**/tests/**`). Scorer reality (verified against `spec_match.py`):
  specificity keys to each doc's FIRST matching glob and every glob scores
  equal-or-worse than `**/*.cpp` (more wildcards rank lower), so test globs
  cannot promote verification docs in the FULL-block budget. They are kept
  as semantic documentation and future-proofing; the context-economy levers
  are file granularity and descriptions, both delivered.
- **index.md declares no frontmatter**: it is the layer entry point read by
  convention (`trellis-before-dev`), never a path-selected injection.
- Fan-out behavior is accepted and documented: one C++ touch matches many
  docs of equal specificity; `spec_inject.py` fills the FULL budget in
  specificity order with `rel_path` as the deterministic tie-break and
  degrades the rest to description index lines. Index lines still route.

### Rule contracts (R4, R5)

- **IDs**: zero renumbering; every moved/split rule keeps its ID. Doc moves
  are mechanical; no rule text edits during moves (content edits only if a
  gate fails).
- **`tools/validate_rules.py`**: bind set becomes the 14 rule docs
  (`design/`, `implement/`, `verification/` paths); `index.md`, the
  disposition, and the routers stay exempt.
- **`tools/extract_rules.py`**: unchanged logic; `rules.json` regenerated —
  the `doc` field follows the new locations.
- **`tools/check_snippets.py`**: path set follows the same 15 docs;
  snippets travel verbatim with their sections.
- **Prefix table** (`guideline-authoring.md` Rule IDs section) gains rows:
  `ERR-` → error-contracts.md, error-propagation.md;
  `MEM-` → ownership-design.md, memory-discipline.md;
  `QUAL-` → headers-and-dependencies.md, naming-and-constants.md,
  static-analysis.md. All other prefixes unchanged.

### Doc shape (per guideline-authoring.md)

Each split part is a complete document: `# Title` + one-paragraph `>`
summary + `## Overview` stating that half's stance + the carried sections
verbatim + the exact two-line footer (Language note + attribution).
Sections carry their `Caught by:` lines and strength defaults with them;
the EXPR-26 class of bug is guarded by running `validate_rules.py` after
each split, not at the end.

### Sync surface (same-change obligations, R5)

For every stage that adds/moves/renames a file:

1. `specs/cpp/cpp/index.md` — Guidelines Index **and** Pre-Development
   Checklist (regrouped per phase).
2. `specs/cpp/README.md` — Guideline Files table **and** install-layout
   tree.
3. Registry-level `README.md` layout tree and `USAGE.md` install claims —
   the subdirectory layout is a visible change to what installs.
4. `core-guidelines-disposition.md` routing links retargeted: `E` →
   error-contracts.md (propagation half noted), `R` → ownership-design.md,
   `SF`/`Enum`/`NL`/`SL` rows → their split targets, `Per`/others
   re-verified.
5. Guide cross-links retargeted where they name a moved doc:
   functions-and-interfaces → ownership-design.md (ladder),
   error-contracts → performance.md (PERF-1) preserved,
   expressions-and-flow → performance.md preserved.
6. `guideline-authoring.md` — prefix table rows plus any doc-count
   references.

All links stay repo-relative within `specs/cpp/`; docs inside phase
subdirs reach siblings and the disposition via `../`.

## Staging

| Stage | Content | Gate |
|---|---|---|
| 1 | Frontmatter pass on the 11 existing content docs (no moves) | link check; `match_specs_for_file` smoke test returns cpp docs for a dummy `.cpp` path |
| 2 | Splits (ERR, MEM, QUAL) + whole-doc moves into phase dirs; tools rebind; `rules.json` regen; link/disposition/prefix-table sweep | `validate_rules.py`, digest determinism, `check_snippets.py`, link check — run here, not at the end |
| 3 | Routers ×3 + index regroup + README ×2 + USAGE claims | link check; four-place file-set equality |
| 4 | Full verification | all gates + injection smoke test + file-set check |

## Trade-offs (recorded)

- FN/CLS/TPL stay 440–621 lines: they are honestly single-phase; splitting
  them buys context bytes at the cost of fragmenting the design anchors the
  phase exists to highlight. The FULL→ticket degradation bounds the cost.
- PERF stays whole in implement: its verification half ("Measure First" +
  Anti-Rule) is ~60 lines — too thin for a document. The verification
  router links PERF-1…PERF-6 explicitly.
- verification/ is thin by content reality (TEST 312 + curation ~75):
  routers compensate by routing the measurement and TSan rules that live in
  implement-side docs.
- Over-splitting to hit a doc count was rejected: seams exist only where
  sections are self-contained; forcing more would break section-scoped
  Caught-by inheritance (EXPR-26 class).

## Compatibility / Rollback

- Template identity unchanged: registry `index.json` entry `cpp` (path
  `specs/cpp`) continues to exist; the layer is still one directory, so
  consumer install and update flows are structurally untouched — only the
  inner tree changes, which is what README/USAGE document.
- No consumer-side migration logic is required; `trellis update` applies
  the tree through the standard hash/conflict flow.
- One git commit per stage = rollback point; `rules.json` regeneration is
  deterministic (digest check), so rollback is byte-verifiable.
