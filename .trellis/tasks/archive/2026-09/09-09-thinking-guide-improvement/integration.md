# Parent integration review (2026-09-10)

> Union verification of both children on the merged tree. Parent owns the
> cross-child acceptance criteria; this file is its sign-off record.

## Commits

| Commit | Change |
|--------|--------|
| `78e8faf` | `docs(spec): rewrite thinking-guide layer contract to family shape` (child 1) |
| `584d3e4` | `docs(guides): reshape cpp thinking-guide layer to family shape` (child 1) |
| `31937fd` | `docs(guides): add big-question scar home and land deferred pointers` (child 2) |
| `fa105f2` | `docs(spec): sync registry specs with the big-question layer` (child 2) |

## Cross-child acceptance — verified on the union

| Criterion | Result |
|-----------|--------|
| Manifest check (`index.json` paths exist) | PASS — `missing: []` |
| Relative-link check across `specs/` | PASS — rc=0, zero unresolvable `./`-relative targets |
| `tools/validate_rules.py` | PASS — 14 docs checked, 0 violations |
| Digest determinism (`extract_rules.py` ×2, byte-compare) | PASS — 539 rules, byte-identical, `rules.json` unchanged by this work |
| `tools/check_snippets.py` | PASS — 122 blocks / 19 docs [clean=43, must-fail=5, ub=74], 0 violations |
| 14/14 `cpp/` topic guides reachable from the layer | PASS (script over all 11 layer files) |
| Method survival: 15 phase rows + 4 spans = 19 | PASS — design 6 (5 carried + restored invalidation row), implementation 6, verification 3, spans 4 |
| Per-file ≤ 9 KB (injected files) | PASS — max 8,783 B (`guides/index.md`); all others ≤ 4.8 KB |
| Frontmatter rules | PASS — 7 `guides/` files + `big-question/index.md` carry `description:` + the shared C++ glob; the 3 incident files carry none |
| Zero ` ```cpp ` under `guides/` and `big-question/` | PASS |
| Supersession recorded in the contract | PASS — cites the archived 2026-09-09 resolution, the changed circumstance, and what survives |
| File-set sync | PASS — `specs/cpp/README.md` tree + both file tables, root `README.md` tree, `guideline-authoring.md` contract, `registry/index.md` product row |
| Carrier links resolve in-repo and post-install | PASS — uniform `../cpp/<phase>/<doc>.md` pattern at depth 1 (`guides/`, `big-question/` → `cpp/`), same structure post-install |

## Child reports

- Child 1: `trellis-check` PASS (no findings); `reviewer` PASS with 6 accuracy
  findings — the 5 non-frozen ones fixed (recipes' `-g` glob, UB heuristic
  softened, qualified "no compiler flags", row-6 read-first link, deferred
  pointer tense); `security-reviewer` PASS (5 low + 4 informational; the
  low ones reconciled — three fixed, two target PRD-frozen row text and were
  ruled out of scope by the second `reviewer`/`security-reviewer` pass).
- Child 2: `trellis-check` PASS (no findings, no edits);
  `reviewer` PASS (no findings) plus a navigation improvement taken (the
  router's `Growing This Layer` line is now the second scar-home link);
  `security-reviewer` PASS (2 informational accuracy fixes applied: erase
  taxonomy now names `vector`/`string` vs node-based containers; the
  `-O0`/`-O2` UB signature now carries the `NDEBUG`/timing confounder
  caveat). Both advisory roles re-confirmed all post-validation edits.

## Accepted deviations

1. Child 2 additionally edited `.trellis/spec/registry/index.md` (product
   row, tombstone parenthetical, Quality Check scope note) — recorded in the
   child-2 PRD addendum; the file became stale when child 1 redefined the
   layer to span two directories.
2. Child 2 also recorded the layer's `rg -g` recipe convention in the
   contract (beyond drift repair) — same addendum; the fact was discovered by
   review and would otherwise be re-learned by the next author.
3. `.omp/config.yml` (gitignored, project level) enables OMP advisors for the
   validation roles used in this session — harness configuration, not part of
   the shipped product.

## Residual risks (accepted)

- The 7-file `guides/` layer plus `big-question/index.md` share one unscoped
  C++ glob; a C/C++ touch injects ~30 KB of method prose alongside the topic
  guides, with `max_spec_chars` degradation as the only valve
  (design-acknowledged).
- The layer sits outside `validate_rules.py` / `check_snippets.py` walks by
  design; its gates are the relative-link check plus hand review. The
  `EXEMPT_DOCS` basename trap is now documented in `registry/index.md`.
- Consumer-grown incident entries rely on contributor discipline for the
  prose-only / link-don't-duplicate rules (the format is documented in
  `big-question/index.md`).
- Two inherited phrases inside PRD-frozen row text ("ASan's most common
  catch"; "ASan flags the use, never the store") are retained verbatim per
  the row-survival criterion; both were ruled technically defensible by the
  advisory passes.
