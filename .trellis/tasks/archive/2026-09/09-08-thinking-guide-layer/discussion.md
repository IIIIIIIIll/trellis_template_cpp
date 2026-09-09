# Discussion: thinking-guide philosophy vs the stock Trellis layer

> Status: **RESOLVED** 2026-09-09 — developer decision recorded in the
> Resolution section below. No template change was made from this document.

## Context

Revision 2 of `specs/cpp/guides/index.md` shipped a curated method (procedure
spine + cue triggers + canonical failure anchors; see `design.md`). Reviewing
it against the stock thinking guides shipped by `trellis init`
(`@mindfoldhq/trellis/dist/templates/markdown/spec/guides/`) surfaced a real
philosophical divergence. Recorded here so the follow-up decision is made
with the full analysis in view.

## The divergence (evidence-backed)

### Axis 1 — where the content comes from

- **Stock: bottom-up incident scars.** The stock guides `index.md` instructs
  verbatim: "After bugs: Add new insights to the relevant guide (learn from
  mistakes)" and "Found a new 'didn't think of that' moment? Add it to the
  relevant guide." The residue is visible in the shipped files:
  `cross-layer-thinking-guide.md` contains three sections duplicated verbatim
  (Cross-Platform Template Consistency, Mode-Detection Probe Checklist, and
  Generated Runtime Template Upgrade Consistency each appear twice) —
  append-on-incident growth without curation. Its triggers reference
  Trellis's own JSONL/RPC/mode-probe bugs; the code-reuse guide's tail is
  Trellis-internal (rsync sync commands, `getAllScripts()` history, release
  version numbers).
- **Ours: top-down distillation.** 18 rows derived from the 539-rule corpus
  and its detector vocabulary; curated to one home per claim; governed by
  `.trellis/spec/registry/guideline-authoring.md`; versioned per
  `registry-contract.md` release discipline.

### Axis 2 — lifecycle

- **Stock:** starts (near-)empty, grows project-ward through lived incidents.
- **Ours:** starts project-independent; after install it is expected to
  diverge project-ward — locally edited files trigger the update "Modified by
  you" prompt rather than silent overwrite (hash/conflict flow, `USAGE.md`).
- Both converge on the same end state: a project-specific method grown from
  incidents. The template exists because a greenfield consumer has no scar
  tissue yet (`specs/cpp/cpp/index.md`, Adapting section: "so a new repository
  starts consistent instead of empty").

### Axis 3 — author of record

- **Stock:** the team living in the repo (its Contributing section).
- **Ours pre-install:** the template maintainer. **Post-install:** the
  consumer team.

## The gap (why this needs a decision)

The handover from "maintainer-written method" to "consumer-grown guide" is
undocumented. Nothing in the shipped guide tells the consumer that growing
their own incidents into it is the intended lifecycle. Failure mode: a
consumer treats the guide as a finished product, never appends scars, and the
layer freezes at genericity — exactly what the stock philosophy warns against
(our repo-local tombstone `.trellis/spec/guides/index.md`: "grow it from real
incidents rather than restoring generic templates").

## Options (for discussion)

| Option | Guidance lives in | Tradeoff |
|--------|-------------------|----------|
| A. Growth section in the guide (sketch below) | `specs/cpp/guides/index.md`, new short section | Seen at work time — injected with C++ file touches; costs ~10 lines of the 720-char injection headroom remaining (8,680 / 9,400) |
| B. Adaptation note in the template README | `specs/cpp/README.md` | Zero injection cost; but README is onboarding reading, not present mid-work |
| C. Consumer walkthrough note | `USAGE.md` | Adoption-time only; weakest at the moment of danger |
| D. Leave as-is | — | Guide stays a pure product; adaptation relies on the generic "Adapting These Guidelines" section in `cpp/index.md` |

### Option A sketch (not decided)

A short "Growing This Guide After Install" section:

1. This is the starting method, not the finished one.
2. After each real incident: add its signature to the matching row's failure
   column, or add a cue row.
3. Keep the invariants: incidents become cues/signatures; normative rules
   stay in the phase guides (one home per rule).
4. Local edits are safe — the update flow prompts instead of overwriting.

## Constraint for any growth model

The stock cross-layer guide's duplicated sections show what uncuration costs.
If incident-growth is adopted, the growth instructions should bind to the
authoring rules: no duplicate rows or sections, each incident lands as a
signature or cue deduplicated against existing rows. And `guides/` sits
outside `tools/check_snippets.py`'s DEFAULT_DIR, so the guide stays
code-free (Revision 2 decision) — incidents are recorded as prose, not
fences.

## Decision status

**Deferred.** Further discussion wanted before changing the template. When
decided, the outcome lands either in `specs/cpp/guides/index.md` (Option A),
`specs/cpp/README.md` (Option B), `USAGE.md` (Option C), or nowhere (D) — and
this document gets a resolution note.

---

## Resolution (2026-09-09, developer decision)

The growth framing was **rejected**. The thinking guide is a fixed,
project-independent, curated piece of engineering material whose job is to
guide the LLM along the engineering path. Its value comes from curation and
stability, not from local incident-append. It is a product, not a notebook —
and not a starting point that converges toward the stock layer's end state.

Consequences:

- **No template change.** The shipped guide makes no growth claims, and none
  are wanted. Options A–C are moot; the outcome is D, resolved by philosophy
  rather than by omission.
- **Author of record stays the template maintainer — permanently.** There is
  no maintainer→consumer handover to document. Improvements flow through the
  release channel (tagged releases; `trellis update`), never consumer-side
  scar accumulation. Consumers may still edit locally — the update flow
  prompts instead of overwriting — but that is mechanics, not lifecycle
  intent.
- **Project-independence is the feature.** Project specifics belong in the
  consumer's adapted `cpp/` layer; the thinking guide stays generic on
  purpose: a C++ engineering method, not project memory.
- Axis 2's "both converge on the same end state" claim is withdrawn — the
  notebook metaphor described only the stock layer.
