# PRD: Exception cost-model notes in error-handling and performance guides

## Background

Review of `specs/cpp/cpp/error-handling.md` found the error-signaling taxonomy
implicitly encodes the performance-critical decisions (anticipated failures are
values, rare failures throw), but no document states the exception cost model,
and `performance.md` has no exception-cost content beyond the noexcept-move
cross-link. User decision (2026-09-02): **minimal option** — cost-model note
only, no new rule IDs.

## Requirements

1. `specs/cpp/cpp/error-handling.md`, ERR-7 block: add a 1-3 sentence rationale
   paragraph stating the cost shape — non-throwing path effectively free under
   table-driven unwinding; a thrown exception typically costs three to four
   orders of magnitude more than a status check; link to
   `./performance.md` for the measurement discipline.
2. `specs/cpp/cpp/performance.md`, Allocation Hygiene section after PERF-14:
   add one rationale sentence pointing at `ERR-7` as the owning rule. The
   sentence carries cost rationale only — no restated rule text
   ("one home per rule" anti-pattern).

## Constraints

- No new rule IDs, no rule strength/detector changes.
- No file add/rename/retitle → no `index.md` / `README.md` / disposition sync.
- Authoring spec (`.trellis/spec/registry/guideline-authoring.md`) governs:
  rationale 1-3 sentences, repo-relative links, rule text stays in one guide.
- If `tools/extract_rules.py` output changes (rationale absorbed into
  `statement`), the regenerated digest ships in the same change.

## Acceptance criteria

- [ ] Both edits are prose-only; no fence, rule ID, or table changes.
- [ ] `python3 tools/extract_rules.py` re-run; `rules.json` matches output.
- [ ] `python3 tools/validate_rules.py` → 0 violations.
- [ ] `python3 tools/check_snippets.py --path specs/cpp/cpp/error-handling.md` → 0 violations.
- [ ] Changes committed.
