# Consuming This Registry

> Consumer guide for this repository: installing the C++ guideline template
> into a Trellis-managed project, picking a source string, staying updated,
> and fixing common problems. Hosting the registry instead? See
> [HOSTING.md](./HOSTING.md).

---

## Prerequisites

- The Trellis CLI installed.
- A Trellis-managed repository — any project with a `.trellis/` directory,
  freshly scaffolded or long-running.
- A reachable copy of this registry. Prefixed fetches (`gh:`/`github:`/
  `gitlab:`/`bitbucket:`) read anonymously over HTTPS, so the hosted
  repository must be public; use the SSH source form for private copies.

---

## Adopting Into an Existing Project

The same command adopts into a fresh scaffold or an existing Trellis project:

```sh
trellis init --registry gh:<owner>/trellis-specs --template cpp
```

What happens:

- Template contents copy into `.trellis/spec/`.
- The `cpp/` layer directory lands as `.trellis/spec/cpp/`, discovered
  automatically by Trellis on startup.
- The stray template `README.md` beside the layer installs as documentation;
  layer discovery ignores it.
- Adoption persists the source so later refreshes know where to sync from,
  in `.trellis/config.yaml`:

  ```yaml
  registry:
    spec:
      source: gh:<owner>/trellis-specs
      template: cpp
  ```

Monorepos: `trellis init` prompts once per detected package. Packages that
adopt the template skip blank-spec scaffolding, and their content lands under
`.trellis/spec/<pkg>/`.

---

## Choosing a Template

Trellis probes `{subdir}/index.json` at the source. This repository ships one,
so consumers always get **marketplace mode**: an interactive picker over the
templates listed there. Scripts cannot answer a picker — pass `--template cpp`
explicitly, with `-y` for non-interactive runs, otherwise init fails with
`Registry is a marketplace with multiple templates.`:

```sh
trellis init -y --registry gh:<owner>/trellis-specs --template cpp
```

---

## Source Strings at a Glance

| Form | Example | Notes |
|------|---------|-------|
| `gh:` / `github:` | `gh:<owner>/trellis-specs` | Anonymous raw fetch; public read required |
| `gitlab:` | `gitlab:<owner>/trellis-specs` | Same transport against GitLab raw URLs |
| `bitbucket:` | `bitbucket:<owner>/trellis-specs` | Same transport against Bitbucket raw URLs |
| Plain HTTPS | `https://github.com/user/repo` | Normalized automatically; GitHub/GitLab browse URLs work as-is |
| SSH | `git@host:org/repo[/subdir][#ref]` | Git-clone backend using your existing SSH credentials; the only private-capable path |

Append `#ref` to pin a branch or tag — `gh:<owner>/trellis-specs#v1.2.0`
makes updates reproducible. Omitting the ref floats on `main`, which
auto-freshens on every update. Full anatomy and HTTPS normalization rules:
[HOSTING.md](./HOSTING.md).

---

## Staying Updated

```sh
trellis update
```

Each run re-probes `index.json`, resolves the persisted `template: cpp` id,
downloads the current template, and reconciles it through the standard
hash/conflict flow against `.trellis/.template-hashes.json`:

- Files you have not touched refresh silently.
- Files you modified trigger the "Modified by you" prompt — your
  project-specific changes are never overwritten silently.
- An unreachable registry degrades to a yellow warning only; updates never
  fail hard because of the network, so consumers keep working offline.

Restructures install additively: when a template release renames or moves
guideline files — most recently the phase grouping into `design/`,
`implement/`, and `verification/` subdirectories — the new paths are added
and files under an old name or location are left orphaned on your side;
nothing under `.trellis/spec/` is deleted for you. After an update that
introduces many new guideline paths, diff your `cpp/` layer against the
template and remove stale orphans by hand.
Pure additions — a new layer directory (such as `guides/` alongside `cpp/`)
or new files beside existing ones — need no cleanup at all: they simply
install, and only renames or moves create orphans.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Registry is a marketplace with multiple templates.` | Scripted init omitted `--template`; the picker cannot run | Add `--template cpp` (and `-y`) |
| Spec refresh skipped with a gray notice on update | Marketplace registries require `registry.spec.template`; it is missing from `.trellis/config.yaml` | Add `template: cpp` to the registry block |
| Yellow warning naming the template, then skip | Its id resolved to nothing in the registry's `index.json` | Check the source string points at the right repo and ref |
| Yellow warning on update, everything else works | Registry unreachable (offline, wrong host) | Expected degradation — retry when reachable |
| Guideline files stop refreshing | You modified them locally; the "Modified by you" prompt protects them | Expected protection, not a bug |
| 404 or auth failure fetching under `gh:` | Anonymous raw fetches need a public repo | Switch to the SSH source form |
| Update brings different content than before | No `#ref`: the source floats on `main` | Pin a tag, e.g. `#v1.2.0` |
| Files appear under `.trellis/spec/<pkg>/` | Monorepo layout: content lands per adopted package | Expected |

---

## Where to Go Next

- Hosting, publishing, source-string anatomy, and CI validation of this
  registry → [HOSTING.md](./HOSTING.md).
- What the guidelines cover and how they install →
  [specs/cpp/README.md](./specs/cpp/README.md).
