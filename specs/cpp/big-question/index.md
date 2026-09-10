---
description: Big-question incident deep-dives for C++ — severity-indexed exemplars and the consumer growth format
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Common Issues and Solutions

> Documented pitfalls of this template's C++ guideline corpus — canonical
> failure classes written up as Problem / Root Cause / Solution / Key
> Takeaways, with the owning guide linked instead of duplicated.

The seeded entries are **format exemplars, not project history**: each is a
canonical C++ incident class drawn from the failure vocabulary the topic
guides already define. Read an entry before fixing a bug whose signature
matches its row; add an entry when your project meets a class the corpus
did not cover. The [thinking guides](../guides/index.md) route by symptom
into the method — this directory is where the incidents themselves
accumulate, and it is the only writable half of the layer.

---

## Severity Levels

| Severity | Meaning |
|----------|---------|
| **Critical** | Crash, data corruption, or undefined behavior reachable in production |
| **Warning** | Degraded behavior or a latent trap; a workaround exists |
| **Info** | Minor issue, easy to fix, no production consequence |

---

## Issue Index

| Issue | Category | Severity |
|-------|----------|----------|
| [Static initialization order fiasco](./static-initialization-order.md) — one global reads another before it exists | Initialization & Linkage | Critical |
| [Dangling view after owner mutation](./dangling-string-view.md) — a stored `string_view`/reference outlives the container it views | Ownership & Lifetime | Critical |
| [Optimization-only undefined behavior](./optimization-ub.md) — works at `-O0`, misbehaves at `-O2` | Undefined Behavior & Optimization | Critical |

The seeds are all Critical by design: each is a canonical class from the
guide corpus's failure vocabulary, where the canonical consequence is a
crash, corruption, or undefined behavior. The column records the
consequence, not the frequency.

---

## How to Contribute

1. **Create one file per incident** — kebab-case `.md`, named for the
   failure mode, next to this index.
2. **Follow the incident format** — `# Title`, a one-line blockquote
   signature, then `## Problem`, `## Root Cause`, `## Solution`,
   `## Key Takeaways`, and `## Read first`.
3. **Add the index row** — issue, category, and severity in the table
   above, re-checked against the severity definitions.
4. **Link, do not duplicate** — the owning `cpp/` guide carries the rules
   and the compiled Wrong/Right examples; the incident states mechanism and
   strategy and links out to it.

Incident files carry **no frontmatter**: they are not injected, and this
index is their entry point. No fenced C++ blocks appear anywhere in this
directory — the mechanism is prose, and the examples live one link away in
the `cpp/` guides; bash command recipes are the only legal fences.

---

**Language**: All documentation should be written in **English**.
