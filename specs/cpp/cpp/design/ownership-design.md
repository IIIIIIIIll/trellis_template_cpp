---
description: Ownership ladder and smart-pointer conventions at API edges
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Ownership Design

> The ownership ladder and smart-pointer signature conventions that decide, at every API boundary, who owns what and how lifetime is transferred.

---

## Overview

Ownership is decided when an interface is written — in the types of its parameters, returns, and members — not reconstructed from a sanitizer report afterwards. This document fixes the ladder that ranks every owning and borrowing tool: `unique_ptr` is the default owner, raw pointers and views borrow visibly, `shared_ptr` requires a written lifetime-sharing justification, and owning raw `new`/`delete` is forbidden outright. Signatures broadcast the same decision: taking a smart pointer is a lifetime contract with the caller, so every smart-pointer parameter kind carries an explicit meaning. When a signature names its owner, lifetime bugs surface as review findings instead of production crashes.

---

## The Ownership Ladder

Caught by: ASan (use-after-free and double-free from broken ownership), LSan (leaked cycles that `weak_ptr` should have broken), TSan (data races from undeclared shared owners), review for shared-ptr sprawl.

Default strength: hard.

| Rank | Tool | Use when | Notes |
|------|------|----------|-------|
| **MEM-5** Default owner | `std::unique_ptr<T>` | Single owner, dynamic lifetime | Zero overhead; the factory return type of choice |
| **MEM-6** Borrowed view | Raw `T*`, `T&`, `std::span` (C++20; C++14: `T*` + size), `std::string_view` (C++17; C++14: `const std::string&`) | Access without ownership | Must not dangle; the caller guarantees outliving |
| **MEM-7** Shared owner | `std::shared_ptr<T>` | Lifetime genuinely shared, owner unknowable statically | Requires a written justification; cycles go through `weak_ptr` |
| **MEM-8** Forbidden | Owning raw `new`/`delete`, mixing `malloc`/`free` | Never | Blocked in review |

- **MEM-9.** The rungs are exhaustive by construction (`R.20`): ownership is spelled in types, and assigning `new`'s result to a raw pointer strands the object outside the ladder. Raw pointers sit on Borrowed view by definition (`R.3`) — a `T*` denotes exactly one borrowed object (`R.2`); arrays decay and lose their length, so sequences travel as a pointer-plus-size pair (**C++17:** `string_view` for text; **C++20:** `std::span` for element ranges). On the owning side, `new T[n]` is Forbidden like every other naked allocation; a genuine need for an uninitialized heap array is spelled `std::make_unique<T[]>(n)`, and constructed elements default to containers.

**MEM-10.** Owning raw pointers occupy Forbidden outright, which is why this project needs no `owner<T*>` annotation: nothing legal remains for it to mark. References borrow too (`R.4`): a `T&` is a present, non-owning view with no null state, and binding one to `*new` is an owning raw pointer in disguise that dies in review like any Forbidden-rung allocation.

**MEM-11.** `malloc`/`free` share the Forbidden rung (`R.10`) — they construct and destroy nothing (a `malloc`-ed record's `std::string` member is just a string-sized bag of bits) and mixing the verb pairs is undefined behavior; `nothrow` new stays as the fallback where exceptions truly cannot fly.

**MEM-12.** A non-`const` global is an undeclared shared owner and data-race candidate (`R.6`): constants are `constexpr`, mutable state gets explicit ownership plus [Concurrency](../implement/concurrency.md)'s locking story, and init-order traps follow [Headers and Dependencies](./headers-and-dependencies.md)' accessor-function pattern.

Rules:

- **MEM-13.** Create with `std::make_unique` / `std::make_shared`, never `unique_ptr<T>(new T(...))` (`R.22`, `R.23`) — one spelling instead of repeating the type name, exception safety, and one allocation instead of two for shared. The root cause is `R.13`: two allocations in one statement can interleave under unspecified evaluation order and leak when the second constructor throws; factories remove the naked allocation, making the hazard unreachable.
- **MEM-14.** "Maybe null, not owning" parameters take `T*`; "present, not owning" parameters take `T&`. Pointer out-parameters are forbidden; return values instead.
- **MEM-15.** A `shared_ptr` in a signature is a design decision, not convenience. Copying one costs an atomic operation and freezes object lifetime; justify it in a comment or downgrade to `unique_ptr`/references — `R.21`: `unique_ptr` outranks `shared_ptr` for deterministic destruction and zero refcount traffic.
- **MEM-16.** Observing a shared object without extending its life takes `std::weak_ptr` and locks — mandatory for back-edges in parent/child graphs, caches, and observer lists.
- **MEM-17.** Non-`std` smart pointers join the ladder through the `std` pattern (`R.31`): copyable counts as shared-like, move-only as unique-like — every smart-pointer signature rule below applies to them unchanged.
- **MEM-18.** Custom-deleter owners: `std::make_unique` has no deleter-taking form (`R.23` fixes only the default-deleter spelling), so an unwrapped resource with non-default cleanup writes its owner out in full at the acquisition site — `std::unique_ptr<Handle, Deleter>{acquire(...), release}` — and never parks the raw handle in between. A deleter that never runs is LeakSanitizer's classic leak signature.
- **MEM-19.** `make_shared` carve-outs (`R.22`): the fused allocation keeps the object's bytes alive while any `weak_ptr` exists — a mandated `weak_ptr` back-edge or cache entry over a large object pays full memory after the object is logically dead — and `make_shared` cannot take a custom deleter. When either bite lands, write the deliberate exception with a comment saying why: `std::shared_ptr<T>{new T{...}}` separates object from control block so weak observers stop pinning the bytes, and `std::shared_ptr<Handle>{acquire(...), release}` carries the deleter. No checker sees the retained bytes — the footprint is a review item — while the compiler rejects `make_shared` with a deleter outright.

---

## Smart Pointers in Signatures

Caught by: review — no checker reliably distinguishes takeover from borrow, so treat smart-pointer parameter types as reviewed API surface.

Default strength: hard.

**MEM-31.** Take smart pointers as parameters only to explicitly express lifetime semantics (`R.30`): readers take Borrowed views (`widget*`, `widget&`; **C++20:** `std::span`), sinks take by-value owners, and a by-value `shared_ptr` parameter nobody stores is an atomic no-op billed to every caller.

| Parameter | Contract | Notes |
|-----------|----------|-------|
| **MEM-32** `unique_ptr<widget>` by value | Callee assumes ownership — stores or consumes the widget | Anything less takes `widget*` or `widget&` (`R.32`) |
| **MEM-33** `unique_ptr<widget>&` | Callee reseats the slot — assigns or calls `reset()` on some path | Never reassigned, it is a forbidden pointer out-parameter wearing a template (`R.33`) |
| **MEM-34** `shared_ptr<widget>` by value | Callee joins the owner set — stores a copy, ideally moved | Otherwise every call pays atomic refcount traffic for nothing; the Shared-owner justification applies to signatures, not just members (`R.34`) |
| **MEM-35** `shared_ptr<widget>&` | Callee might reseat the pointer | Same contract as the unique case: no assignment or reset anywhere, no parameter (`R.35`) |
| **MEM-36** `const shared_ptr<widget>&` | Reserved for conditionally retaining a count | See the deviation below |

Deviation from `R.36`: upstream offers `const shared_ptr<widget>&`, hedged with warnings, for the "might retain a refcount" case; the ladder resolves the hedge. Definite sharers take the `shared_ptr` by value, definite readers take a plain view, and the const-lvalue-reference spelling survives only for genuinely conditional retention.

**MEM-37.** Never pass a pointer or reference obtained from an aliased smart pointer down a call chain (`R.37`): resetting through another alias mid-call destroys the object under the borrowed reference. Pin the subtree first with a cheap local strong copy, then extract the view.

---

## Quality Check

Gates before merging ownership work: format-clean (`clang-format --dry-run`) and tidy-clean on changed sources, and the unit suite green under an ASan+UBSan build — allocation and lifetime are exactly what sanitizers exist to catch.

Before merging ownership design, confirm:

- [ ] Every new `shared_ptr` carries a lifetime-sharing justification

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
