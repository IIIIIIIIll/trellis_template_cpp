# Static Initialization Order Fiasco

*Format exemplar for a canonical C++ incident class — not project history.*

> A global's constructor reads another translation unit's global before that
> global's dynamic initializer has run — the reader sees zero-initialized
> storage, and whether the value is right depends on link order.

## Problem

The program starts against an empty registry, a null logger, or a
default-constructed config. The read happens inside a namespace-scope
object's constructor, so it shows before `main` runs and looks like "the
configuration was ignored", not a crash.

Signatures:

- Correct in one binary (a test harness, a single-TU build) and wrong in
  another (the full link, a different target) with no source difference.
- The symptom moves — or disappears — when a translation unit is added,
  removed, or reordered in the build.
- The reader's value is not garbage but *empty*: zero-initialization ran
  first, so a null pointer or empty container looks like a plausible "not
  configured" state.

## Root Cause

Namespace-scope objects with static storage duration initialize in two
phases: static (zero or constant) initialization, then dynamic
initialization, which runs constructors. Within a translation unit dynamic
initialization follows declaration order; **across translation units the
order is unspecified** — link order and the toolchain decide.

A global whose constructor calls into another global can therefore read
storage that has only been zero-initialized — for a class type a valid,
empty object, not broken memory. That is why the failure surfaces as missing
state rather than as a fault in a debugger.

Destruction mirrors the trap: reverse order of the completion of
construction, same cross-TU uncertainty, so a static destructor can read
another translation unit's already-destroyed object.

## Solution

Remove the ordering question instead of trying to pin it:

- **Constant-initialize where possible.** A `constexpr` object — `inline
  constexpr` on C++17 — is initialized before any dynamic initialization, so
  no reader can observe it uninitialized.
- **Use function-local statics for order-dependent state.** A function-local
  static initializes on first control passing through its declaration
  (thread-safe since C++11), so it exists before anyone reads it; the
  accessor becomes the ordering mechanism.
- **Keep the dependency visible.** If one global must be built from another,
  construct it in the same translation unit with declaration order stating
  the dependency — better, pass the dependency in.
- **C++20:** `constinit` makes compile-time initialization a requirement and
  turns the order bug into a compile error.

Topic layer: [Headers and Dependencies](../cpp/design/headers-and-dependencies.md)
owns cross-TU initialization order and the namespace-scope constants rule;
[Functions and Interfaces](../cpp/design/functions-and-interfaces.md) owns
the global and accessor rules;
[Expressions and Flow](../cpp/implement/expressions-and-flow.md) owns the
initialization discipline these objects violate.

## Key Takeaways

- Cross-TU initialization order is unspecified: "it works on my machine" is
  a link-order accident, not a contract.
- A global whose initializer reads another global is a design smell — pass
  the dependency, or own the ordering inside one accessor.
- Zero-initialized is not initialized: look for the plausible-empty value,
  not a crash.
- Destructors reverse the same unspecified order; shutdown needs the same
  care as startup.

## Read first

- [Headers and Dependencies](../cpp/design/headers-and-dependencies.md) —
  cross-TU initialization order.
- [Functions and Interfaces](../cpp/design/functions-and-interfaces.md) —
  one global's initializer never reads another.
- [Expressions and Flow](../cpp/implement/expressions-and-flow.md) —
  initialization discipline.

---

**Language**: All documentation should be written in **English**.
