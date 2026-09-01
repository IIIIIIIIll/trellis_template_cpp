---
description: Structure, tone, and cross-linking conventions for the shipped C++ guideline documents under specs/cpp/
paths: [specs/**]
---

# Guideline Authoring

> Conventions for writing and editing the guideline documents this registry
> ships — the files under `specs/cpp/cpp/` and their overview
> `specs/cpp/README.md`.

---

## Document Shape

Every guide under `specs/cpp/cpp/` follows the same skeleton. Real reference:
`specs/cpp/cpp/index.md`, `specs/cpp/cpp/quality-guidelines.md`.

1. `# Title` immediately followed by a one-paragraph `>` blockquote summary.
2. `## Overview` stating the guide's stance and scope — what it decides, not a
   table of contents restated.
3. Body organized by decision, using tables for mappings and **Wrong/Right**
   code pairs for rules.
4. Footer, exactly two lines: the `**Language**` note and the Core Guidelines
   attribution (see `specs/cpp/cpp/index.md` bottom). Every guide under
   `specs/cpp/cpp/` carries both; the layer-overview README is exempt.

Wrong/Right pairs are the house style for any rule that can be shown in code.
The wrong example names what a reviewer would flag; the right example carries
the owning rule's local ID (`AREA-n`, see Rule Blocks below) as a comment when
one exists:

```cpp
// NOLINT                      ← Wrong: silenced with no trace of why
// Deviates from F.21: ...     ← Right: deviation travels with the code
```

Full examples: `specs/cpp/cpp/core-guidelines-disposition.md`
("Recording a Deviation").

---

## Rule Blocks

Every normative rule in a topic guide is one discrete block — a rule never
spans sections and never mingles with another rule's text. Prose rules use
this grammar:

````markdown
**MEM-7 (hard).** Never call `new`/`delete` for owning a single object; take
RAII ownership in one step.

<optional rationale, 1-3 sentences>

```cpp
// Wrong: ...
// Right: ...
```

Caught by: `cppcoreguidelines-pro-type-cstyle-cast`
````

- **Lead-in**: `**<AREA>-<n> (<strength>).**` — one greppable token serving
  citation (the ID), triage (the strength), and extraction (the position).
  Every rule — including rules whose substance is a Core Guidelines rule —
  carries a local ID; Core Guidelines IDs stay in the text as cross-reference
  anchors only (developer decision 2026-08-30).
- **Strength vocabulary is closed**: `hard` — violating the rule requires a
  deviation comment (rule ID + reason + what would change the answer, see
  "Recording a Deviation" in the Core Guidelines disposition); `default` — a
  measurement-backed local deviation is allowed without ceremony.
- **Caught-by pairing**: a rule names its detector on a `Caught by:` line; a
  rule nothing automated catches states
  `Caught by: review — no automated detector.` explicitly. A rule without its
  own line inherits the nearest preceding `Caught by:` line within the same
  section; a section-level line covers every rule below it that lacks its
  own.
- **Wrong/Right encodings** — all three are valid; pairing is judged per rule
  block, exactly one Wrong and one Right per example group:
  1. one fence holding both, split by `// Wrong:` / `// Right:` comments;
  2. two fences, each opening with its comment;
  3. two fences under prose lead lines (`**Wrong**` / `**Right**`).

  Wrong examples that compile but misbehave at runtime carry the
  `// compiles; UB at runtime` marker; Wrong examples whose point is a failed
  compilation carry `// compile-error` on the offending construct.
- **Dialect markers**: a fence naming a C++17-or-later symbol or syntax
  (`std::string_view`, `std::optional`, `if constexpr`, `[[nodiscard]]`,
  structured bindings) keeps that spelling and opens with a `// C++17`
  comment line at or near the fence top; `// C++20` marks C++20-only idioms.
  The markers match `//\s*C\+\+17\b` / `//\s*C\+\+20\b` (`Fence.cxx17` /
  `Fence.cxx20` in `tools/rules_grammar.py`); `tools/check_snippets.py`
  compiles a marked fence at `-std=c++17` / `-std=c++20` and every unmarked
  fence at the `-std=c++14` baseline. Dialect markers coexist with the
  Wrong/Right, UB, and compile-error markers.
  Versioning caution: the `_v` trait aliases (`std::is_arithmetic_v`) are
  C++17, not C++14 — an unmarked fence must use the `::value` member form.
- **List-item form**: a rule may be a bullet item
  (`- **MEM-7 (hard).** ...`); the lead-in grammar is identical after the
  `- `.
- **Table rows**: a row carrying a normative claim puts `**<ID>**` in its
  first cell, optionally appending `(hard)`/`(default)`; tables stay
  matrices — the block grammar governs prose rules.
- **Strength fallback**: strength comes from the cell or block marker, else
  the enclosing section's stated default (a standalone
  `Default strength: hard.` or `Default strength: default.` line in the
  section); if neither exists, `tools/validate_rules.py` flags the rule —
  there is no silent defaulting.

### Rule IDs

| Doc | Prefix | Doc | Prefix |
|-----|--------|-----|--------|
| memory-and-ownership | `MEM-` | classes-and-hierarchies | `CLS-` |
| error-handling | `ERR-` | templates-and-generics | `TPL-` |
| quality-guidelines | `QUAL-` | concurrency | `CONC-` |
| testing-conventions | `TEST-` | expressions-and-flow | `EXPR-` |
| functions-and-interfaces | `FN-` | performance | `PERF-` |

Numbering is **stable and append-only**: retired rules leave gaps and are
never renumbered; IDs are unique repo-wide.

`tools/validate_rules.py` binds the 10 topic guides; `index.md` and
`core-guidelines-disposition.md` are exempt (disposition rows are stances,
not rules). Any rule add, change, or delete re-runs `tools/extract_rules.py`
in the same change to regenerate the `rules.json` digest — the digest is
derived from the markdown and is never hand-edited. `rules.json` itself is
footer-exempt and validator-exempt: it is generated output, not an authored
document.

---

## Content Rules

- **Opinionated defaults, not surveys.** Guides pick a side and say why.
  Baseline is C++14; C++17/20 additions appear as marked upgrades where they
  change the recommendation — a rule states the C++14 spelling first, then
  the upgrade as a bold `**C++17:**` / `**C++20:**` note (table cells use
  the parenthetical form `std::string_view` (C++17; C++14:
  `const std::string&`)).
  (`specs/cpp/README.md` states this contract.)
- **Core Guidelines citations are anchors, never copies.** Cite IDs like
  `F.21`, `ES.20`; write our own paraphrase. The Guidelines' prose and
  examples are never copied into this repository — license footer exists
  because of this rule.
- **Stance vocabulary is fixed**: *Adopt*, *Adapt*, *Covered elsewhere*
  (defined in `specs/cpp/cpp/index.md`). *Adapt* obligates a written,
  reasoned difference in the companion guide — an adapted rule silently
  dropped is a broken contract with reviewers.
- **One home per rule.** A rule lives in exactly one guide; other guides link
  to it. The alignment document's section table is the routing hub — new
  topics get a row there before guides start citing them.
- **Pair every pitfall with its detector** (clang-tidy check, sanitizer,
  review gate) when one exists. A rule nobody or nothing enforces gets either
  enforcement named or deleted.
- **Upkeep in place**: when an upstream rule ID moves, fix its citations
  during the next edit of the affected guide — no bulk sweeps
  (the Core Guidelines disposition,
  `specs/cpp/cpp/core-guidelines-disposition.md`).

---

## Sync Obligations

Adding, removing, renaming, or re-titling a guide file requires updating, in
the same change:

1. `specs/cpp/cpp/index.md` — Guidelines Index table **and** Pre-Development
   Checklist rows (both must cover every file).
2. `specs/cpp/README.md` — Guideline Files table and install-layout tree.
3. Any guide whose relative links pointed at the old path/name — links are
   repo-relative within `specs/cpp/`.
4. `specs/cpp/cpp/core-guidelines-disposition.md` — its disposition and
   residual-ledger tables route rules to guides by link; retarget those
   links when a guide is added, renamed, or re-titled.

Anti-patterns seen in template-driven repos, all rejected here: empty
headings kept "for later", aspirational rules the tooling cannot check,
duplicated rule text drifting between two guides, and tables whose rows no
longer match the file tree.

---

**Language**: All documentation should be written in **English**.
