# C++ Development Guidelines

> Best practices for native C++ development in this project.

---

## Overview

This directory contains the guidelines for C++ development. They are opinionated defaults targeting a C++17 baseline, with C++20/23 differences noted where they change a recommendation. Treat them as the starting point to adapt: record what your project actually enforces, not aspirations nobody checks.

---

## Guidelines Index

| Guide | Description |
|-------|-------------|
| [Memory and Ownership](./memory-and-ownership.md) | RAII invariant, ownership ladder, pass-by conventions, iterator invalidation and other lifetime pitfalls |
| [Error Handling](./error-handling.md) | Exceptions versus `expected`/error-code policy, failure contracts across API boundaries |
| [Quality Guidelines](./quality-guidelines.md) | Naming, header hygiene, ODR and ABI pitfalls |
| [Testing Conventions](./testing-conventions.md) | Test framework and layout, test naming, what deserves a test |
| [Functions and Interfaces](./functions-and-interfaces.md) | Function signature design, parameter and return-value conventions at API boundaries |
| [Classes and Hierarchies](./classes-and-hierarchies.md) | Class design and inheritance: invariants, composition versus virtual dispatch |
| [Templates and Generics](./templates-and-generics.md) | Templates, concepts, and generic library design |
| [Concurrency](./concurrency.md) | Threads and shared state, synchronization discipline, data-race prevention |
| [Expressions and Flow](./expressions-and-flow.md) | Expression-level correctness, initialization, conversions, control flow |
| [Performance](./performance.md) | Optimization work guided by measurement: hot paths, allocation pressure |

---

## Adapting These Guidelines

These documents ship with concrete defaults so a new repository starts consistent instead of empty:

1. Keep the **structure** (sections, tables, wrong-vs-right examples) and replace specifics that conflict with your project's reality
2. Document **actual** conventions, not ideals; a rule nobody enforces is worse than no rule
3. Add **common mistakes** your team has made, pairing each pitfall with the tool that catches it
4. When a rule stops being enforced by tooling or review, either restore enforcement or delete the rule

---

## Core Guidelines Disposition

The [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) are advice rather than law; instead of re-litigating philosophy inside each topic guide, this section records the project's stance toward every major Guidelines section in one place and routes it to the guide that operationalizes it. Rule IDs such as `F.21` or `ES.20` appear throughout these guides as cross-reference anchors only — every explanation is our own paraphrase, and neither upstream prose nor examples are copied. A stance recorded here is a contract with reviewers: **adapt** means a written, reasoned local difference exists in the companion guide, not that the rule was quietly ignored. Questions about adopting or deviating from a specific rule resolve against the tables below.

| Stance | Meaning |
|--------|---------|
| Adopt | Followed as written; the companion guide adds enforcement detail |
| Adapt | Followed in intent, with a documented difference spelled out in the companion guide |
| Covered elsewhere | The substance already lives in one of our guides under different organization |

### Disposition by Section

All fourteen major Guidelines sections, each routed to the guide that owns it:

| Section | Stance | Lives in | Disposition |
|---------|--------|----------|-------------|
| `P` | Adopt selectively | Every guide | Express intent directly (`P.1`), compile-time over run-time checking (`P.5`, `P.7`), supporting tools over trust (`P.12`) |
| `I` | Adapt | [Functions and Interfaces](./functions-and-interfaces.md) | No ownership transfer through raw pointers (`I.11`) via the memory guide's ownership ladder |
| `F` | Adapt | [Functions and Interfaces](./functions-and-interfaces.md) | Cheap copies by value (`F.16`), returned out-values (`F.20`), named multi-result structs (`F.21`) |
| `ES` | Adapt | [Expressions and Flow](./expressions-and-flow.md) | Initialize everything (`ES.20`); refuse silent narrowing conversions (`ES.46`) |
| `C` | Adapt | [Classes and Hierarchies](./classes-and-hierarchies.md) | Rule-of-five discipline (`C.21`), in-class initializers (`C.48`, `C.49`), no copying polymorphic types (`C.67`) |
| `Enum` | Adopt | [Quality Guidelines](./quality-guidelines.md) | Scoped `enum class` everywhere; constant-style enumerator naming, not `ALL_CAPS` (`Enum.5`) |
| `R` | Adopt | [Memory and Ownership](./memory-and-ownership.md) | RAII invariant (`R.1`); no owning `new`/`delete` (`R.11`); smart-pointer ladder with justified sharing |
| `E` | Adapt | [Error Handling](./error-handling.md) | Exceptions default, status returns at ABI edges; leak prevention (`E.6`) intact |
| `T` | Adapt | [Templates and Generics](./templates-and-generics.md) | Raise abstraction through templates (`T.1`); metaprogramming needs a measured payoff |
| `CP` | Adopt | [Concurrency](./concurrency.md) | RAII locks over bare lock/unlock pairs (`CP.20`); shared state minimized; data races are defects |
| `SF` | Adopt | [Quality Guidelines](./quality-guidelines.md) | Self-contained headers, `#pragma once`, anonymous namespaces confined to `.cpp` files |
| `NL` | Adapt | [Quality Guidelines](./quality-guidelines.md) | Naming owned here; layout delegated entirely to the committed clang-format configuration |
| `Per` | Adapt | [Performance](./performance.md) | Measurement first, hot paths only, allocation pressure priced explicitly |
| `Con` | Adopt | [Functions and Interfaces](./functions-and-interfaces.md) | Immutable by default (`Con.1`): `const`/`constexpr` unless mutability justifies itself at review |

### Recording a Deviation

When a task genuinely cannot follow a rule we adopted, deviating is allowed but must be visible: bare suppressions are rejected, and a deviation comment names the rule ID, states the reason, and says what would change the answer — mirroring the directory-wide ban on silencing static analysis without justification. Anything longer belongs in the task discussion; anything shorter is a bare suppression.

```cpp
struct Endpoint {           // F.21: multiple results travel in a named struct
    std::string host;
    int port;
};
Endpoint parse_endpoint(std::string_view line);

// Deviates from F.21: tuple keeps this parser usable in a measured,
// allocation-free loop where a named struct would add header coupling.
// Revisit if a third field ever appears.
std::tuple<std::string_view, int> split_host_port(std::string_view line);
```

### Residual Sections Ledger

Nine Guidelines sections contain nothing a topic guide can operationalize as coding practice on its own: `A` (library architecture), `CPL` (C interop), `FAQ` (upstream background and GSL history), `GSL` (guidelines support library), `NR` (deliberate anti-rules), `Pro` (safety profiles), `RF` (meta-commentary on coding standards), `SL` (standard-library policy), and `In` (meta-advice). Pure-historical FAQ entries — announcement history, authorship credit, hosting and toolchain trivia, context for GSL-only constructs made moot by outright bans or standard equivalents — are provenance trivia carrying no practice and get no row. Every remaining entry records where its substance lands so no cited rule ID goes unaddressed:

| Rule | Stance | Disposition |
|------|--------|-------------|
| `A.1` | Adopt | Isolate less-stable code behind stable seams so it can be tested, refactored, and deprecated alone |
| `A.2` | Adopt | Reusable parts ship as maintained libraries — headers plus optional binaries — not copy-pasted fragments |
| `A.4` | Adopt | Library dependency graphs stay acyclic; the file-level twin lives in Quality Guidelines under `SF.9` |
| `CPL.1` | Adopt | Prefer C++ for its type checking; enforced simply by compiling everything with a C++ compiler |
| `CPL.2` | Adapt | Surviving C stays in the common subset compiled as C++; genuine C-only translation units are recorded deviations |
| `CPL.3` | Adopt | Call C through a C++ facade: `extern "C"` at the boundary, RAII and type safety for callers |
| `FAQ.8` | Adopt | Modern-C++-only scope confirmed; matches this directory's C++17 baseline with noted C++20 refinements |
| `FAQ.9` | Adopt | The Guidelines propose no new language features; every cited practice here uses shippable standard features |
| `FAQ.50` | Adapt | Concept taken, dependency declined: standard library plus curated warnings replace any GSL requirement |
| `FAQ.51` | Adapt | Microsoft's GSL is one implementation among several; nothing here vendors or assumes it |
| `FAQ.52` | Adopt | Interfaces-not-implementations reasoning backs standard types over GSL aliases wherever equivalents exist |
| `FAQ.54` | Adopt | GSL was never standardized — one more reason the `std` equivalent wins by default |
| `FAQ.55` | Adopt | View taxonomy adopted directly: `std::string_view` for read-only views (C++17), `std::span` for read-write (C++20) |
| `FAQ.59` | Adopt | `Expects` is contract-syntax placeholder, not `assert`; precondition discipline lives in Error Handling pending language contracts |
| `FAQ.60` | Adapt | Same story for `Ensures`: Error Handling owns the failure-contract vocabulary, not a GSL macro |
| `GSL` | Adapt | GSL declined: standard-library equivalents and curated warnings replace GSL constructs; the `FAQ.50`–`FAQ.55` rows above record the reasoning |
| `NR.1` | Adopt | Anti-rule acknowledged: declare at first use; declarations-on-top manufactures uninitialized variables |
| `NR.2` | Adopt | Anti-rule acknowledged: early returns concentrate error handling; single-return gymnastics invent extra state |
| `NR.3` | Adapt | Anti-rule acknowledged with carve-out: exceptions stay default, status returns at module and ABI edges |
| `NR.4` | Adopt | Anti-rule acknowledged: cohesive classes group under namespaces; no one-class-per-file sprawl |
| `NR.5` | Adopt | Anti-rule acknowledged: constructors deliver ready-to-use objects; two-phase `Init()` leaks semi-constructed objects |
| `NR.6` | Adopt | Anti-rule acknowledged: RAII makes goto-exit cleanup ladders obsolete |
| `NR.7` | Adopt | Anti-rule acknowledged: protected data is hierarchy-scoped global data; keep data private |
| `Pro` | Adapt | The safety profiles map onto enforcement machinery already running — the Profiles table below records the mapping |
| `SL.1` | Adopt | Use libraries wherever possible; reinvented wheels lack reviewers, tests, and fixes |
| `SL.2` | Adopt | Standard library before third-party: most scrutinized, most portable, least supply-chain risk |
| `SL.3` | Adopt | Nothing user-defined enters namespace `std`; same reasoning as banning forward-declared `std::` types |
| `SL.4` | Adopt | Umbrella rule: use standard components within their contracts; concrete catchers live in the profile mapping below |
| `RF` | Adopt | Followed as written: a coding standard should be adapted per organization, and this registry is exactly such an adaptation — meta-commentary carrying no coding practice |
| `In.0` | Adopt | Meta-entry: understand a rule's implications before applying it — reasoned stances, justified deviations |

### Adoption Process

A rule moves from the Guidelines into daily practice through one coherent change: propose it with an ID (`F.21`, not a paraphrase of its mood), record the stance here — writing the documented difference into the companion guide when the answer is adapt — and land an enforcement catcher: a curated clang-tidy check, a compiler warning, a sanitizer run, or an explicit review item; if nothing can catch it, say so in the guide rather than pretending tooling has it covered. This index updates in the same change, so the registry never describes a directory that no longer exists. Demotion runs the same path in reverse: when an adopted rule stops earning its keep — findings all suppressed, pattern no longer occurring — remove the enforcement and drop the stance row together.

### Upkeep

Rule numbering occasionally shifts upstream: fix moved IDs during the next edit of the affected guide rather than in bulk sweeps, and give any new upstream section a row here before a guide starts citing it.

### Profiles

The Guidelines group their highest-value rules into safety profiles; we do not track conformance as such — each profile maps onto machinery that is already running:

| Guideline profile | Our equivalent enforcement |
|-------------------|----------------------------|
| Type safety | Warning set plus narrowing-conversion checks; `enum class` and explicit conversions per Expressions and Flow |
| Bounds safety | An ASan+UBSan build for out-of-bounds access; the container-invalidation table in Memory and Ownership covers what ASan misses deterministically |
| Lifetime safety | Ownership ladder plus dangling-view review rules; ASan catches the escapes that reach memory |
| Concurrency safety | A ThreadSanitizer build for threading changes; lock discipline in Concurrency |

A profile claim nobody measures is a mood, not a gate.

---

## Pre-Development Checklist

Before writing code, route the task through the relevant guide:

| Task involves | Read first |
|---------------|------------|
| Raw pointers, resource handles, container lifetime questions | [Memory and Ownership](./memory-and-ownership.md) |
| Reporting failures, designing error paths across APIs | [Error Handling](./error-handling.md) |
| New headers or files, public API surface, naming decisions | [Quality Guidelines](./quality-guidelines.md) |
| Writing, changing, or removing tests | [Testing Conventions](./testing-conventions.md) |
| Function signatures or API design at module boundaries | [Functions and Interfaces](./functions-and-interfaces.md) |
| Class design, inheritance, or object lifecycle decisions | [Classes and Hierarchies](./classes-and-hierarchies.md) |
| Templates, concepts, or generic code | [Templates and Generics](./templates-and-generics.md) |
| Threading, atomics, mutexes, or shared state | [Concurrency](./concurrency.md) |
| Expression-level correctness or control flow changes | [Expressions and Flow](./expressions-and-flow.md) |
| Optimization or hot-path work | [Performance](./performance.md) |

A change touching several rows above should skim every listed guide before starting — the expensive C++ mistakes are cross-cutting.

---

## Quality Check

Run the full gate before declaring any change complete:

- **Format-clean** — `clang-format --dry-run` reports no diffs on the sources you touched.
- **Tidy-clean** — static analysis runs on changed sources; findings are fixed or silenced with an inline justification.
- **Tests green** — the unit suite passes plain, then again under an ASan+UBSan build whenever the change touches allocation, containers, or object lifetime.
- **ThreadSanitizer** — threading changes additionally pass a TSan build.

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
