---
description: Manifest schema, marketplace behavior, install mapping, and cross-doc consistency duties for registry plumbing
paths: [index.json, README.md, USAGE.md, HOSTING.md]
---

# Registry Contract

> Rules for `index.json`, the directory layout it points at, and keeping
> `README.md` / `USAGE.md` / `HOSTING.md` truthful about behavior.

---

## Manifest Contract

`index.json` at the repo root is what makes this a **marketplace-mode**
registry. Current shape (see `index.json`):

```json
{
  "version": 1,
  "templates": [
    { "id": "cpp", "type": "spec", "name": "...", "description": "...",
      "path": "specs/cpp", "tags": ["cpp", "c++", "native"] }
  ]
}
```

Rules:

- Every `templates[].path` MUST exist in the tree and point at a template root
  — a directory containing one or more layer directories plus an optional
  `README.md`. This is also the first check `HOSTING.md` prescribes for CI;
  no CI workflow exists in this repository yet, so run it manually (command
  in [the layer index](./index.md)).
- Template roots ship a stray `README.md` on purpose: layer discovery ignores
  it, so documentation travels with the template (`HOSTING.md`, Install
  Mapping).
- Marketplace mode is load-bearing behavior: its presence forces scripted
  consumers to pass `--template cpp`; without it `trellis init -y` fails with
  `Registry is a marketplace with multiple templates.` (`USAGE.md`,
  Troubleshooting). Never "simplify" the registry by deleting `index.json`.
- New template = new `specs/<id>/` root + an `index.json` entry with a unique
  id, plus updates to `README.md`'s Layout tree. Descriptions in the manifest
  sell the template in the picker — keep them accurate when scope changes.

---

## Behavior Claims Must Match Reality

The three root docs make concrete behavioral claims that go stale silently:

| Doc | Claims it owns |
|-----|----------------|
| `README.md` | Repository layout tree; quickstart command shapes |
| `USAGE.md` | Consumer flows: adopt, pick, update; troubleshooting table symptoms/causes |
| `HOSTING.md` | Source-string grammar, raw-URL patterns per provider, mode detection, install mapping, update lifecycle, versioning |

When changing anything these describe — moving directories, adding templates,
rewording error strings we quote — update every doc that quotes the old
behavior in the same change. Cross-links between the three docs and
`specs/cpp/README.md` are relative and must keep resolving.

`HOSTING.md` ends with a table mapping documented behavior to Trellis CLI
implementation paths (`packages/cli/src/...`). Those paths live in the
upstream Trellis repository, not here; treat them as external references for
traceability, not files to find in this tree.

---

## Update Lifecycle Assumptions

Consumers persist adoption as `registry.spec.source` + `template: <id>` in
their `.trellis/config.yaml`, then reconcile on `trellis update` through a
hash/conflict flow against their `.trellis/.template-hashes.json`: pristine
files refresh silently, locally edited files prompt. Consequences for us:

- File identity matters: renaming or moving files inside a template root
  changes what consumers receive on update (new paths added, old ones left
  orphaned on their side). Prefer editing in place over reshuffles; when a
  move is warranted, call it out in `USAGE.md`.
- Release discipline: tag per guideline release; consumers pin via `#ref`
  (`HOSTING.md`, Versioning). Floating `main` auto-freshens downstream —
  never push half-finished guideline edits to the default branch expecting
  invisibility.

---

**Language**: All documentation should be written in **English**.
