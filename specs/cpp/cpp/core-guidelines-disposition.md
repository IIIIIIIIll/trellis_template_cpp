# Core Guidelines Disposition

> Where this project stands on the ISO C++ Core Guidelines — which sections
> we adopt, which we adapt, and how deviations, adoption, and upkeep are
> governed.

---

## Overview

The [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) are advice rather than law; instead of re-litigating philosophy inside each topic guide, this document records the project's stance toward every major Guidelines section in one place and routes it to the guide that operationalizes it. Rule IDs such as `F.21` or `ES.20` appear throughout these guides as cross-reference anchors only — every explanation is our own paraphrase, and neither upstream prose nor examples are copied. A stance recorded here is a contract with reviewers: **adapt** means a written, reasoned local difference exists — in the owning guide, or in the disposition itself when no guide owns the rule — not that the rule was quietly ignored. Questions about adopting or deviating from a specific rule resolve against the tables below. Stances use the fixed vocabulary defined in [the guidelines index](./index.md) (Stance Vocabulary): *Adopt*, *Adapt*, *Adopt selectively*, *Covered elsewhere*.

---

## Disposition by Section

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

---

## Recording a Deviation

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

---

## Residual Sections Ledger

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
| `FAQ.50`, `FAQ.51`, `FAQ.52`, `FAQ.54` | Adapt | GSL declined: `std` equivalents plus curated warnings replace it; nothing vendors or assumes GSL, which was never standardized |
| `FAQ.55` | Adopt | View taxonomy adopted directly: `std::string_view` for read-only views (C++17), `std::span` for read-write (C++20) |
| `FAQ.59` | Adopt | `Expects` is contract-syntax placeholder, not `assert`; precondition discipline lives in Error Handling pending language contracts |
| `FAQ.60` | Adapt | Same story for `Ensures`: Error Handling owns the failure-contract vocabulary, not a GSL macro |
| `GSL` | Adapt | GSL declined: standard-library equivalents and curated warnings replace GSL constructs; the merged `FAQ.50`/`FAQ.51`/`FAQ.52`/`FAQ.54` row above records the reasoning |
| `NR.1` | Adopt | Anti-rule acknowledged: declare at first use; declarations-on-top manufactures uninitialized variables |
| `NR.2` | Adopt | Anti-rule acknowledged: early returns concentrate error handling; single-return gymnastics invent extra state |
| `NR.3` | Adapt | Anti-rule acknowledged with carve-out: exceptions stay default, status returns at module and ABI edges |
| `NR.4` | Adopt | Anti-rule acknowledged: cohesive classes group under namespaces; no one-class-per-file sprawl |
| `NR.5` | Adopt | Anti-rule acknowledged: constructors deliver ready-to-use objects; two-phase `Init()` leaks semi-constructed objects |
| `NR.6` | Adopt | Anti-rule acknowledged: RAII makes goto-exit cleanup ladders obsolete |
| `NR.7` | Adopt | Anti-rule acknowledged: protected data is hierarchy-scoped global data; keep data private |
| `Pro` | Adapt | The safety profiles map onto the enforcement machinery the Quality Check in [the guidelines index](./index.md) prescribes — the Profiles table below records the mapping |
| `SL.1` | Adopt | Use libraries wherever possible; reinvented wheels lack reviewers, tests, and fixes — [Third-Party Dependencies](./quality-guidelines.md) in Quality Guidelines owns the vetting |
| `SL.2` | Adopt | Standard library before third-party: most scrutinized, most portable, least supply-chain risk — the ordering rule lives in [Third-Party Dependencies](./quality-guidelines.md) |
| `SL.3` | Adopt | Nothing user-defined enters namespace `std`; same reasoning as banning forward-declared `std::` types |
| `SL.4` | Adopt | Umbrella rule: use standard components within their contracts; concrete catchers live in the profile mapping below |
| `RF` | Adopt | Followed as written: a coding standard should be adapted per organization, and this registry is exactly such an adaptation — meta-commentary carrying no coding practice |
| `In.0` | Adopt | Meta-entry: understand a rule's implications before applying it — reasoned stances, justified deviations |

---

## Adoption Process

A rule moves from the Guidelines into daily practice through one coherent change: propose it with an ID (`F.21`, not a paraphrase of its mood), record the stance here — writing the documented difference into the owning guide, or into the disposition itself when no guide owns the rule, when the answer is adapt — and land an enforcement catcher: a curated clang-tidy check, a compiler warning, a sanitizer run, or an explicit review item; if nothing can catch it, say so in the guide rather than pretending tooling has it covered. The routing index ([index.md](./index.md)) updates in the same change, so the registry never describes a directory that no longer exists. Demotion runs the same path in reverse: when an adopted rule stops earning its keep — findings all suppressed, pattern no longer occurring — remove the enforcement and amend the stance row together; drop the row outright only when it is a residual-ledger entry, since every one of the fourteen sections must keep its row.

---

## Upkeep

Rule numbering occasionally shifts upstream: fix moved IDs during the next edit of the affected guide rather than in bulk sweeps, and give any new upstream section a row here before a guide starts citing it.

---

## Profiles

The Guidelines group their highest-value rules into safety profiles; we do not track conformance as such — each profile maps onto machinery the Quality Check in [the guidelines index](./index.md) prescribes, and every row names the gate that runs it:

| Guideline profile | Trigger (Quality Check) | Our equivalent enforcement |
|-------------------|-------------------------|----------------------------|
| Type safety | Tidy-clean: the curated clang-tidy checks, including narrowing-conversion checks, run on changed sources | `enum class` and explicit conversions per Expressions and Flow |
| Bounds safety | Tests green: an ASan+UBSan build whenever the change touches allocation, containers, or object lifetime | Out-of-bounds access; the container-invalidation table in Memory and Ownership covers what ASan misses deterministically |
| Lifetime safety | Tests green: the same ASan+UBSan condition on lifetime-touching changes | Ownership ladder plus dangling-view review rules; ASan catches the escapes that reach memory |
| Concurrency safety | ThreadSanitizer: threading changes additionally pass a TSan build | Lock discipline in Concurrency |

A profile claim nobody measures is a mood, not a gate.

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
