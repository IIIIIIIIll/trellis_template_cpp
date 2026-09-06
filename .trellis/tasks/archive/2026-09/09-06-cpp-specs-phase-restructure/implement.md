# Implementation Plan

## Ordered Checklist

### Stage 1 — Frontmatter pass (no moves)
1. Add `paths:` frontmatter (shared C++ glob list per design.md) to the 11
   content docs (all except `index.md`); add test-scoped extra globs to
   `testing-conventions.md`.
2. Smoke-test selection: call
   `match_specs_for_file(repo_root, 'src/demo.cpp')` in a throwaway script —
   expect the cpp docs listed; `src/demo_test.cpp` — expect testing docs
   first.

### Stage 2 — Moves and splits (mechanical, per design.md tree)
3. ERR split → `design/error-contracts.md` (28–300) +
   `implement/error-propagation.md` (301–475); delete source.
4. MEM split → `design/ownership-design.md` (61–93, 159–180) +
   `implement/memory-discipline.md` (20–60, 94–158, 181–280); delete source.
5. QUAL split ×3 → `design/headers-and-dependencies.md` (186–460),
   `implement/naming-and-constants.md` (19–111, 461–545),
   `verification/static-analysis.md` (112–185); delete source.
6. Whole moves: FN/CLS/TPL → `design/`; EXPR/CONC/PERF → `implement/`;
   TEST → `verification/`.
7. Each split part gets `# Title` + `>` summary + `## Overview` + two-line
   footer; carried sections verbatim.
8. Tools rebind: `validate_rules.py` bind set → 14 rule docs;
   `check_snippets.py` path set likewise; `extract_rules.py` re-run →
   regenerate `specs/cpp/cpp/rules.json` (never hand-edit).
9. Link sweep: retarget every link naming a moved/split doc (disposition
   rows E/R/SF/Enum/NL/SL; FN → ownership ladder; authoring prefix table).
10. **Gate**: `validate_rules.py` + digest determinism + `check_snippets.py`
    + specs link check. Fix before proceeding.

### Stage 3 — Reading surface
11. Write 3 routers (`design.md`, `implementation.md`, `verification.md`)
    at layer root — reading paths + phase checklists, zero rule text, all
    pointers.
12. Regroup `index.md`: Guidelines Index + Pre-Development Checklist under
    Design / Implementation / Verification / Alignment & Governance.
13. Update `specs/cpp/README.md` (table + tree), registry `README.md`
    layout tree, `USAGE.md` install claims if any.
14. Gate: link check + four-place file-set equality (cpp/index.md,
    specs/cpp/README.md, registry README.md tree, actual tree).

### Stage 4 — Full verification
15. All gates again + injection smoke test (both file kinds) + manual
    skim: every phase router reaches every rule doc of its phase; no rule
    text duplicated between routers and rule docs.

## Delegation Map (sub-agent dispatch)

- Stages 2.3/2.4/2.5 + 2.6 are independent per source doc → parallel
  dispatch, one agent per source doc (ERR, MEM, QUAL, wholes).
- 2.7 folds into each agent's assignment.
- 2.8–2.10 and everything in stages 3–4: single integration owner
  (shared files: tools, rules.json, index, READMEs, authoring spec).
- Cross-agent contract (stated in every assignment): exact target tree,
  shared glob list, no rule-text edits, section line-ranges from the
  section map in design.md, each part gets full doc shape.

## Validation Commands

```bash
python3 tools/validate_rules.py
python3 tools/extract_rules.py && cp specs/cpp/cpp/rules.json /tmp/rules-a.json \
  && python3 tools/extract_rules.py && cmp specs/cpp/cpp/rules.json /tmp/rules-a.json
python3 tools/check_snippets.py
# + the link-check and manifest checks from .trellis/spec/registry/index.md
```

## Risky Files / Rollback Points

- `guideline-authoring.md` — injected spec; prefix-table and doc-count edits
  must respect its own contracts (closed strength vocabulary, stable IDs).
- `tools/validate_rules.py`, `tools/check_snippets.py` — binding changes
  only; no logic rewrites.
- `specs/cpp/cpp/rules.json` — generated output; regenerate, never edit.
- Rollback: one commit per stage; regen determinism makes rollback
  byte-verifiable.

## Pre-start

- `implement.jsonl` / `check.jsonl` curated with real spec entries (done).
- Fresh user approval of the final planning summary (pending).
