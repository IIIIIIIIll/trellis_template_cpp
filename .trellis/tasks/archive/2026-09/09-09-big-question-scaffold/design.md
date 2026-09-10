# Design (child 2): big-question scar home

> Depends on child 1's contract rewrite and file set. This design inlines
> the sibling format so no external clone is needed.

## Layer mechanics

`specs/cpp/big-question/` becomes the template's third layer directory.
Layer discovery treats every directory under the template root as an
auto-discovered layer (stray `README.md` ignored — the way `guides/` and
`cpp/` install); it lands at the consumer's
`.trellis/spec/big-question/`. Injection: only files with frontmatter and
matching `paths:` are injected — `index.md` only (≈ 3–4 KB, well under the
9,400-char budget alongside the other layers). Incident files carry no
frontmatter → never injected, reachable via the index and the router
pointer.

## `index.md` skeleton

```
---
description: Big-question incident deep-dives for C++ — severity-indexed exemplars and the consumer growth format
paths: [<shared C++ glob list>]
---

# Common Issues and Solutions

> Documented pitfalls discovered on the path this template's guidelines
> describe — each as Problem / Root Cause / Solution / Key Takeaways, with
> the owning guide linked instead of duplicated.

## Severity Levels          ← table: Critical / Warning / Info, defined
## Issue Index              ← table: Issue | Category | Severity (3 rows)
## How to Contribute        ← 4 numbered steps (format contract; zero ```cpp fences — bash legal)
---
**Language**: …
```

Footer: Language-only (matches the guides-layer convention; no CG
attribution).

## Incident skeletons (content briefs for the writer)

### `static-initialization-order.md` (Category: Initialization & Linkage; Critical)

Opens with the italic disclosure line: *"Format exemplar for a canonical
C++ incident class — not project history."*

- Signature line: "A global or static object reads another global's value
  before that global is initialized — correctness depends on link order."
- Problem: crash/garbage before `main`; value correct in one binary, wrong
  in another; symptom moves when link order changes.
- Root cause: dynamic initialization order across translation units is
  unspecified; readers in other TUs may read the global before its
  dynamic initializer has run.
- Solution: constant-initialize (`constexpr`), function-local statics
  (Meyers singleton) for order-dependent state, keep initializers
  intra-TU; when the dependency is unavoidable, name it in the owning
  guide's terms.
- Takeaways: cross-TU global reads are a design smell; link order is not a
  contract.
- Read first: expressions-and-flow (namespace-scope objects),
  headers-and-dependencies.

### `dangling-string-view.md` (Ownership & Lifetime; Critical)

Opens with the italic disclosure line: *"Format exemplar for a canonical
C++ incident class — not project history."*

- Signature: "A `std::string_view`/reference stored beyond the statement
  that created it points into a container that later mutated."
- Problem: ASan use-after-free flags a READ far from the bug; the store
  looked harmless; intermittent under reserve/split/SSO differences.
- Root cause: views/pointers do not extend lifetime; owner mutation
  (growth, erase, temporary materialization) invalidates.
- Solution: check every stored reference against the owner's mutation
  surface for the whole life of the store (the guide row verbatim in
  spirit); store by value or document the owner contract; reserve up
  front where growth is predictable, otherwise restructure so no
  reference is held across mutation.
- Takeaways: ASan flags the use, never the store — the store is the review
  moment.
- Read first: memory-discipline (stored references), expressions-and-flow
  (range-for extension).

### `optimization-ub.md` (Undefined Behavior & Optimization; Critical)

Opens with the italic disclosure line: *"Format exemplar for a canonical
C++ incident class — not project history."*

- Signature: "Works at `-O0`, breaks at `-O2` — or breaks only under a
  different compiler/STL build."
- Problem: debug build hides it; release build misbehaves; "worked before
  the compiler upgrade."
- Root cause: UB gives the optimizer license — uninitialized reads, signed
  overflow, invalid pointers/dangling reads get folded away or transformed;
  `-O0` merely fails to expose it.
- Solution: treat `-O0`-vs-`-O2` divergence as a UB signature, not a
  compiler bug; run UBSan + ASan in CI; `-D_GLIBCXX_ASSERTIONS` (or
  equivalent) for STL checks; find the owning guide rule and the detector.
- Takeaways: UB that happens to be fast is still UB; green tests do not
  license it.
- Read first: performance, expressions-and-flow, testing-conventions
  (sanitizer gates).

## Router + guide edits (deferred-gap completion)

- `guides/index.md`: (a) Available-Guides table gains pointer row
  "Growing This Layer — big-question/" OR a dedicated one-line section
  after Core Principles; (b) Core Principles "Learn From Bugs" line links
  `../big-question/index.md`. Keep the router ≤ 9,000 B after edits.
- `guides/bug-root-cause-thinking-guide.md`: "Record the Incident" section
  links `../big-question/index.md`; keep ≤ 9,000 B.

## README sync

- `specs/cpp/README.md` layout tree: `big-question/` section after
  `guides/` listing 4 files; file table gains 4 rows; install prose
  sentence: three layer directories install (`cpp/`, `guides/`,
  `big-question/`).
- Root `README.md`: layer enumeration line if present.

## Risks

- **Fabricated-scar smell**: mitigated by the mandated exemplar-disclosure
  line on every seed file and by seeding canonical classes already owned by
  the guide corpus (nothing new is claimed).
- **Drift vs cpp/ docs**: incident files state mechanism + strategy, never
  rule text; the "Read first" links carry the normative content.
- **Severity inflation**: vocabulary fixed to the three sibling levels;
  all three seeds are Critical (canonical classes), which is accurate, not
  inflation — record the reasoning in the index if questioned.
- **Gate ordering**: this child's router/guide edits keep the relative-link
  gate green because `big-question/index.md` exists in the same change.
