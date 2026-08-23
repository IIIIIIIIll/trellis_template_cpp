# Core Guidelines Alignment

> How these guidelines relate to the ISO C++ Core Guidelines: what this project adopts, what it adapts, where each topic lives, and how deviations from an adopted rule are recorded.

---

## Overview

The [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) are the closest thing C++ has to a community-wide engineering standard, but they are advice rather than law, and following every rule literally serves nobody. Instead of re-litigating the philosophy inside each topic guide, this document records the project's stance toward every major Guidelines section in one place, and routes each section to the guide that operationalizes it.

Two commitments follow from that setup:

1. Rule identifiers such as `F.21` or `ES.20` appear throughout our guides as cross-reference anchors only. Every explanation is our own paraphrase; the Guidelines' prose and examples are never copied into this repository.
2. A stance recorded here is a contract with reviewers: **adapted** means a written, reasoned local difference exists in the companion guide — not that the rule was quietly ignored.

Stances used below:

| Stance | Meaning |
|--------|---------|
| Adopt | Followed as written; the companion guide adds enforcement detail |
| Adapt | Followed in intent, with a documented difference spelled out in the companion guide |
| Covered elsewhere | The substance already lives in one of our guides under different organization |

---

## Adoption Stance by Section

The table covers all fourteen major sections of the Guidelines plus their most load-bearing individual rules.

| Section | Area | Stance | Disposition |
|---------|------|--------|-------------|
| `P` | Philosophy | Adopt selectively | The intent is absorbed across every guide: express ideas directly in code (`P.1`), prefer compile-time checking (`P.5`), catch run-time errors early (`P.7`), and use supporting tools (`P.12`) — the last is why CI carries sanitizers and static analysis instead of trust |
| `I` | Interfaces | Adapt | Routed to Functions and Interfaces; the ban on transferring ownership through raw pointers (`I.11`) is adopted outright via the memory guide's ownership ladder |
| `F` | Functions | Adapt | Routed to Functions and Interfaces; cheap-to-copy inputs by value (`F.16`), returned out-values instead of out-parameters (`F.20`), named structs for multiple results (`F.21`), all with project-specific spelling |
| `ES` | Expressions and statements | Adapt | Routed to Expressions and Flow; initialize everything (`ES.20`) and refuse silent narrowing conversions (`ES.46`) carry over unchanged |
| `C` | Classes and class hierarchies | Adapt | Routed to Classes and Hierarchies; rule-of-five discipline (`C.21`), in-class member initializers (`C.48`), initialization over assignment in constructors (`C.49`), and suppressed copying on polymorphic types (`C.67`) are adopted verbatim in spirit |
| `Enum` | Enumerations | Adopt | Scoped `enum class` everywhere; enumerators use constant naming, not `ALL_CAPS` (`Enum.5`). Declaration style and naming live in Quality Guidelines |
| `R` | Resource management | Adopt | Owned end-to-end by [Memory and Ownership](./memory-and-ownership.md): RAII as invariant (`R.1`), no explicit owning `new`/`delete` (`R.11`), smart-pointer ladder with justification for sharing |
| `E` | Error handling | Adapt | Owned by [Error Handling](./error-handling.md); the exception-centric default story is replaced where ABI and module boundaries demand status returns, while RAII-for-leak-prevention (`E.6`) and throw-by-value/catch-by-const-reference survive intact |
| `T` | Templates and generic programming | Adapt | Routed to Templates and Generics; raise abstraction through templates (`T.1`), but metaprogramming needs a measured payoff before it replaces readable code — see also the constexpr discipline in Quality Guidelines |
| `CP` | Concurrency and parallelism | Adopt | Owned by Concurrency: RAII locks rather than bare lock/unlock pairs (`CP.20`), shared state minimized and documented, data races treated as defects rather than tuning opportunities |
| `SF` | Source files | Adopt | Owned by [Quality Guidelines](./quality-guidelines.md): self-contained headers, `#pragma once`, anonymous namespaces confined to `.cpp` files, `inline constexpr` globals in headers |
| `NL` | Naming and layout | Adapt | Naming rules live in [Quality Guidelines](./quality-guidelines.md) (standard-library rhythm, no type encoding in names); layout is delegated entirely to the committed clang-format configuration, so hand-maintained layout rules are deliberately out of scope |
| `PER` | Performance | Adapt | Owned by Performance: measurement first, hot paths only, allocation pressure priced explicitly; intuition-driven optimization is rejected |
| `Con` | Constants and immutability | Adopt | Default to immutable objects (`Con.1`): `const` and `constexpr` by default, mutability must justify itself at review |

Notes on upkeep:

- Rule numbering occasionally shifts upstream. When a cited ID moves, fix its citations during the next edit of the affected guide rather than in bulk sweeps.
- New sections added upstream get a row here before any guide starts citing them; an uncited section stays uncited until someone needs it.

---

## Recording a Deviation

When a task genuinely cannot follow a rule we adopted, deviating is allowed but must be visible: the comment names the rule ID and states the reason, mirroring Build and Toolchain's policy that silencing static analysis without justification is rejected in review.

Wrong:

```cpp
// NOLINT
std::tuple<std::string, int> split_endpoint(std::string_view line);
// Why silenced? Nobody will know next quarter.
```

Right:

```cpp
struct Endpoint {           // F.21: multiple results travel in a named struct
    std::string host;
    int port;
};
Endpoint parse_endpoint(std::string_view line);
```

And when deviation truly wins, the reasoning travels with the code:

```cpp
// Deviates from F.21: tuple return keeps this parser usable in a measured
// allocation-free loop where a named struct would add header coupling.
// Revisit if a third field ever appears.
std::tuple<std::string_view, int> split_host_port(std::string_view line);
```

A deviation comment answers three questions in two lines: which rule, why here, and what would change the answer. Anything longer belongs in the task discussion; anything shorter is a bare suppression.

---

## How a Rule Gets Adopted

A rule moves from the Guidelines into daily practice through four steps, and skipping any of them produces either dead documentation or unenforced aspiration:

1. **Propose with an ID.** A task or review names the rule it wants followed (`F.21`, `ES.46`) — not a paraphrase of its mood. The ID makes the discussion checkable.
2. **Pick a stance.** The rule lands in the stance table as adopt, adapt, or covered-elsewhere. "Adapt" requires writing down the difference in the companion guide at the same time; a stance without a documented difference is just an ignored rule with paperwork.
3. **Land enforcement.** Every adopted rule gets a catcher: a clang-tidy check from the curated list, a compiler warning already in the build, a sanitizer preset, or an explicit review checklist item. If nothing can catch it, say so in the guide rather than pretending CI has it covered.
4. **Update this file in the same change.** The stance table and the routing map are part of the diff, so the registry never describes a directory that no longer exists.

The reverse path exists too: when an adopted rule stops earning its keep — findings are all suppressed, or the pattern no longer occurs — remove the enforcement and demote the stance row in the same change. Guidelines hygiene is ordinary code hygiene.

---

## Profiles and the Sanitizer Matrix

The Guidelines group their highest-value rules into profiles (type safety, bounds safety, lifetime safety). We do not track profile conformance as such; instead each profile maps onto machinery that is already running:

| Guideline profile | Our equivalent enforcement |
|-------------------|----------------------------|
| Type safety | Warning set plus narrowing-conversion checks; `enum class` and explicit conversions per Expressions and Flow |
| Bounds safety | ASan preset for out-of-bounds access, container-invalidation table in Memory and Ownership for the cases ASan misses deterministically |
| Lifetime safety | Ownership ladder plus dangling-view review rules; ASan catches the escapes that reach memory |
| Concurrency safety | TSAN preset for threading changes, lock discipline in Concurrency |

The mapping is deliberate: where the Guidelines ask developers to be careful, we prefer a tool that is careless about feelings. A profile claim nobody measures is a mood, not a gate.

---

## Where Each Topic Lives

Routing table for the whole directory. When a task touches several rows, skim each listed guide before starting — the expensive C++ mistakes are cross-cutting.

| Guide | Owns | Fed by sections |
|-------|------|-----------------|
| [Functions and Interfaces](./functions-and-interfaces.md) | Signature design, parameter and return conventions at API boundaries, overloads and operators | `I`, `F` |
| [Classes and Hierarchies](./classes-and-hierarchies.md) | Class design, invariants, inheritance versus composition, virtual dispatch | `C` |
| [Templates and Generics](./templates-and-generics.md) | Concepts, generic library design, metaprogramming restraint | `T` |
| [Concurrency](./concurrency.md) | Threading model, synchronization primitives, shared-state minimization | `CP` |
| [Expressions and Flow](./expressions-and-flow.md) | Expression-level correctness, initialization, conversions, control flow | `ES`, `Con` |
| [Performance](./performance.md) | Measurement-first optimization, hot-path discipline, allocation pressure | `PER` |
| [Memory and Ownership](./memory-and-ownership.md) | Ownership ladder, lifetimes, container invalidation | `R`, parts of `I` |
| [Error Handling](./error-handling.md) | Failure contracts, exceptions versus expected-style results, module edges | `E` |
| [Quality Guidelines](./quality-guidelines.md) | Naming, header hygiene, ODR/ABI safety, constexpr discipline | `SF`, `NL`, `Enum` |
| [Testing Conventions](./testing-conventions.md) | What earns a test and how tests are organized | verification posture of `P` |
| [Build and Toolchain](./build-and-toolchain.md) | Warning policy, sanitizer matrix, clang-tidy curation, CI gates | tooling mandate of `P` |

This document owns none of those topics itself. It exists so the routing above stays consistent: when a guide changes a rule that came from the Guidelines, the stance table is updated in the same change. Coverage is explicit end to end: each topic guide now integrates the full Core Guidelines rule set for the sections it owns directly in its body, so every rule ID carries its recorded Adopt / Adapt / Covered-elsewhere disposition in context; this document remains the authoritative stance map, and the sections that belong to no topic guide stay ledgered at the bottom of this file.

---

## Curated clang-tidy Checks from the Guidelines

Build and Toolchain decides *how* clang-tidy runs (changed-lines in CI, curated allowlist, justified inline suppressions). It also already warns against enabling `cppcoreguidelines-*` wholesale: hundreds of hits bury signal. This guide proposes *which* individual checks earn a slot, grouped by how confidently they pay off.

Enable first — low noise, direct defect yield:

| Check | Guards against | Related rules |
|-------|----------------|---------------|
| `cppcoreguidelines-slicing` | Derived-to-base copies silently dropping the dynamic type | `C.67` |
| `cppcoreguidelines-init-variables` | Uninitialized locals | `ES.20` |
| `cppcoreguidelines-narrowing-conversions` | Lossy implicit conversions | `ES.46` |
| `cppcoreguidelines-pro-type-member-init` | Members left uninitialized | `C.48` |
| `cppcoreguidelines-special-member-functions` | Half-defined copy/move/destroy sets | `C.21` |
| `cppcoreguidelines-prefer-member-initializer` | Constructor-body assignments that belong in the init list | `C.49` |

Slicing deserves the example, because the compiler stays happy while behavior vanishes:

```cpp
// Wrong: HttpHandler sliced into Base on the way in; dispatch and fields gone.
void install(Base handler);
install(HttpHandler{});

// Right: borrow the object; storage decisions belong to the owner.
void install(const Base& handler);
```

Second wave — evaluate against your codebase before enabling:

| Check | Notes |
|-------|-------|
| `cppcoreguidelines-virtual-class-destructor` | Polymorphic bases need virtual destructors; noisy only where protected non-virtual destructors are deliberate |
| `cppcoreguidelines-no-malloc` | Flags `malloc`/`free`/`calloc`/`realloc`; aligns with the ownership ladder, delete the check if C interop dominates the tree |
| `cppcoreguidelines-pro-type-static-cast-downcast` | Unsound downcasts; kind-tag dispatch (Quality Guidelines) makes most of them unnecessary anyway |
| `cppcoreguidelines-avoid-non-const-global-variables` | Mutable globals are review bait; expect findings in legacy glue and fix or justify each one |
| `cppcoreguidelines-rvalue-reference-param-never-moved` | Sink parameters declared but never moved from — pairs with the pass-by rules in Memory and Ownership |

Skip with a written reason, not by omission:

| Check | Why skipped here |
|-------|------------------|
| `cppcoreguidelines-owning-memory` | Models `gsl::owner`; since owning raw pointers are banned outright, its findings duplicate review rules instead of adding yield |
| `cppcoreguidelines-avoid-magic-numbers` | High churn, low signal alongside normal review |

When a check lands in `.clang-tidy`, record it in the same change that adopts the corresponding rule; when a check is rejected, leave the reason here so the question is answered once.

---

## License Note

The Core Guidelines are published by Standard C++ Foundation under terms that permit creating derivative works for internal business purposes, provided attribution accompanies the derivative. This directory is exactly such a derivative: an internal-only digest that cites rule identifiers and links back to the source while reproducing neither its text nor its examples.

Consequences for anyone touching these files:

- Do not publish this registry externally or fold its contents into shipped product documentation; link readers to the Guidelines instead.
- Keep the attribution footer on every guide; it is part of the license bargain, not decoration.
- If a future use falls outside internal business use, re-read the license terms at the source before copying anything further.

---

## Quality Check

Before merging changes to this file or citing new rule IDs elsewhere, confirm:

- [ ] Stance table lists all fourteen sections: `P`, `I`, `F`, `ES`, `C`, `Enum`, `R`, `E`, `T`, `CP`, `SF`, `NL`, `PER`, `Con`
- [ ] Every disposition pointer targets a guide that actually exists in this directory
- [ ] Rule IDs appear as inline code and serve cross-reference only; no Guideline prose or examples reproduced anywhere in the directory
- [ ] New clang-tidy candidates were weighed against the Build and Toolchain curation policy before entering `.clang-tidy`, and skips carry reasons
- [ ] Any adopted-rule change in a companion guide updated its row here in the same change
- [ ] Deviation comments name the rule ID and reason; bare suppressions stay rejected
- [ ] Attribution footer present on every guide in this directory

---

## Residual Sections Ledger

Six Guidelines sections contain nothing a topic guide can operationalize as coding practice on its own: `A` (library architecture), `CPL` (C interop), `FAQ` (upstream project background and GSL history), `NR` (deliberate anti-rules), `SL` (standard-library policy), and `In` (meta-advice). Each entry below records where its substance lands so no rule ID in those sections goes unaddressed.

| Rule | Stance | Disposition |
|------|--------|-------------|
| `A.1` | Adopt | Isolate less stable code behind stable seams so it can be unit-tested, refactored, and deprecated without dragging the rest of the system along. |
| `A.2` | Adopt | Potentially reusable parts ship as maintained libraries — headers plus optional binaries, documented together — not copy-pasted fragments scattered through applications. |
| `A.4` | Adopt | Library dependency graphs stay acyclic: cycles complicate builds and invite indeterminism; the file-level twin lives in Quality Guidelines under `SF.9`. |
| `CPL.1` | Adopt | Prefer C++ to C for its type checking and notation; enforced by simply compiling everything with a C++ compiler. |
| `CPL.2` | Adapt | If C survives anywhere it stays in the common C/C++ subset compiled as C++, so the C++ compiler checks it; a genuine C-only translation unit would be a Build-and-Toolchain-visible deviation. |
| `CPL.3` | Adopt | Call C through a C++ facade: `extern "C"` declarations sit at the boundary while callers get RAII and type safety, never raw C idioms. |
| `FAQ.1` | Covered elsewhere | Interpretive guidance absorbed into topic stances: the aims are restated as this directory's Overview charter — modern, machine-checkable C++. |
| `FAQ.2` | Covered elsewhere | Announcement history from CppCon 2015; provenance trivia with no practice to adopt. |
| `FAQ.3` | Covered elsewhere | Authorship credit, satisfied once by the attribution footer every guide carries. |
| `FAQ.4` | Covered elsewhere | Upstream contribution process; improving this digest follows ordinary task flow instead. |
| `FAQ.5` | Covered elsewhere | Upstream editor/maintainer path; no analogue needed here. |
| `FAQ.6` | Covered elsewhere | Confirms the Guidelines are advisory rather than committee-approved — the premise of this file's "advice rather than law" framing. |
| `FAQ.7` | Covered elsewhere | Repository-hosting explanation (Standard C++ Foundation); consistent with the License Note. |
| `FAQ.8` | Adopt | Modern-C++-only scope confirmed; matches this directory's C++17 baseline with noted C++20 refinements. |
| `FAQ.9` | Adopt | The Guidelines propose no new language features, and likewise every cited practice here uses shippable standard features only. |
| `FAQ.10` | Covered elsewhere | Markdown and toolchain trivia about upstream sources; irrelevant to this digest. |
| `FAQ.50` | Adapt | We take the concept and decline the dependency: standard library plus curated warnings replace any GSL requirement — the documented difference is the clang-tidy curation above. |
| `FAQ.51` | Adapt | Microsoft's GSL is one implementation among several; nothing here vendors or assumes it. |
| `FAQ.52` | Adopt | Interfaces-not-implementations reasoning backs preferring standard types over GSL aliases wherever an equivalent exists. |
| `FAQ.53` | Covered elsewhere | Why GSL bypassed Boost; historical context only. |
| `FAQ.54` | Adopt | GSL was never standardized — one more reason the `std` equivalent wins by default. |
| `FAQ.55` | Adopt | The view taxonomy adopted directly: `std::string_view` for read-only views (C++17) and `std::span` for read-write ones (C++20), not `gsl::span<char>`. |
| `FAQ.56` | Covered elsewhere | Context for `owner` versus `observer_ptr`; moot because owning raw pointers are banned outright in Memory and Ownership. |
| `FAQ.57` | Covered elsewhere | Context for `stack_array`; `std::array` fills that need under Memory and Ownership's container guidance. |
| `FAQ.58` | Covered elsewhere | Context for `dyn_array`; fixed-size heap arrays are rare and `std::vector` covers them. |
| `FAQ.59` | Adapt | `Expects` is a contract-syntax placeholder, not `assert`; precondition discipline lives in Error Handling pending language contracts. |
| `FAQ.60` | Adapt | Same story for `Ensures` postconditions: Error Handling owns the failure-contract vocabulary, not a GSL macro. |
| `NR.1` | Adopt | Deliberate anti-rule acknowledged: declare at first use with an initializer; declarations-on-top manufactures uninitialized variables. |
| `NR.2` | Adopt | Deliberate anti-rule acknowledged: early returns concentrate error handling; single-return gymnastics invent extra state variables. |
| `NR.3` | Adapt | Deliberate anti-rule acknowledged with a documented carve-out: exceptions stay the default, replaced by status returns at module and ABI edges per Error Handling. |
| `NR.4` | Adopt | Deliberate anti-rule acknowledged: cohesive classes group under namespaces and shared headers; one-class-per-file sprawl slows builds without aiding maintenance. |
| `NR.5` | Adopt | Deliberate anti-rule acknowledged: constructors deliver ready-to-use objects with established invariants; two-phase `Init()` patterns leak semi-constructed objects. |
| `NR.6` | Adopt | Deliberate anti-rule acknowledged: RAII makes goto-exit cleanup ladders obsolete pre-exception relics. |
| `NR.7` | Adopt | Deliberate anti-rule acknowledged: protected data is global data scoped to a hierarchy; keep data private — Classes and Hierarchies territory. |
| `SL.1` | Adopt | Use libraries wherever possible: reinvented wheels lack reviewers, tests, and fixes; adopted through Quality Guidelines' library posture. |
| `SL.2` | Adopt | Standard library before third-party libraries — most scrutinized, most portable, least supply-chain risk; baked into Quality Guidelines' uniformity principle. |
| `SL.3` | Adopt | Nothing user-defined enters namespace `std`: the same `[namespace.std]` reasoning behind banning forward-declared `std::` types in Quality Guidelines. |
| `SL.4` | Adopt | Umbrella rule: use standard components within their contracts; concrete catchers distributed across the profile mappings earlier in this file. |
| `In.0` | Adopt | Meta-entry: don't panic — understand a rule's implications before applying it, embodied here in the demand for reasoned stances and justified deviations. |
---

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
