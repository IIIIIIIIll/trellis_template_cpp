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
`specs/cpp/cpp/core-guidelines-alignment.md`, `specs/cpp/cpp/index.md`.

1. `# Title` immediately followed by a one-paragraph `>` blockquote summary.
2. `## Overview` stating the guide's stance and scope — what it decides, not a
   table of contents restated.
3. Body organized by decision, using tables for mappings and **Wrong/Right**
   code pairs for rules.
4. Footer, exactly two lines: the `**Language**` note and the Core Guidelines
   attribution (see `specs/cpp/cpp/index.md` bottom). Every shipped doc
   carries both.

Wrong/Right pairs are the house style for any rule that can be shown in code.
The wrong example names what a reviewer would flag; the right example carries
the rule ID as a comment when one exists:

```cpp
// NOLINT                      ← Wrong: silenced with no trace of why
// Deviates from F.21: ...     ← Right: deviation travels with the code
```

Full examples: `specs/cpp/cpp/core-guidelines-alignment.md` ("Recording a
Deviation").

---

## Content Rules

- **Opinionated defaults, not surveys.** Guides pick a side and say why.
  Baseline is C++17; mention C++20/23 only where they change a
  recommendation (`specs/cpp/README.md` states this contract).
- **Core Guidelines citations are anchors, never copies.** Cite IDs like
  `F.21`, `ES.20`; write our own paraphrase. The Guidelines' prose and
  examples are never copied into this repository — license footer exists
  because of this rule.
- **Stance vocabulary is fixed**: *Adopt*, *Adapt*, *Covered elsewhere*
  (defined in `core-guidelines-alignment.md`). *Adapt* obligates a written,
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
  (`core-guidelines-alignment.md`, "Notes on upkeep").

---

## Sync Obligations

Adding, removing, renaming, or re-titling a guide file requires updating, in
the same change:

1. `specs/cpp/cpp/index.md` — Guidelines Index table **and** Pre-Development
   Checklist rows (both must cover every file).
2. `specs/cpp/README.md` — Guideline Files table and install-layout tree.
3. Any guide whose relative links pointed at the old path/name — links are
   repo-relative within `specs/cpp/`.

Anti-patterns seen in template-driven repos, all rejected here: empty
headings kept "for later", aspirational rules the tooling cannot check,
duplicated rule text drifting between two guides, and tables whose rows no
longer match the file tree.

---

**Language**: All documentation should be written in **English**.
