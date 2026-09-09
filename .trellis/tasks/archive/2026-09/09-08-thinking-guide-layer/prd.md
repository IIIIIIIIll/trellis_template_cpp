# PRD: Thinking-guide layer in the cpp template

## Problem

The cpp template ships fourteen topic guides plus phase routers, all routed by
**task type** (the Pre-Development Checklist in `specs/cpp/cpp/index.md`).
Nothing ships the *cross-cutting risk questions* — the triggers whose owning
guide is not the obvious one from the task description. Stock `trellis init`
normally provides a generic `guides/` layer; consumers of this template get
nothing there.

## Goal

Ship `specs/cpp/guides/index.md` — a C++-specific thinking guide installing to
the consumer's `.trellis/spec/guides/` — as a second layer directory of the
template root `specs/cpp/`.

## Non-goals

- No content changes to the fourteen topic guides; no `rules.json` regen.
- No new rule blocks anywhere. The `tools/` validators stay bound to
  `specs/cpp/cpp/` only — that scope must not change.
- No change to the repo-local `.trellis/spec/guides/index.md` tombstone (its
  rationale is repo-specific and unaffected by template content).
- No `index.json` change — the manifest pins `specs/cpp`, not layers.

## Design (fixed decisions)

1. **Single file**: `specs/cpp/guides/index.md`. No subdirectory split, no
   placeholder headings. A future split is a consumer-visible move (orphan
   cleanup), so start minimal.
2. **Frontmatter required** (spec_match.py injects on `paths:`; no frontmatter,
   no injection):
   - `description:` one line.
   - `paths:` the shared C++ glob list exactly as the other guides carry it:
     `**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp`.
3. **No normative rule blocks**: triggers are questions routing into the phase
   guides, never `**ID-n (strength).**` blocks. One home per rule is preserved.
4. **Structure** per guideline-authoring.md Document Shape: `# Title` +
   one-paragraph blockquote; `## Overview` stating stance and scope; body
   organized by decision; footer `**Language**` line (Language-only matches
   the in-repo guides-layer precedent; no Core Guidelines attribution needed —
   this guide cites no CG text).
5. **Distinct value vs the existing checklist** (must not duplicate it):
   `cpp/index.md` routes by task type; this guide poses *risk-shaped* questions
   that fire when the task row is not obvious, plus interactions no single
   guide owns. The Overview must state this relationship explicitly.

## Required content substance

Trigger tables organized by the three phases, then a cross-cutting section.
Each row: trigger question → owning guide link(s). Minimum substance:

**Design**

- Who owns this at every point of its lifetime, and who can destroy it?
  → Ownership Design; body-side rules in Memory Discipline.
- What invariant must hold after construction and after every public call —
  and who re-establishes it when an operation fails mid-way?
  → Classes and Hierarchies; failure semantics in Error Contracts.
- Can any other call invalidate this parameter/return value while the caller
  still holds it? → Functions and Interfaces; Ownership Design.
- Does this failure mode have a representation in the signature, or only in a
  comment? → Error Contracts.
- Is this template needed or speculative; are its type requirements checked at
  the interface? → Templates and Generics.
- What does this header cost every translation unit that includes it, and does
  this type's layout leak into ABI? → Headers and Dependencies.

**Implementation**

- What allocates here, in which loop, and who frees it?
  → Memory Discipline; measurement gates in Performance.
- What is the evaluation order of this expression, and which implicit
  conversions fire? → Expressions and Flow.
- What state do two threads touch, and which lock makes the invariant hold?
  → Concurrency.
- Does the error path leak, double-free, or swallow?
  → Error Propagation; Memory Discipline.
- Does the name promise what the body does? → Naming and Constants.

**Verification**

- Which detector is supposed to catch the mistake this code invites?
  → Static Analysis.
- What test would fail if this broke — and does the design make writing it
  possible? → Testing Conventions.

**Cross-cutting interactions** (no single guide owns; state explicitly that
these spans are why the trigger layer exists)

- Ownership × concurrency: freeing on another thread; lock lifetime vs object
  lifetime. → Concurrency + Ownership Design + Memory Discipline.
- Exceptions × templates: a generic's failure contract instantiates at every
  use site. → Error Contracts + Templates and Generics.
- Performance × correctness: UB that happens to be fast (uninitialized reads,
  dangling references that "work"). → Performance + Expressions and Flow +
  Memory Discipline.
- Headers × evolution: changing a header recompiles the world; changing layout
  breaks binaries. → Headers and Dependencies.

All guide links are repo-relative `../cpp/<phase>/<doc>.md` — they must resolve
both in-repo (`specs/cpp/guides/` → `specs/cpp/cpp/…`) and post-install
(`.trellis/spec/guides/` → `.trellis/spec/cpp/…`).

## Sync obligations (same change)

1. `specs/cpp/README.md` — layout tree gains `guides/`; a Thinking Guides
   table section after Verification; the "What Installs Where" prose now
   describes two layer directories (`cpp/` and `guides/`).
2. Root `README.md` — Layout tree gains `guides/` under `specs/cpp/`; the
   layer sentence mentions both layers. The "nineteen documents" count for
   `cpp/` itself is unchanged (guides/ is a separate layer).
3. `USAGE.md` — "Staying Updated" section: one sentence noting new layers and
   files install additively (nothing to clean up for pure additions; orphan
   cleanup concerns renames/moves only).
4. `specs/cpp/cpp/index.md` — Pre-Development Checklist gains one row routing
   "unsure which guide owns the risk / task spans several" to
   [Thinking Guides](../guides/index.md). Nothing else in cpp/index.md
   changes.

## Acceptance criteria

- `specs/cpp/guides/index.md` exists with the required frontmatter, structure,
  and content substance above; zero `**ID-n**` rule blocks; Language footer.
- All four sync edits applied in the same change; every relative link in
  `specs/` resolves.
- Gates green (run from repo root per `.trellis/spec/registry/index.md`):
  manifest check, relative-link check, `tools/validate_rules.py`,
  `tools/extract_rules.py` twice + byte-compare, `tools/check_snippets.py`.
- `git status` shows changes only in: `specs/cpp/guides/` (new),
  `specs/cpp/README.md`, `README.md`, `USAGE.md`, `specs/cpp/cpp/index.md`.

## Risks

- Duplication with the Pre-Development Checklist — mitigated by the Overview
  framing and trigger (question) vs task-row (category) distinction.
- Silent validator blindness on file-set change — not applicable: `guides/`
  is outside `DEFAULT_DIR`, and no DOC_PREFIX map entry is added.
- Consumer update flow: pure addition → installs additively, no orphans.
