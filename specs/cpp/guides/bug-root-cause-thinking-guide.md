---
description: Bug root cause thinking guide — reproduce and minimize, classify to the owning guide, name the detector, land the test, record the incident
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Bug Root Cause Thinking Guide

> Making the symptom disappear is a hypothesis, not a diagnosis. What
> follows the repair is the diagnosis: prove the cause, find out why nothing
> caught it, and make the same mistake harder next time.

---

## Reproduce Then Minimize

A reproduction you can run on demand turns a guess into a fix; the minimized
version reveals the class. Shrink it to fewest includes, one function, the
smallest input, the narrowest interleaving: a crash in ten lines is a
lifetime or a precondition; one that needs the whole program is state
ordering or a race.

A case whose behavior shifts between `-O0` and `-O2` is a UB signature:
treat it as undefined behavior until ruled out — `NDEBUG`-gated asserts and
timing differences also flip with the build, so exclude those first, but
"the compiler is wrong" is not a root cause. Depth:
[Expressions and Flow](../cpp/implement/expressions-and-flow.md);
[Memory Discipline](../cpp/implement/memory-discipline.md).

## Classify the Root Cause

Name the class before naming the fix; the class names its owning guide:

| Class you found | Owning guide |
|-----------------|--------------|
| Ownership and lifetime — two deleters, a leak | [Ownership Design](../cpp/design/ownership-design.md); [Memory Discipline](../cpp/implement/memory-discipline.md) |
| Invalidation window — a view outliving its owner | [Functions and Interfaces](../cpp/design/functions-and-interfaces.md) |
| Failure path — a swallowed error, a missing rollback | [Error Propagation](../cpp/implement/error-propagation.md); [Error Contracts](../cpp/design/error-contracts.md) |
| Guarding and lock order — a race, a deadlock | [Concurrency](../cpp/implement/concurrency.md) |
| Undefined behavior — works at `-O0`, breaks at `-O2` | [Expressions and Flow](../cpp/implement/expressions-and-flow.md) |
| Build boundary — ODR, layout, initialization order | [Headers and Dependencies](../cpp/design/headers-and-dependencies.md) |
| Class invariant — a half-updated object | [Classes and Hierarchies](../cpp/design/classes-and-hierarchies.md) |
| Template instantiation — an error blamed on the caller | [Templates and Generics](../cpp/design/templates-and-generics.md) |

A class that fits none of these is a finding about the rule set: the durable
fix may be a rule, not a patch.

## Name the Missing Detector

Ask what should have caught this before a user did, and answer with a
mechanism: a warning, a clang-tidy check, a sanitizer with its interleaving,
an assertion, or a test that runs. If nothing catches it, the gap is the
defect — name the check that closes it. Depth:
[Static Analysis](../cpp/verification/static-analysis.md).

## Add the Test

The minimized reproduction seeds the regression test. It must fail on the
unfixed code for the reason the classifier named — a test that passes before
the fix tests the wrong thing — and assert the consequence, not the internal
sequence. Depth:
[Testing Conventions](../cpp/verification/testing-conventions.md).

## Record the Incident

The step that changes the future: write the incident down in the
[big-question/](../big-question/index.md) directory — what happened, the
root-cause class, the fix, the takeaway that lets the next reader recognize
the shape. Its index is the entry point; a fresh bug matching an existing
entry is a signal to re-read it before fixing, and a class no rule owns yet
is how a patch becomes a rule.

## Before Calling the Bug Fixed

- [ ] A reproduction runs on demand, minimized
- [ ] The fix names a root-cause class, not a symptom
- [ ] The class points at its owning guide, or the gap is named
- [ ] The detector that should have caught it is named, or the absence noted
- [ ] The regression test fails unfixed, for the reason claimed
- [ ] The incident is filed where the next reader finds it

---

**Language**: All documentation should be written in **English**.
