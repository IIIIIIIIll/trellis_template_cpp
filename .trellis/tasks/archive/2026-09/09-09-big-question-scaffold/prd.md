# PRD (child 2): Ship big-question scar home for cpp template

> Parent: `09-09-thinking-guide-improvement`. Sequenced AFTER
> `09-09-thinking-guide-layer-reshape` (consumes its contract text; adds the
> router pointer line and the bug-root-cause guide link that child 1
> deliberately deferred to keep every merged state gate-green).

## Problem

Consumers of the cpp template have no designated place to record incident
lessons. Every trellis sibling project ships a growth path: Contributing
sections in the guides router plus a `big-question/` directory of
severity-indexed incident deep-dives with a documented contribution format.
The 2026-09-09 resolution rejected growth instructions in the *thinking
guide*; the parent decision set reverses that resolution in scoped form —
the scar home is where consumers grow, the method stays curated.

## Goal

Ship `specs/cpp/big-question/` as the template's third layer directory
(installs to the consumer's `.trellis/spec/big-question/`): severity index +
contribution format + 3 seeded incident narratives for canonical C++
incident classes, explicitly framed as format exemplars. Sync READMEs and
complete the deferred pointer/link edits in the same change.

## Requirements

### File set (4 files, all in `specs/cpp/big-question/`)

| File | Frontmatter | Role |
|------|-------------|------|
| `index.md` | YES (`description:` + shared C++ `paths:` glob; injected) | Severity levels, issue index, How to Contribute |
| `static-initialization-order.md` | NO (not injected; reached via index) | Exemplar incident: SIOF across TUs |
| `dangling-string-view.md` | NO | Exemplar incident: view outliving owner mutation |
| `optimization-ub.md` | NO | Exemplar incident: UB that survives `-O0` and breaks `-O2` |

### `index.md` — family format (derived from nextjs sibling, paraphrased)

1. Frontmatter + `# Common Issues and Solutions`-style title + intro
   blockquote: documented pitfalls for C++ projects built from this
   template's guideline corpus.
2. **Severity Levels** table: Critical (crash, corruption, UB in production)
   / Warning (degraded, workaround exists) / Info (minor, easy fix).
3. **Issue Index** table: `Issue | Category | Severity` — 3 rows for the
   seeds (Categories: Initialization & Linkage / Ownership & Lifetime /
   Undefined Behavior & Optimization).
4. **How to Contribute** — the growth format, numbered like the sibling:
   (1) new kebab-case `.md`; (2) follow the format: Problem → Root Cause →
   Solution → Key Takeaways; (3) update the index table with category +
   severity; (4) link the owning `cpp/` guide instead of duplicating its
   rules; compiled examples live in the `cpp/` docs, not here (zero ` ```cpp `
   fences — house fence policy).
5. Language-only footer.

### Incident file format (all three seeds)

`# <Title>` + blockquote (one-line incident signature) + sections:
**Problem** (the observable signature a developer/LLM would hit), **Root
Cause** (the mechanism, C++-precise), **Solution** (strategy + which guide's
rules prevent it), **Key Takeaways** (2–4 bullets), **Read first** links
into `../cpp/…`. Each file opens with one italic line: "Format exemplar for
a canonical C++ incident class — not project history." (no fabricated scar
tissue). Zero ` ```cpp ` fences: mechanism described in prose; compiled
BAD/GOOD pairs live one link away in the `cpp/` docs.

Seed ↔ cpp/ guide mapping (read-first links):

- `static-initialization-order.md` → `../cpp/implement/expressions-and-flow.md`
  (namespace-scope objects across TUs; SIOF rules) +
  `../cpp/design/headers-and-dependencies.md`.
- `dangling-string-view.md` → `../cpp/implement/memory-discipline.md`
  (stored-reference mutation-surface row) +
  `../cpp/implement/expressions-and-flow.md` (range-for extension).
- `optimization-ub.md` → `../cpp/implement/performance.md` +
  `../cpp/implement/expressions-and-flow.md` +
  `../cpp/verification/testing-conventions.md` (sanitizer gates).

### Deferred edits completed by THIS child (child 1 left gaps on purpose)

1. Router `specs/cpp/guides/index.md`: the Core Principles "Learn From
   Bugs" line gains the link `[big-question/](../big-question/index.md)`;
   the Available-Guides table or pointer section gains the one-line scar-home
   pointer.
2. `specs/cpp/guides/bug-root-cause-thinking-guide.md`: "Record the
   Incident" section gains the link to `../big-question/index.md`.

### Sync set

1. `specs/cpp/README.md`: layout tree gains `big-question/` section (4
   files, one-line roles); file table gains 4 rows; "What Installs Where"
   prose mentions the third layer directory.
2. Root `README.md`: layout tree line if it enumerates layer directories.
3. `USAGE.md` / `index.json`: no change (additive install; manifest pins
   `specs/cpp` root; layer discovery picks up `big-question/` the same way
   it picks up `guides/`).
4. Contract: already rewritten by child 1 to govern `big-question/` —
   verify it matches what lands; fix drift inside this change if found.

## Acceptance criteria

- All parent cross-child criteria hold on the UNION (gates, links, sync,
  zero ` ```cpp `).
- `index.md` ≤ 9 KB with frontmatter; the 3 incident files have NO
  frontmatter (grep-verified) and carry the exemplar-disclosure line.
- Relative-link check passes with the router pointer and bug-root-cause
  link present.
- Incident narratives: each has Problem / Root Cause / Solution / Key
  Takeaways + read-first links resolving in-repo and post-install.
- `git status` touches only: `specs/cpp/big-question/**` (4 files),
  `specs/cpp/guides/index.md`, `specs/cpp/guides/bug-root-cause-thinking-guide.md`,
  `specs/cpp/README.md`, root `README.md`.
  Exception: `.trellis/spec/registry/guideline-authoring.md` may be touched
  ONLY to fix contract drift between child 1's rewrite and what lands — any
  such fix must be called out in the report.

---

## Addendum (2026-09-10)

Post-implementation review of child 1 surfaced two repo-internal drift items
that child 2 absorbs, beyond the original sync set:

1. `.trellis/spec/registry/index.md` — child 1 redefined the layer to span
   `specs/cpp/guides/` **and** `specs/cpp/big-question/`, which made this
   registry spec's product table (and the tombstone parenthetical) stale; its
   Quality Check section also gains the layer's gate scope note (outside
   validator walks; the `EXEMPT_DOCS` basename trap under
   `validate_rules.py --path`).
2. `.trellis/spec/registry/guideline-authoring.md` — beyond drift repair, one
   sentence records the layer's recipe convention
   (`rg -g '*.{cpp,cc,cxx,hpp,hh,h,inl,ipp}'`, not `--type cpp`, which omits
   `*.ipp`) discovered by review; the deferred-pointer sentence moves to
   present tense now that the pointers land in this same change.

Both are called out in the change report; `git status` therefore also lists
`.trellis/spec/registry/index.md` (accepted deviation from the list below).

---

**Language**: All documentation should be written in **English**.
