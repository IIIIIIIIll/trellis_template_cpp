---
description: The verification phase as an ordered procedure — a detector for each bug class, sanitizer and interleaving coverage, a regression test that fails when the change breaks
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Verification Thinking Guide

> Before the change is called done, answer for the risk it introduced:
> which detector catches each mistake, which sanitizer sees it, and which
> test fails when the behavior breaks.

---

## Why This Phase

Compiling and passing tests prove less than they appear to: a clean build
says nothing about a lifetime bug the sanitizer would have caught, and a
green test run says nothing about an interleaving it never produced. This
phase exists to convert the diff's risks into named detectors — a warning,
a clang-tidy check, a sanitizer gate with its trigger, a regression test
whose failure mode is understood.

The price of skipping it is deferred, not avoided: the same bug class
returns next quarter because nothing flags it, a racy program ships behind
green tests, and the next refactor reintroduces a fixed bug because no test
existed to fail. The rows below are short; the cost of the failure column
is not.

The phase is finished when every row has an answer you could show someone,
not when the suite is green. An unanswered row is allowed — it is a risk
being accepted on purpose — but it has to be written down as such, or the
silence will read as coverage later.

---

## The Procedure

| # | Step | Fires when you see | Canonical failure | Read first |
|---|------|--------------------|-------------------|------------|
| 1 | For every mistake this diff invites, name the detector that catches it — or add the check or the review gate. | A diff whose bug class has no entry in the curated clang-tidy/compiler-warning set | The class re-offending silently next quarter | [Static Analysis](../cpp/verification/static-analysis.md) |
| 2 | Say which sanitizer catches it, and which interleaving triggers it. If no interleaving does, the design rule was the only defense. | Threading, allocation, or lifetime touched by the diff | Green tests, racy program | [Testing Conventions](../cpp/verification/testing-conventions.md); sanitizer gates in the [layer index](../cpp/index.md) |
| 3 | Name the test that fails when this breaks, and what it fails for. | A bug fix without a regression test | Re-offense after the next refactor | [Testing Conventions](../cpp/verification/testing-conventions.md) |

Each row ends in a concrete artifact, never an assurance: a check name, a
sanitizer invocation plus the interleaving it needs, a test whose failure
mode you can describe out loud. If a row resolves to "we would notice it in
production", that is a real answer too — record it where the change is
reviewed, so the defense reads as chosen rather than forgotten.

When a row has no answer and no honest way to get one, the gap is usually
upstream: a lifetime the design never fixed, or a failure path the body
never completed. Fix it there and the row answers itself — a detector bolted
onto an unclear interface documents the ambiguity instead of removing it.

---

## Before Leaving This Phase

- [ ] Does every mistake this diff invites have a detector that catches it, or a review gate that will?
- [ ] Is there a sanitizer and a named interleaving for the threading, allocation, or lifetime risk — or a design rule standing in for both?
- [ ] Is there a test that fails when this change breaks, and does the failure mean what you think it means?

---

**Language**: All documentation should be written in **English**.
