# Implement (child 2): big-question scar home

> Run AFTER child 1's reshape lands. Dispatch prompt prefix:
> `Active task: .trellis/tasks/09-09-big-question-scaffold`.

## Step 1 — Layer files

- [ ] `specs/cpp/big-question/index.md`: frontmatter (description + shared
      C++ glob), severity table, issue index (3 rows), How to Contribute
      (4 steps; zero-fence + link-don't-duplicate rules stated), Language
      footer. ≤ 9,000 B.
- [ ] 3 incident files per `design.md` briefs: exemplar-disclosure line,
      Problem / Root Cause / Solution / Key Takeaways, read-first links.
      NO frontmatter (verify with grep).

## Step 2 — Deferred edits into child 1's files

- [ ] `guides/index.md`: scar-home pointer (table row or section) + Core
      Principles link. Re-check ≤ 9,000 B.
- [ ] `guides/bug-root-cause-thinking-guide.md`: link in "Record the
      Incident". Re-check ≤ 9,000 B.

## Step 3 — README syncs

- [ ] `specs/cpp/README.md`: layout tree `big-question/` section, file
      table rows (4), install prose (three layers).
- [ ] Root `README.md`: enumeration line if present.

## Step 4 — Gates (full suite, union of both children)

- [ ] Manifest check; relative-link check across `specs/` (now includes
      big-question links); `validate_rules.py`; extract+compare;
      `check_snippets.py`.
- [ ] `grep -c '```cpp' specs/cpp/big-question/ specs/cpp/guides/` → 0.
- [ ] Frontmatter-absence check on incident files.
- [ ] Citation invariant + row-survival spot check (19 rows).

## Step 5 — Report

- File sizes, gate outputs, sync diff; hand to parent integration review.

## Non-goals

- No `cpp/` guide edits. No harness changes. No new rule blocks. No
  frontmatter on incident files. No fabricated incidents beyond the three
  canonical exemplars.
