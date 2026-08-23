# Expressions and Flow

> Expression-level discipline for C++ in this project: initialization that cannot fail, `auto` where it helps, casts that announce themselves, consistent signedness, and control flow that stays flat enough to review.

---

## Overview

Most C++ defects below the ownership level are expression-shaped: a value read before it was written, a narrowing conversion that silently ate a counter, a C-style cast that quietly stripped `const` on its way to corruption. This document fixes the shape of individual expressions and statements so the compiler catches mistakes instead of absorbing them.

Baseline is C++17; deviations for C++20/23 are noted inline. Ownership and lifetime questions live in [Memory and Ownership](./memory-and-ownership.md); failure paths in [Error Handling](./error-handling.md).

---

## Initialization Discipline

Every object holds a value from the moment it is created (`ES.20`). Declaring first and assigning later is how uninitialized reads survive refactors: someone inserts an early return between the declaration and the assignment.

| Situation | Form |
|-----------|------|
| Any object, at declaration | Initialize immediately (`ES.20`) |
| Value known only mid-function | Declare at that point, initialized (`ES.22`) |
| Object never reassigned afterward | Mark it `const`; compile-time-known values are `constexpr` (`ES.25`) |
| Loop-local helper | Declare inside the loop body, smallest scope (`ES.74`) |

Wrong:

```cpp
Status process(const Request& req) {
    Result out;                     // default-constructed into an unknown state
    if (!authorize(req)) {
        return Status::Denied;
    }
    out = evaluate(req);            // gap between birth and first value
    return out.status();
}
```

Right:

```cpp
Status process(const Request& req) {
    if (!authorize(req)) {
        return Status::Denied;
    }
    const Result out = evaluate(req);
    return out.status();
}
```

Class members follow the same rule twice: in-class initializers for every member with a sensible default, and a constructor member-initializer list for everything else. Constructor bodies that assign members are initialization theater — by the time the body runs, members were already constructed.

### Braces Prevent Narrowing

Prefer brace initialization (`ES.23`): the `{}` form turns a lossy conversion into a compile error instead of a silent truncation (`ES.46`).

```cpp
// Wrong: compiles, loses data
int samples = collect();
uint8_t quantized = samples;        // silent truncation
double ratio = 3 / 4;               // integer division happens first: 0.0

// Right: the compiler refuses
int samples = collect();
uint8_t quantized{samples};         // error: narrowing
double ratio = 3.0 / 4.0;           // intent stated in types, not hoped for in results
```

Use `=` where the type is spelled out and no conversion risk exists (`std::string name = req.user();`); use `{}` wherever a conversion could bite — integral-to-smaller-integral and floating-to-integral above all.

### Member Initializer Lists Follow Declaration Order

Members initialize in **declaration order**, not list order (`C.47`). Reordering the list to look tidy initializes members in an order their dependencies do not expect, and `-Wreorder` flags it.

```cpp
// Wrong: list order lies about execution order
class Window {
public:
    explicit Window(Size s)
        : area_{static_cast<int>(s.width()) * static_cast<int>(s.height())},
          width_(s.width()),
          height_(s.height()) {}
private:
    int area_;       // declared FIRST, so it initializes FIRST -- reads width_/height_
    int width_;
    int height_;
};
```

Right: declare members in dependency order and mirror that order in every constructor's initializer list.

---

## `auto`: When It Helps, When It Hides

`auto` removes redundancy, not information (`ES.11`). Use it when the initializer already states the type; spell the type when the type *is* the information.

| Use `auto` | Spell the type |
|------------|----------------|
| Iterators: `auto it = map.find(key);` | Numeric contracts: `int64_t offset`, `size_t count` |
| Range-for over an obviously typed sequence | Anything crossing an API boundary (parameters, returns) |
| Calls whose name carries the type: `auto conn = open_connection(cfg);` | Domain-typed values (`Meters`, `SampleRate`) |
| Lambda parameters and expression templates nobody could spell | Conversions you want checked — `auto` hides truncation |

```cpp
// Wrong: the reader must resolve the whole call chain to know what `r` is
auto r = service.rate(id);

// Right: the contract is visible at the call site
SampleRate r = service.rate(id);
```

Public function signatures spell their return types; a signature is documentation, and `auto` deletes the relevant line.

---

## Cast Discipline

Casts are declarations of distrust toward the type system, so they are rare, precise, and searchable (`ES.48`).

| Intent | Tool |
|--------|------|
| Deliberate arithmetic conversion | `static_cast` |
| Polymorphic downcast | `dynamic_cast`, result checked |
| Bit-level reinterpretation of trivially copyable bytes | `memcpy` (C++17), `std::bit_cast` (C++20) |
| Strip `const` to mutate | Forbidden (`ES.50`) |
| Pointer reinterpretation | `reinterpret_cast` plus a review comment justifying alignment and lifetime |

Forbidden outright: C-style casts `(T)x`. A C-style cast asks the compiler to silently pick the cheapest of five different operations — including `const_cast` and `reinterpret_cast` — which is exactly why it must never appear (`ES.49`).

```cpp
// Wrong: what does this even do? (strips const AND mutates -- UB if the object is truly const)
void tick(const Frame* frame) {
    auto* mutable_frame = (Frame*)frame;
    mutable_frame->sequence += 1;
}

// Right: nothing here needs a cast; fix the const contract instead
void tick(Frame* frame) {
    frame->sequence += 1;
}
```

When a `reinterpret_cast` survives review, the comment above it states why the pointed-to memory genuinely holds the target type, who guarantees alignment, and what bounds the lifetime. A bare one is treated as a defect.

---

## Signedness Consistency

An expression commits to one signedness and keeps it (`ES.100`): signed types do arithmetic (`ES.102`), unsigned types do bit manipulation (`ES.101`).

The classic failure is choosing unsigned "because counts are never negative" (`ES.106`):

```cpp
// Wrong: unsigned wraps instead of going negative
std::vector<Item> pending = remaining();
for (std::size_t i = pending.size() - 1; i >= 0; --i) {   // empty vector: wraps, UB
    ship(pending[i]);
}

// Right: walk backwards with reverse iterators, or use signed indices
for (auto it = pending.rbegin(); it != pending.rend(); ++it) {
    ship(*it);
}
```

Rules:

1. Indices, counts, offsets, and differences are signed — `int64_t` unless profiling says narrower. Subscripts gain nothing from being unsigned (`ES.107`).
2. Bit masks, flags, and hashes are `uint32_t`/`uint64_t` (`ES.101`).
3. Mixed-sign comparisons get fixed at the source: restructure the condition or convert the value with a genuinely bounded domain. Never sprinkle casts until the warning disappears.
4. Buffer math and length fields near limits carry explicit precondition checks (`ES.103`, `ES.104`); wraparound is a bug, not a feature.

Caught by: the sign-comparison and sign-conversion warnings enabled by default in the build; suppressing one requires a comment naming the reason.

---

## Control Flow Shape

Functions read top-down: guard clauses first, main path last. Early returns are the default; single-exit is not a goal — one extra `return` that removes three indent levels is a win. The real budget is nesting depth: past two levels of compound conditionals, extract predicates (`ES.28`) and delete cleverness (`ES.70`).

```cpp
// Wrong: the happy path is buried; every branch doubles the state space
bool submit(const Order& order) {
    bool accepted = false;
    if (order.valid()) {
        if (!order.is_duplicate()) {
            if (inventory.reserve(order.lines())) {
                ledger.commit(order);
                accepted = true;
            } else {
                metrics.count("out_of_stock");
            }
        } else {
            metrics.count("duplicate");
        }
    }
    return accepted;
}

// Right: guards reject early; the main path stays at column zero
bool submit(const Order& order) {
    if (!order.valid()) return false;
    if (order.is_duplicate()) { metrics.count("duplicate"); return false; }
    if (!inventory.reserve(order.lines())) { metrics.count("out_of_stock"); return false; }
    ledger.commit(order);
    return true;
}
```

Loop and branch rules:

1. No `goto` (`ES.76`). No `do/while` unless it removes worse duplication between the prologue and the tail (`ES.75`) — in practice, almost never.
2. Every non-empty `case` ends with `break` or an obvious `return`; an intentional fallthrough is stated in a comment and reviewed (`ES.78`).
3. Redundant boolean dressing is noise: `if (found)`, not `if (found == true)` (`ES.87`). Conditions contain no assignments and no hidden side effects.
4. Range-based `for` is the default loop. Never mutate a container's structure while iterating it — reallocation invalidates the iterator — and never bind a range-for directly to a temporary. The invalidation table lives in [Memory and Ownership](./memory-and-ownership.md).

```cpp
// Wrong: the temporary dies before the first iteration completes
for (const Row& row : make_rows()) { consume(row); }

// Right: own the range for the duration of the iteration
const std::vector<Row> rows = make_rows();
for (const Row& row : rows) { consume(row); }
```

5. Variables live in the smallest scope that can hold them (`ES.74`); a loop variable is dead the moment its loop ends.

---

## Quality Check

Review checklist:

- [ ] Every declaration initializes; no member relies on constructor-body assignment alone
- [ ] `{}` used wherever a narrowing conversion is conceivable; no new silent-truncation warnings
- [ ] Member initializer lists match declaration order; `-Wreorder` clean
- [ ] `auto` only where the initializer states the type; public APIs spell their types
- [ ] Zero C-style casts; every `reinterpret_cast` carries its justification comment; no `const_cast` mutation
- [ ] Signed arithmetic uses signed types; no unsigned sentinels guarding negatives
- [ ] Nesting stays shallow; guards return early; repeated compound conditions became named predicates
- [ ] No structural container mutation inside a range-for; no iteration over dying temporaries

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
