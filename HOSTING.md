# Hosting a Trellis Spec Registry

> Operations guide for this repository: how Trellis resolves, installs, and
> updates spec templates served from a self-hosted registry like this one.

---

## Source String Anatomy

Every registry reference uses one format:

```
provider:owner/repo/subdir#ref
```

- `provider` — one of the prefixes below (or omitted for plain HTTPS URLs,
  which are auto-normalized).
- `owner/repo` — the repository holding your templates.
- `subdir` — path inside the repo where the template or registry root lives.
  For this repository it is empty at the repo root, or e.g. `specs/cpp` to
  address one template directly.
- `ref` — git branch or tag. Defaults to `main` when omitted.

### Anonymous raw-file prefixes

| Prefix     | Raw file URL pattern                                        |
|------------|-------------------------------------------------------------|
| `gh:`      | `https://raw.githubusercontent.com/{repo}/{ref}/{subdir}`   |
| `github:`  | `https://raw.githubusercontent.com/{repo}/{ref}/{subdir}`   |
| `gitlab:`  | `https://gitlab.com/{repo}/-/raw/{ref}/{subdir}`            |
| `bitbucket:` | `https://bitbucket.org/{repo}/raw/{ref}/{subdir}`         |

These fetch files anonymously over HTTPS, so the hosted repository must be
publicly readable. They are the fastest path and the recommended default for
open registries like this one.

### Plain HTTPS URLs

Recognized HTTPS URLs are normalized automatically:

- `https://github.com/user/repo` becomes `gh:user/repo`
- `https://github.com/user/repo/tree/branch/path` becomes
  `gh:user/repo/path#branch` — GitHub/GitLab web browse URLs work as-is.

Unknown hosts are not normalized; they fall through to the git backend
(appendix below).

### Which paths can be private

- Prefixed raw fetches (`gh:`/`github:`/`gitlab:`/`bitbucket:`) and their
  normalized HTTPS equivalents require public read access.
- SSH sources (`git@host:org/repo`) and unknown HTTPS hosts use a git-clone
  backend instead of anonymous raw HTTP. These are the only private-repo-capable
  paths; self-hosted instances are treated as GitLab-compatible.

---

## Mode Detection

Trellis probes `{subdir}/index.json` with a 5-second timeout:

- **Found** → marketplace mode. The CLI shows an interactive picker over the
  entries in `index.json`. Running `trellis init -y --registry <source>`
  without `--template` fails with:
  `Registry is a marketplace with multiple templates.` — pass
  `--template cpp` explicitly in scripts.
- **404** → direct-download mode. The subdir itself is treated as one template;
  no manifest file exists.

This repository ships an `index.json`, so consumers get marketplace mode and
can add more template layers later without breaking existing ones.

---

## Install Mapping

For a `spec`-type template such as `cpp`:

- Template contents copy into `.trellis/spec/`.
- Layer directories at the template root become auto-discovered layers:
  this template's `cpp/` directory lands as `.trellis/spec/cpp/`.
- A stray `README.md` beside layer directories is ignored by layer discovery,
  so shipping docs next to guidelines is safe.
- Monorepos: `trellis init` prompts per detected package. Packages that adopt
  the template skip blank-spec scaffolding, and content lands under
  `.trellis/spec/<pkg>/`.

---

## Update Lifecycle

Adoption persists into the consumer's `.trellis/config.yaml`:

```yaml
registry:
  spec:
    source: gh:<owner>/trellis-specs
    template: cpp
```

On every `trellis update`:

1. Re-probe `index.json`. Marketplace registries REQUIRE
   `registry.spec.template`; if missing, the registry spec refresh is skipped
   with a gray notice.
2. Resolve the id against the index. Missing entry → yellow warning, skip.
3. Download the template into a temp directory (capped around 30 seconds).
4. Run collected spec files through the standard hash/conflict flow against
   `.trellis/.template-hashes.json`: pristine files refresh silently; locally
   edited files trigger the "Modified by you" prompt so consumer changes are
   never clobbered.

An unreachable registry produces a yellow warning only — never a fatal error.
Consumers keep working offline.

---

## Versioning

Pin a release inside the source string:

```yaml
registry:
  spec:
    source: gh:<owner>/trellis-specs#v1.2.0
    template: cpp
```

- Pinning via `#<tag>` makes updates reproducible; bumping means editing one
  config line.
- Floating `main` (no ref) auto-freshens on every update.
- Recommendation: tag per guideline release in this repository, and pin in
  consumer configs until a deliberate upgrade.

---

## Failure Visibility and CI

Consumer-side registry problems degrade to warnings or skips, not errors — a
broken index can go unnoticed downstream. Validate in this repository's CI:

1. JSON-schema check `index.json` (required fields per template entry).
2. Every `templates[].path` exists in the tree.
3. Markdown lint across all guideline documents.

Run these on every push and on tag creation.

---

## Appendix: Private and Self-Hosted Registries

GitHub-first hosting covers most teams. For private guideline sets:

- Use SSH form (`git@host:org/repo[/subdir][#ref]`) pointing at a private
  GitHub/GitLab/Bitbucket repository, or any unknown HTTPS host running git.
- Self-hosted git servers are treated as GitLab-compatible by the clone
  backend.
- Clone access uses the consumer's existing SSH credentials; no tokens are
  embedded in `config.yaml`.
- Everything above (mode detection, install mapping, update lifecycle)
  behaves identically; only transport differs.

---

## How This Maps to Trellis Internals

| Behavior documented here | Implementation |
|--------------------------|----------------|
| Source parsing, raw URL patterns, HTTPS normalization, backends | `packages/cli/src/utils/template-fetcher.ts` |
| Update lifecycle: re-probe, id resolution, temp download, conflict flow, warning degradation | `packages/cli/src/commands/update.ts` |
| Install mapping: spec scaffolding, per-package layout, remote-template adoption | `packages/cli/src/configurators/workflow.ts` |
