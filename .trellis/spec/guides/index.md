# Thinking Guides

> Intentionally empty for this repository — by decision, not omission.

---

## Why There Are No Guides Here

This repository ships C++ guideline **markdown**; it contains no application
code. The stock Trellis thinking guides target code-shaped risks — data flow
across API/service/database layers, duplicated code patterns, shared
constants — none of which can occur in a docs-only spec registry.

The habits that do transfer live in the registry layer already:

| Habit | Home |
|-------|------|
| Search before changing any value or behavioral claim | [Registry Contract](../registry/registry-contract.md) |
| Keep cross-references and file tables in sync | [Guideline Authoring](../registry/guideline-authoring.md) |
| Structural checks before declaring work done | [Registry Guidelines](../registry/index.md) |

If a repo-specific thinking trigger emerges (a recurring class of doc drift,
a manifest mistake happening twice), record it in this file — grow it from
real incidents rather than restoring generic templates.

---

**Language**: All documentation should be written in **English**.
