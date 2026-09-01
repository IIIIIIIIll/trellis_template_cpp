# Design: Lower C++ guideline baseline to C++14

## Decision: tiered baseline, not strict downgrade

Rules keep their best-practice C++17/20 recommendations; every rule gains a
C++14-expressible default spelling. Rationale: deleting `string_view` /
`optional` guidance would degrade the product for C++17+ consumers and
contradict the "opinionated defaults" contract; the tiered form mirrors the
docs' existing C++20 `std::span` pattern ("the rules are identical either
way").

## Contract 1 — Overview baseline paragraph (canonical, all 12 docs)

Exact text (wrap to house width):

> Baseline: C++14 (`std::make_unique`, generic lambdas, relaxed
> `constexpr`). C++17 and C++20 additions appear as marked upgrades where
> they change the recommendation — `std::string_view`, `std::optional`,
> `if constexpr`, `[[nodiscard]]`, `std::span` — each with the C++14
> spelling alongside, so a C++14 project can follow every rule as written.

If a doc's Overview already phrases the baseline differently, replace that
phrasing with this paragraph. Where the Overview already carries a C++20
sentence (memory, concurrency, templates), fold it in — do not keep both.

## Contract 2 — rule prose marking

- Rule body: C++14 default spelling first; upgrade appended as a bold note:
  `**C++17:** `std::string_view`` / `**C++20:** `std::span``.
- Table cells: parenthetical form
  `std::string_view` (C++17; C++14: `const std::string&`).
- Never delete the C++17+ recommendation. IDs, strengths, Caught-by lines
  unchanged. If a detector itself is C++17-only, note that in the Caught-by
  line.

## Contract 3 — snippets and gate

- New dialect marker `// C++17` (regex `//\s*C\+\+17\b`), `Fence.cxx17`
  field in rules_grammar.py. check_snippets.py flag selection: `cxx20` →
  `-std=c++20`; else `cxx17` → `-std=c++17`; else new baseline
  `-std=c++14` (CXX14_FLAGS).
- Policy: any fence naming a C++17+ symbol or syntax (`string_view`,
  `optional`, `span`, `variant`, `if constexpr`, `[[nodiscard]]`, inline
  variables, structured bindings) carries the matching marker; unmarked
  fences must compile at C++14.
- Marker placement: comment line at/near the fence top; coexists with
  Wrong/Right/UB/compile-error markers.

## Contract 4 — stubs at three dialects

- Verified by probe (research/dialect-probes.md, g++ 13.3.0):
  - C++17 headers include fine at C++14 (contents guarded out) — guard the
    includes anyway for libc++ portability.
  - Stub declarations naming `std::optional` / `std::string_view` /
    `std::variant` (and the `BytesView` alias) MUST be guarded behind
    `#if __cplusplus >= 201703L` — the names do not exist at C++14.
  - Inline namespace-scope variables compile at C++14 with a warning only —
    stubs keep them unchanged (no `-Werror` in gate flags).
  - `tl/expected.hpp` fails at C++14 (internal `std::variant`) — guard its
    include behind `>= 201703L`; `expected`-naming fences get `// C++17`.
  - No fence today names `std::span` in code (else the C++17 gate would be
    red) — span stays prose-only; `// C++20` marker grammar kept for
    prose-mandated C++20 idioms.
- Fallback C++14 spellings only where an unmarked snippet needs a name at
  C++14 (expected: none after the marker policy).
- per-doc stub (`tools/stubs/per-doc/expressions-and-flow.hpp`): same
  guarding.

## Contract 5 — registry claims

- specs/cpp/README.md: "Baseline is C++14; C++17/20 additions
  (`std::string_view`, `std::optional`, `if constexpr`, `[[nodiscard]]`,
  `std::span`) are called out as marked upgrades where they matter."
- guideline-authoring.md Content Rules: baseline sentence updated; document
  the `// C++17` marker next to the UB / compile-error markers in Rule
  Blocks.
- index.md, core-guidelines-disposition.md, registry-contract.md: sweep
  C++17 claims and update.
- error-handling.md: retitle the "## C++17 Baseline: `std::expected` Is
  C++23" section (drop "C++17 Baseline").

## Slice decomposition (parallel; files disjoint)

| Slice | Files |
|-------|-------|
| S0 tooling | tools/rules_grammar.py, tools/check_snippets.py, tools/stubs/** |
| S1 functions | specs/cpp/cpp/functions-and-interfaces.md |
| S2 memory | specs/cpp/cpp/memory-and-ownership.md |
| S3 templates | specs/cpp/cpp/templates-and-generics.md |
| S4 classes+quality | specs/cpp/cpp/classes-and-hierarchies.md, quality-guidelines.md |
| S5 light docs | expressions-and-flow.md, error-handling.md, performance.md, concurrency.md, testing-conventions.md |
| S6 claims | specs/cpp/README.md, cpp/index.md, core-guidelines-disposition.md, .trellis/spec/registry/guideline-authoring.md |
| Integration (main) | rules.json regeneration, full gate suite, AC4-6, straggler fixes |

## Risks

- GCC 13 `<span>` at C++17: header includable; class availability relies on
  stubs — S0 verifies `std::span` usability per dialect.
- Stub C++14 fallback names could mask a missing fence marker — AC6
  hand-compile spot-check guards this.
- Mid-flight check_snippets sees other docs' un-migrated fences: slices
  filter output to their own doc rows and ignore the rest.
