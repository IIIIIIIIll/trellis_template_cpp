---
description: Router for the C++ thinking-guide layer — symptom triggers and pre-change searches that route into the method guides
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# C++ Thinking Guides

> How to think through C++ changes: ordered steps per phase, fired by a signal
> you can observe — a shape in the diff or a symptom in a bug report — each
> naming the failure you buy by skipping it.

**Core Philosophy**: 30 minutes of thinking saves 3 hours of debugging.

---

## Overview

The [C++ guideline layer](../cpp/index.md) routes by **task type**: its
Pre-Development Checklist maps "you are touching X" to "read Y", and its
fourteen topic guides own every normative rule, one home per rule. This layer
routes by **risk shape** — what you are about to write, or what you have just
observed — into the phase guide that carries the procedure.

It covers what task-type routing misses: the change whose owning guide is not
obvious from the task description — "add a config field" can still carry an
ownership question — and the risk spanning several guides. Open your phase's
guide when a change starts; follow it when a trigger fires mid-work. The layer
holds no rules: answers live behind the link.

---

## Why Thinking Guides?

**Most C++ bugs and tech debt come from "didn't think of that"**, not from
lack of skill:

- Didn't think about which translation unit a definition lands in → ODR and
  link errors only the full build sees
- Didn't think about who owns an object after the call → a use-after-free no
  warning reliably flags
- Didn't think about what the optimizer may assume → works at `-O0`,
  misbehaves at `-O2`
- Didn't think about the throw between mutations → an object seen
  half-updated

These guides help you **ask the right questions before coding**.

---

## Available Guides

| Guide | Purpose | When to Use |
|-------|---------|-------------|
| [Design Thinking Guide](./design-thinking-guide.md) | Ownership, invariants, failure modes up front | A signature, class, header, or template changes shape |
| [Implementation Thinking Guide](./implementation-thinking-guide.md) | Lifetime, unwinding, threading, ordering, names | A body allocates, stores a view, or shares state |
| [Verification Thinking Guide](./verification-thinking-guide.md) | The evidence behind every claim of done | The change is about to be called done |
| [Pre-Implementation Checklist](./pre-implementation-checklist.md) | Search, price, and decide before the first edit | The first edit is imminent |
| [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md) | Reuse before you write | A helper, template, or constant is about to appear |
| [Bug Root Cause Thinking Guide](./bug-root-cause-thinking-guide.md) | An incident turned into a detector | A bug is fixed but not yet understood |

---

## Quick Reference: When to Use Which Guide

### When a Boundary Is About to Change Shape

- [ ] A pointer crosses a boundary with no line naming who destroys it
- [ ] Sanitizer output names a free or race created outside this diff
- [ ] A class gains state observable half-updated when a step fails

→ Read [Design Thinking Guide](./design-thinking-guide.md)

### When the Body Holds Something It Should Not

- [ ] A view or iterator outlives its statement, or dangles after growth
- [ ] `new`, `make_unique`, or container growth on a path with several exits
- [ ] Two threads reach one member, or a lock is taken while held
- [ ] An early return, `catch`, or log-and-continue skips a release
- [ ] Behavior differs between `-O0` and `-O2`, or two STL builds

→ Read [Implementation Thinking Guide](./implementation-thinking-guide.md)

### When "Done" Is a Claim Without Evidence

- [ ] Green tests over a change that allocates, threads, or stores a view
- [ ] A fix whose re-introduction no test or check would catch
- [ ] A check added without naming the bug class it defends

→ Read [Verification Thinking Guide](./verification-thinking-guide.md)

### When the First Edit Is Imminent

- [ ] You cannot cite the existing type, helper, or constant to reuse
- [ ] You have not priced a new include for every TU pulling it in
- [ ] You have not decided how failure leaves the new code

→ Read [Pre-Implementation Checklist](./pre-implementation-checklist.md)

### When Similar Code Already Exists

- [ ] A pattern about to appear a third time, or copy-paste as the fast path
- [ ] The same constant is about to land in a second translation unit

→ Read [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md)

### When a Bug Is Fixed but Not Understood

- [ ] The bug took more than 30 minutes to find
- [ ] Nothing — warning, check, sanitizer, test — flagged the class
- [ ] A bug of this shape has been fixed before

→ Read [Bug Root Cause Thinking Guide](./bug-root-cause-thinking-guide.md)

---

## Pre-Modification Rule (CRITICAL)

> **Before changing any value, name, or default other code depends on, search
> for its users first.**

```bash
# Who else uses the value you are about to change?
rg "value_to_change" -g '*.{cpp,cc,cxx,hpp,hh,h,inl,ipp}'

# Does a rule already cover it? (installed layout)
rg "(FN|CLS|TPL|ERR|MEM|QUAL|EXPR|CONC|PERF|TEST)-[0-9]+" .trellis/spec/cpp/
```

If a rule already covers the change, cite its ID; if none does, decide whether
it deserves one.

---

## C++-Specific Layers

Where failures live:

```text
Headers            widely included; layout and inline behavior are ABI
    |
    v
Translation Units  one definition rule; initialization order
    |
    v
Link               symbol visibility; ABI compatibility
    |
    v
Runtime            ownership; invalidation; races; unwinding
```

- **Headers → translation units**: include cost per includer; macro state
  deciding what a header means; inline behavior under old binaries.
- **Translation unit → translation unit**: ODR violations from header
  definitions; initialization order; layout disagreement across TUs.
- **Translation unit → link**: missing or hidden symbols; ABI drift between
  rebuilt and deployed objects; mixed toolchains.
- **Link → runtime**: two owners releasing one object; a view outliving its
  container; a race tests never interleave; a throw from a destructor.

---

## Cross-Cutting Interactions

Each span crosses phases; no single guide owns the risk.

| Span | Classic signature | Read first |
|------|-------------------|------------|
| Ownership × concurrency: freeing on another thread; lock lifetime versus object lifetime | LSan leak dump pointing at both ends of a mutual `shared_ptr` cycle; use-after-free from a queue holding the last reference | [Concurrency](../cpp/implement/concurrency.md) + [Ownership Design](../cpp/design/ownership-design.md) + [Memory Discipline](../cpp/implement/memory-discipline.md) |
| Exceptions × templates: a generic's failure contract instantiates at every use site | `noexcept` move falling back to a copying move during container growth; the throw surfacing at a use site that cannot handle it | [Error Contracts](../cpp/design/error-contracts.md) + [Templates and Generics](../cpp/design/templates-and-generics.md) |
| Performance × correctness: UB that happens to be fast | The uninitialized read that "works" at `-O0` and misbehaves at `-O2`; the dangling reference read inside a hot loop | [Performance](../cpp/implement/performance.md) + [Expressions and Flow](../cpp/implement/expressions-and-flow.md) + [Memory Discipline](../cpp/implement/memory-discipline.md) |
| Headers × evolution: changing a header recompiles the world; changing layout breaks binaries | The inline function whose behavior changed for binaries built against the old header | [Headers and Dependencies](../cpp/design/headers-and-dependencies.md) |

---

## Core Principles

1. **Search Before Write** — find the existing type, helper, constant, and
   rule before adding one; the duplicate is a bug waiting to happen.
2. **Name the Failure in the Signature** — a function that can fail says so
   in its type and name, not in a comment.
3. **One Owner per Object** — every object crossing a boundary gets one line
   naming its destroyer; no line, no finished design.
4. **Detector per Bug Class** — every mistake class a change invites has a
   check, warning, sanitizer, or test behind it.
5. **Learn From Bugs** — an incident ends with a detector and a recorded
   lesson; the incident records live in `big-question/` beside this layer.

---

**Language**: All documentation should be written in **English**.
