# C++ Guidelines Template

> Project-independent C++ coding guidelines packaged as a Trellis spec
> template: what installs where, how to consume it, and how updates stay
> safe alongside local edits.

---

## What Installs Where

Everything under this directory copies into the consumer's `.trellis/spec/`:

```
specs/cpp/            →  .trellis/spec/
├── README.md         →  .trellis/spec/README.md        (ignored by layer discovery)
└── cpp/              →  .trellis/spec/cpp/             (auto-discovered layer)
    ├── index.md
    ├── memory-and-ownership.md
    ├── error-handling.md
    ├── quality-guidelines.md
    ├── testing-conventions.md
    ├── functions-and-interfaces.md
    ├── classes-and-hierarchies.md
    ├── templates-and-generics.md
    ├── concurrency.md
    ├── expressions-and-flow.md
    ├── performance.md
    └── core-guidelines-alignment.md
```

- The `cpp/` directory at the template root becomes a spec layer at
  `.trellis/spec/cpp/`; Trellis discovers layers automatically on startup.
- The stray `README.md` beside the layer directory is documentation only and
  is ignored by layer discovery.

---

## Guideline Files

| File | Summary |
|------|---------|
| [index.md](./cpp/index.md) | Layer entry point: guidelines index, pre-development checklist, quality check |
| [memory-and-ownership.md](./cpp/memory-and-ownership.md) | RAII invariant, ownership ladder, pass-by conventions, iterator invalidation and other lifetime pitfalls |
| [error-handling.md](./cpp/error-handling.md) | Exceptions versus `expected`/error-code policy, failure contracts across API boundaries |
| [quality-guidelines.md](./cpp/quality-guidelines.md) | Naming, header hygiene, ODR and ABI pitfalls |
| [testing-conventions.md](./cpp/testing-conventions.md) | Test framework and layout, test naming, what deserves a test |
| [functions-and-interfaces.md](./cpp/functions-and-interfaces.md) | Function signature design, parameter and return-value conventions at API boundaries |
| [classes-and-hierarchies.md](./cpp/classes-and-hierarchies.md) | Class design and inheritance: invariants, composition versus virtual dispatch |
| [templates-and-generics.md](./cpp/templates-and-generics.md) | Templates, concepts, and generic library design |
| [concurrency.md](./cpp/concurrency.md) | Threads and shared state, synchronization discipline, data-race prevention |
| [expressions-and-flow.md](./cpp/expressions-and-flow.md) | Expression-level correctness, initialization, conversions, control flow |
| [performance.md](./cpp/performance.md) | Optimization work guided by measurement: hot paths, allocation pressure |
| [core-guidelines-alignment.md](./cpp/core-guidelines-alignment.md) | Adopt/adapt/covered-elsewhere stance per Core Guidelines section, section-to-guide map, curated clang-tidy checks, license note |

Baseline is C++17; deviations available in C++20/23 are called out where they
matter. The guidelines are opinionated defaults, not neutral surveys — adapt
them per project after install if your conventions differ.

---

## Consuming This Template

From a fresh or existing Trellis project, pointing at a hosted copy of this
registry (GitHub-first):

```sh
trellis init --registry gh:<owner>/trellis-specs --template cpp
```

Want the full walkthrough — adoption, updates, source strings,
troubleshooting? See [`USAGE.md`](../../USAGE.md) at the registry root.

To refresh an already-adopted installation later:

```sh
trellis update
```

---

## Adoption Lifecycle

1. **Init** — `trellis init --registry gh:<owner>/trellis-specs --template cpp`
   probes the registry's `index.json`, selects this template, and copies the
   files above into place.
2. **Persisted config** — adoption records the source in the project's
   `.trellis/config.yaml`:

   ```yaml
   registry:
     spec:
       source: gh:<owner>/trellis-specs
       template: cpp
   ```

3. **Update sync** — every `trellis update` re-probes `index.json`, resolves
   the `cpp` id, downloads the current template into a temp directory, and
   applies it through the standard hash/conflict flow against
   `.trellis/.template-hashes.json`.

### Local edits are protected

Files you have not touched refresh silently. Files you modified locally
trigger the "Modified by you" prompt during update, so your project-specific
changes are never overwritten silently. An unreachable registry degrades to a
yellow warning — updates never fail hard because of the network.
