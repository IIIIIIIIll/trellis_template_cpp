---
name: Registry Guidelines
description: Working rules for this repository - a Trellis spec-template registry shipping C++ guidelines
---

# Registry Guidelines

> How to work in this repository: a marketplace-style Trellis spec-template
> registry whose product is markdown, not code.

---

## What This Repository Is

This repo hosts installable Trellis spec templates. It contains **no
application code**: no compiler, no build system, no tests, no runtime. The
work products are:

| Path | Role |
|------|------|
| `index.json` | Registry manifest; makes this a marketplace-mode registry |
| `specs/cpp/cpp/*.md` | The product: 12 C++ guideline documents installed into consumer projects |
| `specs/cpp/README.md` | Template overview shipped alongside the layer |
| `README.md`, `USAGE.md`, `HOSTING.md` | Registry-level docs: publish, consume, host |

Consumers run `trellis init --registry gh:<owner>/trellis-specs --template cpp`
and the `cpp/` layer lands as `.trellis/spec/cpp/` in their project. Mechanics:
`HOSTING.md`; consumer walkthrough: `USAGE.md`.

**Why there is no `cpp` layer here**: `.trellis/spec/cpp/` is the path a
consumer gets after installing this template. Installing our own template into
our own repo would collide with that name and buy nothing — editing guideline
markdown does not need those guidelines injected as context. Specs in this
directory instead describe *authoring and maintaining* the registry.

The former `backend/` / `frontend/` scaffold layers from `trellis init` were
removed: they assumed an application codebase this repository does not have.
The generic thinking-guide layer (`.trellis/spec/guides/`) is kept as a
deliberate tombstone: its triggers assume application layers this repository
does not have, so the transferable habits live in these two guides and that
index explains why nothing else belongs there.

---

## Pre-Development Checklist

Before changing files, route through the matching guide:

| Task involves | Read first |
|---------------|------------|
| Editing any file under `specs/cpp/**` (the 12 guideline docs or their README) | [Guideline Authoring](./guideline-authoring.md) |
| Adding or renaming guideline documents, changing doc structure or tone | [Guideline Authoring](./guideline-authoring.md) |
| `index.json`, adding/removing a template entry, moving directories | [Registry Contract](./registry-contract.md) |
| `README.md`, `USAGE.md`, `HOSTING.md`, install/update behavior claims | [Registry Contract](./registry-contract.md) |

A change that moves or renames guideline files almost always touches both
guides: the authoring guide owns the content links, the contract guide owns
the manifest, install mapping, and registry docs.

---

## Quality Check

No compiler or test suite exists here; verification is structural. Run before
declaring any change complete:

```bash
# Manifest is valid JSON and every templates[].path exists in the tree
python3 -c "import json; d=json.load(open('index.json')); import os; missing=[t['path'] for t in d['templates'] if not os.path.isdir(t['path'])]; print('missing:', missing) or exit(bool(missing))"

# Every relative markdown link inside specs/ resolves to a real file
python3 - <<'EOF'
import os, re, sys
bad = []
for root, _, files in os.walk('specs'):
    for f in files:
        if not f.endswith('.md'): continue
        p = os.path.join(root, f)
        text = open(p).read()
        for m in re.finditer(r'\]\((\.[^)]+)\)', text):
            target = os.path.normpath(os.path.join(root, m.group(1)))
            if not os.path.exists(target):
                bad.append(f"{p}: {m.group(1)}")
print('\n'.join(bad)); sys.exit(bool(bad))
EOF
```

Also confirm by hand: any file added, removed, or renamed under `specs/cpp/`
is reflected in `specs/cpp/README.md`'s file table, `specs/cpp/cpp/index.md`'s
Guidelines Index, and — if it changes what installs — `README.md`'s layout
tree. These four places listing the same file set is the invariant that breaks
most easily.

---

**Language**: All documentation should be written in **English**.
