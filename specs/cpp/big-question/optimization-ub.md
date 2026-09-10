# Optimization-Only Undefined Behavior

*Format exemplar for a canonical C++ incident class — not project history.*

> The debug build passes every test; the optimized build misbehaves — or the
> behavior changes with a compiler or standard-library upgrade. The source
> has undefined behavior, and the optimizer is entitled to use it.

## Problem

The classic report: "It works at `-O0`." The release build skips a bounds
check or call, assumes a value is invariant, or deletes a loop that should
have terminated — often in code nobody touched.

Signatures:

- Behavior differs between `-O0` and `-O2` with the same source, compiler,
  and input — the single most reliable UB signature there is, once the
  build-flipping confounders (`NDEBUG`-gated asserts, timing) are excluded.
- Behavior changed after a compiler or standard-library upgrade; the
  previous build "was fine".
- Debug and sanitizer builds stay green while the optimized build is wrong —
  the sanitized run misses the path, or no sanitizer is in the loop.

## Root Cause

Undefined behavior is not "unspecified but reasonable": the language imposes
no requirements at all. Optimizers assume the program contains none — signed
overflow cannot happen, shifts are in range, pointers point at live objects,
uninitialized values are never read — so a branch guarding a UB case is
dead, a value is provably constant, and a computation can be moved, folded,
or deleted.

At `-O0` that reasoning does not run, so the UB has the *appearance* of
working: the machine does the obvious thing with the bits. The optimized
build compiles a different program — not a compiler bug, but a source that
left the language's contract first. Typical sources: uninitialized reads,
signed overflow and out-of-range shifts, out-of-bounds indexing, invalid or
dangling pointers, and violations of container or iterator requirements.

## Solution

- **Classify before fixing.** `-O0`-versus-`-O2` divergence is a UB
  signature, not a compiler defect: reproduce, minimize, find the owning
  rule — do not hunt optimizations.
- **Put the detectors in the pipeline.** The unit suite runs under ASan and
  UBSan failing hard, TSan for threading changes, plus a debug-mode or
  hardened standard library where container violations must become
  deterministic.
- **Fix the contract, not the symptom.** Initialize the object, keep
  arithmetic inside its domain, bound the index, respect the lifetime.
  `volatile`, compiler barriers, and "optimization workarounds" hide the
  divergence while keeping the UB.
- **Re-verify in the build that failed.** The regression test must fail on
  the unfixed code and pass after the fix — proven in the optimized build.

Topic layer: [Expressions and Flow](../cpp/implement/expressions-and-flow.md)
owns the initialization, conversion, shift, and evaluation-order rules and
the lifetime traps;
[Testing Conventions](../cpp/verification/testing-conventions.md) owns the
sanitizer pairing and the unit-suite posture;
[Performance](../cpp/implement/performance.md) owns the measurement
discipline — which build answers which question.

## Key Takeaways

- Undefined behavior that happens to be fast is still undefined behavior; a
  green test suite is not evidence of a well-defined program.
- The optimizer is not malfunctioning when it exploits UB — the source is
  out of contract, and divergence across builds is a signature to diagnose,
  never a flake to retry.
- There is no optimization workaround for UB; the fix is always at the
  source.
- Sanitizer evidence and release-build numbers answer different questions:
  keep both.

## Read first

- [Performance](../cpp/implement/performance.md) — measurement before
  change; which build answers which question.
- [Expressions and Flow](../cpp/implement/expressions-and-flow.md) — the
  expression-level rules whose violation this class is.
- [Testing Conventions](../cpp/verification/testing-conventions.md) —
  sanitizer gates for the unit suite.

---

**Language**: All documentation should be written in **English**.
