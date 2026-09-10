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
| `specs/cpp/cpp/**` | The product: phase-organized C++ guideline documents installed into consumer projects — 14 topic guides under `design/`, `implement/`, `verification/`, three phase routers, `index.md`, and the Core Guidelines disposition |
| `specs/cpp/guides/**` | The thinking-guide layer installed as `.trellis/spec/guides/`: C++ method (cue-triggered per-phase procedures routing into `cpp/`); no normative rules — shape contract in [Guideline Authoring](./guideline-authoring.md) |
| `specs/cpp/big-question/**` | Consumer incident scars installed as `.trellis/spec/big-question/`: severity index, contribution format, and three seeded exemplar narratives — grown by consumers, not shipped rules; shape contract in [Guideline Authoring](./guideline-authoring.md) |
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
index explains why nothing else belongs there. (The template ships its own
C++ thinking-guide layer from `specs/cpp/guides/`, plus the consumer scar
home at `specs/cpp/big-question/`; the tombstone is this repo's local layer
only.)

---

## Pre-Development Checklist

Before changing files, route through the matching guide:

| Task involves | Read first |
|---------------|------------|
| Editing any file under `specs/cpp/**` (the guideline docs, routers, or their README) | [Guideline Authoring](./guideline-authoring.md) |
| Adding or renaming guideline documents, changing doc structure or tone | [Guideline Authoring](./guideline-authoring.md) |
| `index.json`, adding/removing a template entry, moving directories | [Registry Contract](./registry-contract.md) |
| `README.md`, `USAGE.md`, `HOSTING.md`, install/update behavior claims | [Registry Contract](./registry-contract.md) |

A change that moves or renames guideline files almost always touches both
guides: the authoring guide owns the content links, the contract guide owns
the manifest, install mapping, and registry docs.

---

## Quality Check

No compiler or test suite exists here; verification is structural, plus one
compile gate: the snippet harness builds every guideline example against
stubs. Run before declaring any change complete:

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

# Rule grammar binds: every rule lead-in, strength marker, and Caught-by
# pairing is well-formed across the 14 topic guides
python3 tools/validate_rules.py

# Digest determinism: two consecutive extractions produce a byte-identical
# rules.json
python3 tools/extract_rules.py && cp specs/cpp/cpp/rules.json /tmp/rules-a.json \
  && python3 tools/extract_rules.py && cmp specs/cpp/cpp/rules.json /tmp/rules-a.json

# Snippet gate: every fenced ```cpp guideline example compiles under its
# annotated contract (clean / compile-error / compiles-UB); the report carries
# the compiles-UB inventory for manual sanitizer spot-checks
python3 tools/check_snippets.py
```

One scope note: the thinking-guide layer (`specs/cpp/guides/**` and
`specs/cpp/big-question/**`) sits outside both rule and snippet walks — each
tool defaults to `DEFAULT_DIR = specs/cpp/cpp` — so its gates are the
relative-link check above (it walks all of `specs/`) plus hand review.
Pointing `validate_rules.py --path specs/cpp/guides` at the layer naively
would spuriously fail `guides/index.md`: `EXEMPT_DOCS` in
`tools/rules_grammar.py` matches by basename, so the router inherits the
topic layer's attribution-footer requirement, which the layer deliberately
omits.

Also confirm by hand: any file added, removed, or renamed under `specs/cpp/`
is reflected in `specs/cpp/README.md`'s file table, `specs/cpp/cpp/index.md`'s
Guidelines Index, and — if it changes what installs — `README.md`'s layout
tree. These four places listing the same file set is the invariant that breaks
most easily.

---

**Language**: All documentation should be written in **English**.
