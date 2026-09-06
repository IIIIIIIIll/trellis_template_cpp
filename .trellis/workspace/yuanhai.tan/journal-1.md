# Journal - yuanhai.tan (Part 1)

> AI development session journal
> Started: 2026-08-24

---



## Session 1: C++ spec review: index coverage fix + editorial content pass

**Date**: 2026-08-30
**Task**: C++ spec review: index coverage fix + editorial content pass
**Branch**: `main`

### Summary

Completed task 08-25-cpp-spec-review (work spanning 2026-08-25 commits d8bf444..daf526d and this session): finished the last review queue item (rebuilt index.md read-through — 49 cited IDs verified against the 2026-08-30 upstream snapshot; section coverage closed: PER->Per, +Pro/GSL/RF ledger rows), then ran a second editorial pass over all 11 docs for advice soundness/benefit (6 parallel reviewers: 39 findings + 17 gaps, all docs keep) and applied the developer-approved full fix via 6 parallel editors (56/56 items; compile/ASan/UBSan-verified example rewrites incl. range-for intermediate temporaries, type-erasure decay, lock_guard trap; new Third-Party Dependencies home for SL.1-4). Gates: manifest, links, footers, four-way invariant all pass.

### Git Commits

| Hash | Message |
|------|---------|
| `8b30d72` | (see git log) |
| `e6a483a` | (see git log) |

### Status

[OK] **Completed**


## Session 2: Machine-consumable rule structure for cpp guidelines

**Date**: 2026-08-30
**Task**: Machine-consumable rule structure for cpp guidelines
**Branch**: `main`

### Summary

Task 08-30-cpp-rules-machine-format: restructured the shipped cpp guidelines for LLM-session consumption. Index split to routing-only (91 lines) with governance moved to core-guidelines-disposition.md (12th file, four-way invariant synced). All 540 normative rules across 10 guides now carry stable local AREA-n IDs + per-rule hard/default strength (329/211; 23 flagged strengths adjudicated, all accepted as marked) with normalized Caught-by detector lines. New tools/ (stdlib Python): validate_rules.py (grammar/id/strength/detector/pairing/link gate, 0 violations), extract_rules.py (deterministic rules.json digest, 540 rules, byte-identical reruns), check_snippets.py (121 fenced blocks compile: 41 clean / 4 must-fail / 76 UB-inventory, C++20 fence support via '// C++20' annotation, per-doc stubs). Contract codified in guideline-authoring.md; three gates wired into registry Quality Check. All work committed; acceptance criteria 6/6 ticked.

### Git Commits

| Hash | Message |
|------|---------|
| `6e99321` | (see git log) |
| `dfd4126` | (see git log) |
| `9856cca` | (see git log) |
| `84507f4` | (see git log) |
| `63cbf55` | (see git log) |

### Status

[OK] **Completed**


## Session 3: Lower C++ guideline baseline to C++14

**Date**: 2026-09-01
**Task**: Lower C++ guideline baseline to C++14
**Branch**: `main`

### Summary

Task 08-31-cpp14-baseline: baseline of the shipped cpp guideline set lowered from C++17 to C++14 while keeping every C++17/20 recommendation as a marked upgrade. Tooling (7b9c7be): // C++17 fence marker + Fence.cxx17 in rules_grammar.py, CXX14_FLAGS + flags_for() three-way selection in check_snippets.py, stub declarations/includes dialect-guarded at __cplusplus >= 201703L (15/15 dialect combos verified). Docs (634902d): canonical C++14 baseline paragraph in all 10 topic guides + index/README/disposition; 43 rule statements rewritten C++14-first with **C++17:**/**C++20:** notes; 37 fences marked; rules.json regen (540 rules, IDs/strengths/pairings unchanged, byte-identical); carried pre-session R.22<->R.23 citation fix. Hygiene (8c95c10): pyc untracked, *pyc ignored. Gates all green: validate_rules 0, check_snippets 121 blocks 0 violations, digest deterministic, manifest/links clean; AC4 sweep clean; AC6 hand-compiles green incl. negative control (stripped marker fails with string_view error — no stub masking). Seven parallel slices (S0 tooling + S1-S6 docs) + trellis-check full-scope pass (fixed testing-conventions Overview gap + 2 concurrency cells). Spec capture: guideline-authoring Dialect markers bullet + _v-trait-aliases-are-C++17 gotcha. Notable correction: S3 probe showed _v trait aliases are C++17, median fence rewritten to ::value.

### Git Commits

| Hash | Message |
|------|---------|
| `7b9c7be` | (see git log) |
| `634902d` | (see git log) |
| `8c95c10` | (see git log) |

### Status

[OK] **Completed**


## Session 4: Quality-guidelines review fixes

**Date**: 2026-09-05
**Task**: Quality-guidelines review fixes
**Branch**: `main`

### Summary

Reviewed specs/cpp/cpp/quality-guidelines.md against guideline-authoring spec: all validators green; blessed // Good:// Bad: as encoding 4 (style-only anti-patterns); dropped redundant comment-discipline sentence; added Enumerations default-strength line; folded QUAL-48 third segment into Right; rephrased QUAL-57 annotation. Full gate re-run green; digest unchanged.

### Git Commits

| Hash | Message |
|------|---------|
| `ee05bc2` | (see git log) |

### Status

[OK] **Completed**


## Session 5: Fix expressions-and-flow review findings

**Date**: 2026-09-06
**Task**: Fix expressions-and-flow review findings
**Branch**: `main`

### Summary

Review-fix pass over specs/cpp/cpp/expressions-and-flow.md: gave EXPR-26 its own Caught-by line (digest had paired it with EXPR-25's modernize-use-nullptr), marked EXPR-40's [[fallthrough]] as a C++17 upgrade over the C++14 comment spelling, made EXPR-3's Wrong exhibit the UB it claims, re-encoded the style-only EXPR-10/16/37 examples as Good/Bad fences with per-half names, fixed ES.74/ES.41/EXPR-26/EXPR-42 citation precision, moved EXPR-27's 240-char inline comment into preceding lines, and regenerated rules.json. Added a caught-by inheritance gotcha to the registry authoring spec. All gates green: validate_rules 10 docs 0 violations, check_snippets 122 blocks 0 violations, digest byte-identical; trellis-check PASS.

### Git Commits

| Hash | Message |
|------|---------|
| `16469ca` | (see git log) |

### Status

[OK] **Completed**


## Session 6: Phase-oriented restructuring of cpp guidelines

**Date**: 2026-09-06
**Task**: Phase-oriented restructuring of cpp guidelines
**Branch**: `main`

### Summary

Restructured specs/cpp/cpp from 12 flat docs to 19 phase-organized files: 14 topic guides filed one-phase-each under design/, implement/, verification/ (ERR, MEM, QUAL split at self-contained seams; ERR/MEM/QUAL prefix rows now span 2/2/3 docs), three zero-rule phase routers, index + disposition unmoved. Every content doc carries description+paths frontmatter for spec_match injection (consumer-sim: 18 docs selected, index excluded). Tools rebound: rglob walkers in validate/extract/check_snippets, DOC_PREFIX/PREFIX_ALLOCATION map (review caught it silently disabling prefix+footer checks on 7 split docs), exempt routers in rules_grammar, stub labels. rules.json regenerated: 539 rules, ID set byte-identical to HEAD. Sync surfaces updated (index tables, both READMEs, USAGE orphan-cleanup wording, disposition retargets, registry/index counts). Lessons captured into guideline-authoring.md: frontmatter contract, blind-validator warning, tool-binding sync obligations. Verified by three trellis-check agents; final gates: validate 14/0, digest deterministic, snippets 122 blocks 0 violations, links clean. cb624ae = user's static_assert message fix absorbed on the way.

### Git Commits

| Hash | Message |
|------|---------|
| `a5514b2` | (see git log) |
| `cb624ae` | (see git log) |

### Status

[OK] **Completed**
