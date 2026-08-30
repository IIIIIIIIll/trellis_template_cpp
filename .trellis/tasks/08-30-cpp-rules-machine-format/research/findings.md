# Conversion Record — Machine-Consumable Rule Structure

## Phase 3 marking (2026-08-30, developer-approved)

- 540 rules across the 10 topic guides: **hard 329 / default 211**. IDs
  per-prefix (MEM/ERR/QUAL/TEST/FN/CLS/TPL/CONC/EXPR/PERF), document order,
  append-only from here on.
- 23 flagged strengths adjudicated by the developer: **all accepted as
  marked** (perfect-17-style measurement discipline rules stay default;
  evidence-deletion and dangling-class rules stay hard). Re-judging later is
  a strength edit only — IDs never move.
- Per-doc: MEM 49 (39h/10d) · ERR 52 (43/9) · QUAL 64 (55/9) · TEST 32
  (25/7) · FN 69 (32/37) · CLS 95 (44/51) · TPL 47 (15/32) · CONC 46
  (41/5) · EXPR 55 (25/30) · PERF 31 (10/21).
- Left unmarked by judgment (rule homes carry the claims): Quality Check
  checklists (mirror marked rules), clang-tidy curation + sanitizer tables,
  iterator-invalidation matrix, dialect decision matrix, routing/disposition
  prose, Good/Bad-labeled teaching fences (0-marker groups, validator-legal).

## Tooling decisions (ToolsScaffold, documented deviations from open design points)

- Section default syntax: standalone `Default strength: <hard|default>.` line.
- rules.json installs at `specs/cpp/cpp/rules.json`; footer- and
  validator-exempt; listed in both README trees as generated (never
  hand-edited; regenerate via `tools/extract_rules.py` in the same change as
  any rule edit).
- Detector = verbatim `Caught by:` text; the explicit no-detector statement
  normalizes to `review`.
- Unclassified Wrong blocks (compiling Wrong without a marker) are violations
  — the gate is total, no silent defaulting.
- Prose lead recognition: bare `Wrong`/`Right` forms; annotated variants
  (`Right (C++17):`) do not pair — Phase 3 normalized all such leads.
- Section-scope inheritance (strength + caught-by): nearest preceding heading
  of level ≤2.

## Phase 4 harness

- 121 fenced cpp blocks repo-wide: clean 41 / must-fail 4 / ub 76; exit 0.
- C++20 fences annotated `// C++20` (10 fences: dialect-table spellings, Task
  erasure `requires`, `std::span`/`jthread` blocks) compile under
  `-std=c++20`; everything else under `-std=c++17 -Wall -Wextra`.
- 16 fragment-level compile fixes (try-context for catch fragments, missing
  member declarations, `mutable` for `[*this]` capture, template-argument on
  bare `Result`, wrapped member declarations). Zero substantively-wrong
  examples found — every failure traced to fragment context or spelling.
- UB inventory: 76 entries (doc:line) — the manual sanitizer spot-check list;
  includes the range-for chained-temporary example.
- Gates wired into `.trellis/spec/registry/index.md` Quality Check: rule
  validator (0 violations), digest determinism (extract twice, byte-identical),
  snippet gate (exit 0).

## Commits

`6e99321` refactor(specs) · `dfd4126` feat(tools) · `9856cca` refactor(specs) ·
`84507f4` feat(tools)
