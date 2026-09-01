# PRD: Lower C++ guideline baseline to C++14

## Problem

The shipped C++ guideline template states baseline C++17. A consumer project
still on C++14 cannot apply the guidelines as written: the docs reference
C++17/20 constructs without a C++14 spelling — `std::string_view` (~42 refs),
`std::span` (~25), `[[nodiscard]]` (~14), `if constexpr` (~10),
`std::optional` (~7), inline variables, structured bindings, `std::variant`.

## Goal

Baseline becomes C++14. Every rule is followable as written by a C++14
project; C++17/20 recommendations are retained as marked upgrades; the
snippet gate enforces the new baseline.

## Requirements

- R1: Every normative rule in the 10 topic guides is satisfiable with
  C++14-only language and library.
- R2: C++17/20 recommendations are NOT deleted — they remain as marked
  upgrades (`**C++17:**` / `**C++20:**` prose notes, marker'd snippets).
- R3: Snippet gate baseline becomes `-std=c++14`; new `// C++17` fence
  marker; existing `// C++20` marker unchanged.
- R4: Stub headers (`tools/stubs/**`) compile and serve snippets at all
  three dialects (C++14/17/20).
- R5: Registry claims updated: `specs/cpp/README.md`,
  `.trellis/spec/registry/guideline-authoring.md`, every doc's Overview
  baseline sentence.
- R6: Rule IDs, strengths, rule count, and Caught-by pairing unchanged —
  no new rules, no renumbering, no deletions.
- R7: All quality gates green after the change.

## Constraints

- Documentation in English; house style per guideline-authoring.md
  (Wrong/Right encodings, marker grammar, ~78-80 col wrap).
- `rules.json` is regenerated only by the integration step, never per-slice.
- Core Guidelines citations stay as anchors (IDs unchanged).

## Acceptance Criteria

- AC1: `python3 tools/validate_rules.py` → 0 violations.
- AC2: `python3 tools/check_snippets.py` → 0 violations; every fence naming
  a C++17+ symbol carries `// C++17` or `// C++20`; unmarked fences compile
  at `-std=c++14`.
- AC3: `extract_rules.py` run twice → byte-identical `rules.json`; 540 rules.
- AC4: No doc states C++17 as the baseline; each Overview states the C++14
  baseline.
- AC5: `specs/cpp/README.md` and guideline-authoring.md state the new
  baseline contract and document the `// C++17` marker.
- AC6: C++14 smoke: hand-compile a representative unmarked Right example
  from memory-and-ownership.md and functions-and-interfaces.md at
  `-std=c++14` against the stubs.

## Non-goals

- No C++14 feature-guidance rules added (separate decision).
- No rule additions, deletions, or renumbering.
- No C++11 support.
