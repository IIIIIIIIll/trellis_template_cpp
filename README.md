# Trellis Spec Registry: C++ Guidelines

> A self-hosted Trellis spec-template registry shipping project-independent
> C++ coding guidelines, consumable with
> `trellis init --registry gh:<owner>/trellis-specs --template cpp`.

---

## What This Is

Trellis projects normally get their `.trellis/spec/` guidelines scaffolded as
blank files to fill in. This repository instead hosts a ready-made, opinionated
C++ guideline set that any Trellis consumer can install and keep synchronized
from a central place.

It is laid out as a **marketplace-style registry**: an `index.json` manifest at
the root lists one or more templates, and each template lives in its own
subdirectory. `trellis init --registry <source>` probes the manifest, lets you
pick a template, and copies its contents into the consuming project's
`.trellis/spec/`.

---

## Layout

```
drafts/cpp-spec-registry/
├── index.json                 ← registry manifest (template id, type, path)
├── README.md                  ← this file
├── HOSTING.md                 ← ops deep-dive: source strings, modes, updates
└── specs/cpp/
    ├── README.md              ← template overview for consumers
    └── cpp/                   ← the guideline layer itself
        └── *.md               ← six guideline documents
```

The template's layer directory (`cpp/`) becomes `.trellis/spec/cpp/` after
install; layer discovery picks it up automatically.

---

## Quickstart

1. **Publish** — push this directory (or its contents) as a standalone GitHub
   repository, e.g. `<owner>/trellis-specs`. The repo root must contain
   `index.json`.
2. **Consume** — in any Trellis project:

   ```
   trellis init --registry gh:<owner>/trellis-specs --template cpp
   ```

   The guidelines install into `.trellis/spec/cpp/`, and adoption is recorded
   in `.trellis/config.yaml` so later refreshes know where to sync from.
3. **Update** — in existing projects that adopted this template:

   ```
   trellis update
   ```

   Re-fetches the template and applies changes through the normal
   hash/conflict flow — locally edited files are never silently overwritten.

---

## More

Hosting mechanics, source string anatomy, private-repo access, version
pinning, and CI validation of this registry are covered in
[HOSTING.md](./HOSTING.md). Template contents and install layout are described
in [specs/cpp/README.md](./specs/cpp/README.md).
