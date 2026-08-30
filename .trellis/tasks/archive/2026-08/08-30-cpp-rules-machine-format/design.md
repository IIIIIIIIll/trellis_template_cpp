# Design — Machine-Consumable Rule Structure

## Rule-block grammar (markdown-native)

A **rule** is one discrete block; a rule never spans sections or mingles with
another rule's text.

```markdown
**MEM-7 (hard).** Never call `new`/`delete` for owning a single object; take
RAII ownership in one step.

<optional rationale, 1-3 sentences>

```cpp
// Wrong: ...
// Right: ...
```

Caught by: `cppcoreguidelines-pro-type-cstyle-cast` (or: Caught by: review —
no automated detector).
```

- Lead-in format: `**<AREA>-<n> (<strength>).**` — one greppable token
  serving citation (IDs), triage (strength), and extraction (position).
  Every rule — including rules whose substance is a Core Guidelines rule —
  is identified by its local ID; Core Guidelines IDs stay in the text as
  cross-reference anchors only (developer decision 2026-08-30, resolving
  PlanCheck A1 in favor of unified local IDs).
- `<strength>` ∈ {`hard`, `default`}: hard = violation requires a deviation
  comment (rule ID + reason + what would change the answer, per the existing
  convention); default = a measurement-backed local deviation is allowed
  without ceremony.
- `Caught by:` reuses the existing detector-pairing phrase; a rule with no
  detector states `Caught by: review — no automated detector.` explicitly.
- Example fences carry `// Wrong:` / `// Right:` comments; Wrong examples that
  compile but are runtime-UB carry `// compiles; UB at runtime`.

## ID allocation

| Doc | Prefix | Doc | Prefix |
|-----|--------|-----|--------|
| memory-and-ownership | `MEM-` | classes-and-hierarchies | `CLS-` |
| error-handling | `ERR-` | templates-and-generics | `TPL-` |
| quality-guidelines | `QUAL-` | concurrency | `CONC-` |
| testing-conventions | `TEST-` | expressions-and-flow | `EXPR-` |
| functions-and-interfaces | `FN-` | performance | `PERF-` |

- Numbering is **stable and append-only**: retired rules leave gaps, never
  renumber. Mirrors upstream's own practice.
- Every rule gets a local `AREA-n` ID, including rules whose substance is a
  Core Guidelines rule; the CG ID stays in the text as the cross-reference
  anchor. The validator accepts only local-ID lead-ins.
- Tables: a row carrying a normative claim puts `**<ID>**` in its first cell;
  the strength comes from the enclosing section's stated default unless the
  cell also marks it. (Tables stay matrices; the block grammar governs prose
  rules.)

### Grammar details (PlanCheck A2, from the disk survey)

- **Wrong/Right encodings on disk** — all three are valid; pairing is judged
  per rule block (exactly one Wrong and one Right per example group):
  1. one fence holding both, split by `// Wrong:` / `// Right:` comments;
  2. two fences, each opening with its comment;
  3. two fences under prose lead lines (`**Wrong**` / `**Right**`).
- **List-item form**: a rule may be a bullet item (`- **MEM-7 (hard).** ...`);
  the lead-in grammar is identical after the `- `.
- **Table-cell format**: first cell begins `**<ID>**` and may append
  `(hard)`/`(default)`; unmarked cells inherit the section default.
- **Strength fallback**: strength comes from the cell or block marker, else
  the section's stated default; if neither exists the validator flags the
  rule (no silent defaulting).
- **Caught-by inheritance**: a rule without its own `Caught by:` line
  inherits the nearest preceding one within the same section; a
  section-level `Caught by:` covers every rule below it that lacks its own.
- **Validator scope**: binds the 10 topic guides; `index.md` and
  `core-guidelines-disposition.md` are exempt (disposition rows are stances,
  not rules).

## Index split

- New file: `specs/cpp/cpp/core-guidelines-disposition.md` — receives the
  Core Guidelines Disposition section body: disposition-by-section table,
  residual ledger, "Recording a Deviation" example, Adoption Process, Upkeep,
  Profiles. Footer contract applies (Language + attribution).
- `index.md` keeps: Overview, Guidelines Index (+1 row for the new doc),
  Adapting These Guidelines, stance-vocabulary table (4 rows — needed whenever
  a session reads a deviation note), Pre-Development Checklist, Quality Check,
  footer. Target: index drops to ≤120 lines.
- Sync points to update in the same change: `specs/cpp/cpp/index.md` index
  table, `specs/cpp/README.md` table + tree, top-level `README.md` tree
  (eleven → twelve documents), plus the PlanCheck A3 retargets:
  `.trellis/spec/registry/index.md` lines 22 and 51 (11→12 counts and framing
  sentence), `guideline-authoring.md` lines 37 and 62 (section-reference
  retarget to the new doc) and lines 26-27 (Wrong/Right ID-comment clause for
  the lead-in encoding), `functions-and-interfaces.md` line 387
  (deviation-policy link retarget), and inside the moved body the Profiles
  "Quality Check below" and Adoption-Process "This index" self-references
  (reword to name the owning document explicitly).

## Generated digest

`tools/extract_rules.py` parses the rule grammar and emits `rules.json`:

```json
{ "id": "MEM-7", "strength": "hard",
  "statement": "Never call new/delete ...",
  "doc": "memory-and-ownership.md",
  "detector": "cppcoreguidelines-pro-type-cstyle-cast | review",
  "upstream": ["R.11"] }
```

- `upstream` lists the Core Guidelines IDs the rule's text cites; for a rule
  whose substance is a CG rule, that is its own CG ID.
- No `anchor` field (PlanCheck A4): rules are paragraph lead-ins, not
  headings — promoting every rule to a heading to manufacture anchors would
  distort document shape. Digest consumers locate a rule by `doc` + ID grep.
- Regeneration is deterministic; the file is committed but never hand-edited.
- Session usage: inject `rules.json` (a few hundred lines) for routing,
  load the full doc on demand. Satisfies cheap-routing without duplicating
  rule text — the digest is derived, so one-home-per-rule holds.

## Snippet harness

`tools/check_snippets.py`:

1. Extract fenced ```cpp blocks with their doc + line + preceding prose hint.
2. Prepend a stub header (`tools/stubs/stubs.hpp`) declaring the invented
   types each doc uses (Window, Poller, FileDesc, Task/Model, ...). Stubs are
   ordinary code, compiled once per doc run.
3. Compile `g++ -std=c++17 -Wall -Wextra -fsyntax-only` per block:
   - Right blocks and unmarked blocks: must compile clean.
   - Wrong blocks annotated `// compile-error`: must fail, and the primary
     diagnostic must reference the annotated line region.
   - Wrong blocks annotated `// compiles; UB at runtime`: must compile (the
     UB is runtime-only); deeper runtime checks stay out of scope for the
     gate (the 08-30 editorial pass demonstrated ASan/UBSan spot checks; the
     gate keeps them as manual verification, not CI).
4. Exit nonzero with a per-block report on any violation; wired into the
   registry `index.md` Quality Check.

Tradeoff accepted: `-fsyntax-only` will not catch runtime-only example rot
(the class this round's range-for bug fell into — it compiled). Mitigation:
runtime-hazard examples are the reviewer's spot-check list; the harness
reports them as a distinct "compiles; UB at runtime" inventory so review
passes know which examples deserve manual sanitizer runs.

## Validator

`tools/validate_rules.py` — repo gate over the grammar:

- Every rule lead-in matches `**<AREA>-<n> (hard|default).**`; prefixes match
  the allocation table; IDs unique repo-wide.
- Every rule has a `Caught by:` line (or table-cell detector) or the explicit
  no-detector statement.
- Every `// Wrong:` has a `// Right:` sibling within the same fence-pair group.
- Strength vocabulary closed; footer contract per doc; relative links resolve
  (absorbs the existing registry link gate).
- Non-normative prose (rationale, examples, tables without claims) needs no
  marking — the validator only demands IDs where a claim block is detected.

Risk noted: "what counts as a normative claim" is judgment at conversion time.
The converter pass (implementers) marks everything they judge normative; the
validator then guarantees consistency, and future additions must follow the
grammar to pass the gate.
