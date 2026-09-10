# Implement (child 1): Reshape cpp thinking-guide layer

> Ordered checklist. Validation after each block; full gate suite at the
> end. Active task line required on every dispatch:
> `Active task: .trellis/tasks/09-09-thinking-guide-layer-reshape`.

## Step 1 — Contract rewrite (do first: files must land inside a true contract)

- [ ] Rewrite `Thinking-Guide Layer` section of
      `.trellis/spec/registry/guideline-authoring.md` per `design.md`
      §Contract rewrite spec (6 bullets + sync-obligation addition).
- [ ] Verify: no other section of the spec contradicts the new shape
      (Document Shape §0–§4 applies to `specs/cpp/cpp/` docs — confirm its
      wording does not accidentally govern `guides/` files; adjust the
      scoping sentence if needed).

## Step 2 — Router (`specs/cpp/guides/index.md`, in place)

- [ ] Rewrite per `design.md` §Router skeleton; keep frontmatter paths;
      cross-cutting spans table verbatim; NO router pointer to
      `../big-question/index.md` (lands with child 2 — keep current
      file's absence of it; Core Principles "Learn From Bugs" names
      big-question in prose WITHOUT a link until child 2 exists).
- [ ] Size check: `wc -c` ≤ 9,000.
- [ ] Hand review: trigger bullets symptom-phrased; no duplication with
      `specs/cpp/cpp/index.md` Pre-Development Checklist rows.

## Step 3 — Phase guides ×3

- [ ] `design-thinking-guide.md`: 6 rows (5 carried + restored row: cue
      verbatim "Can any other call invalidate this parameter/return value
      while the caller still holds it?"; canonical failure
      "use-after-invalidation the compiler does not flag"; citing
      functions-and-interfaces.md + ownership-design.md).
- [ ] `implementation-thinking-guide.md`: 6 rows carried verbatim.
- [ ] `verification-thinking-guide.md`: 3 rows carried verbatim.
- [ ] Each: Why This Phase prose + procedure table + Before-Leaving
      checklist + frontmatter + Language footer.
- [ ] Size checks: each ≤ 9,000 B.

## Step 4 — Family-standard guides ×3

- [ ] Each file: frontmatter (`description:` + shared C++ `paths:` globs)
      + Language-only footer.
- [ ] `pre-implementation-checklist.md` (rg fences use POST-INSTALL paths).
- [ ] `code-reuse-thinking-guide.md`.
- [ ] `bug-root-cause-thinking-guide.md` (NO link to big-question/ — prose
      pointer only until child 2 lands; then child 2 adds the link).
- [ ] Size checks ≤ 9,000 B each.

## Step 5 — README syncs

- [ ] `specs/cpp/README.md`: layout tree `guides/` section lists 7 files
      with one-line roles; Thinking Guides file table gains 6 rows.
- [ ] Root `README.md`: layout tree `guides/` line updated if it enumerates
      (currently non-enumerating — expect no diff; verify).
- [ ] Confirm `USAGE.md` and `index.json` need NO change (additive +
      in-place; manifest pins root).

## Step 6 — Gates (from repo root, per `.trellis/spec/registry/index.md`)

- [ ] Manifest path check (python one-liner in the layer index).
- [ ] Relative-link check across `specs/` (python heredoc in the layer
      index). Must pass WITHOUT big-question (child 1 adds no pointer).
- [ ] `python3 tools/validate_rules.py` (checked-doc count == file count).
- [ ] `tools/extract_rules.py` twice + byte-compare.
- [ ] `python3 tools/check_snippets.py`.
- [ ] `grep -c '```cpp' specs/cpp/guides/` → 0 for every file.
- [ ] Citation invariant: every `../cpp/<phase>/<doc>.md` of the 14 guides
      appears in ≥ 1 layer file.

## Step 7 — Review + handoff

- [ ] Self-review diff against PRD acceptance criteria.
- [ ] Report: file sizes, gate outputs, sync-set diff.
- Rollback point: single commit `git reset --hard` to pre-task state.

## Non-goals (enforced)

- No `specs/cpp/cpp/**` edits. No `index.json`/`USAGE.md` edits. No
  `check_snippets.py` changes. No rule blocks. No `big-question/` files
  (child 2).
