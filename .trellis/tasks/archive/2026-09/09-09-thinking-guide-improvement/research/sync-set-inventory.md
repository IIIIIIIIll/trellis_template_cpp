# Research: sync-set inventory for a guides-layer reshape

> Branch-independent (holds under every round-4 variant). Verified against
> `registry-contract.md`, `USAGE.md`, `index.json`, `specs/cpp/README.md`,
> `specs/cpp/cpp/index.md` on 2026-09-09.

## Manifest: no change needed

`index.json` pins one template entry: `id: cpp`, `path: specs/cpp`. The path
is the template ROOT — reshaping directories inside it does not touch the
manifest. Only a new top-level template would.

## Orphan-safety constraint (drives the cutover design)

`USAGE.md` (update section, lines 93–108): restructures install additively;
pure additions need no consumer cleanup; renames/moves orphan files on the
consumer side. The 09-08 phase-restructure is cited there as the precedent.

Therefore: **keep `guides/index.md` as the router path** (edited in place —
pristine consumers refresh silently; modified consumers get the "Modified by
you" prompt) and **add new files beside it**. Never rename the existing file
or move the layer. This makes the entire reshape orphan-free for consumers.

## The actual sync set (same change)

| File | Change | Needed when |
|------|--------|-------------|
| `guideline-authoring.md` | Rewrite Thinking-Guide Layer section: multi-file shape, per-file budget, fence policy, growth/Contributing sections, router responsibilities | Always (shape contract changes under every variant) |
| `specs/cpp/README.md` | Layout tree `guides/` section lists the new files; file-table section gains rows | Always (file set changes) |
| root `README.md` | Layout tree line for `guides/` if it enumerates files | If the tree enumerates guide files |
| `USAGE.md` | No change: pure-addition + in-place-edit behavior already documented | Only if a rename/move sneaks in |
| `index.json` | No change: `specs/cpp` root path unchanged | Only on new template roots |
| `specs/cpp/cpp/index.md` | Checklist row `Unsure which guide owns the risk…` → `../guides/index.md` keeps resolving (path kept) | No change |
| `.trellis/spec/registry/index.md` | "Four places listing the same file set" invariant — confirm README file table + cpp/index.md Guidelines Index + layout trees all cover the new set | Verify, likely no edit (Guidelines Index lists `cpp/` docs only; guides/ files live in README's own table) |

## Quality gates to re-run (registry index, unchanged set)

Manifest check, relative-link check across `specs/`, `validate_rules.py`,
extract+byte-compare, `check_snippets.py`. Guides-layer additions stay
outside DEFAULT_DIR under fence policy (α); under (β), `check_snippets.py`
DEFAULT_DIR + stubs gain `guides/` walks (tooling change). (β rejected —
see parent PRD decision 3.)
