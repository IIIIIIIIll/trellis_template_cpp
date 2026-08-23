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

---

## Complete Coverage: ES

| Rule | Stance | Disposition |
|------|--------|-------------|
| `ES.1` | Adopt | Reach for the standard library before any third-party library or hand-written loop: it is better tested, higher level, and present in every toolchain. The sole carve-out is allocation-restricted contexts, which escalate to the arena and pool patterns in [Memory and Ownership](./memory-and-ownership.md). |
| `ES.2` | Adopt | Suitable abstractions — library types and classes — sit closer to the problem than bare language features and give shorter, clearer, better-tested code; raw `char*`-style encodings of concepts are rejected in review. |
| `ES.3` | Adopt | Duplicated logic obscures intent and diverges silently under maintenance; hoist it into one function or replace both copies with a standard algorithm. Review plus static analysis are the catchers. |
| `ES.5` | Adopt | Names live in the smallest scope that can hold them: short scopes release resources early, shrink the state a reader tracks, and block accidental later misuse. Long stretches between a handle's last use and its scope end are the flagged smell. |
| `ES.6` | Adopt | Loop counters are declared in the `for` initializer, and C++17 `if`/`switch` initializer statements confine selection variables to their block — nothing outlives the construct that needed it. |
| `ES.7` | Covered elsewhere | Name-length policy (short common locals, longer uncommon non-locals) is owned by [Quality Guidelines](./quality-guidelines.md) as part of its naming rules. |
| `ES.8` | Covered elsewhere | Confusable-name avoidance — `l1`/`I0`-class look-alikes and type/non-type name collisions — belongs to [Quality Guidelines](./quality-guidelines.md)' naming section. |
| `ES.9` | Covered elsewhere | `ALL_CAPS` stays reserved for macros so constants and enumerators cannot collide with preprocessor substitution; the resulting constant-naming rule lives in [Quality Guidelines](./quality-guidelines.md) (see `Enum.5`). |
| `ES.10` | Adopt | One declarator per statement: comma lists hide an uninitialized variable among initialized ones and blur pointer decoration. Function parameters and structured bindings are the sanctioned exceptions. |
| `ES.12` | Adopt | Shadowing is forbidden — an inner scope introduces a new name instead of reusing an outer one, members included. Restating a base-class function name alongside a `using` declaration remains the exception. |
| `ES.21` | Adopt | A variable appears no earlier than its first use; a declaration drifting ahead of its initializer gets pulled down next to it. |
| `ES.24` | Covered elsewhere | Owning pointers travel in smart pointers with `unique_ptr<T>` as the default holder — the ownership ladder in [Memory and Ownership](./memory-and-ownership.md) owns this end to end. |
| `ES.26` | Adapt | One variable serves one purpose. The single sanctioned overlap is a scoped scratch buffer reused across iterations to dodge reallocation ([Performance](./performance.md)) — same buffer job each pass, never two meanings; stale contents from the previous round stay a reviewed hazard. |
| `ES.27` | Adopt | Fixed-size stack arrays are `std::array`: they carry their bound in the type and never decay to pointers. Built-in arrays with non-local bounds and VLA-style runtime bounds are rejected outright as the security risks they are. |
| `ES.30` | Adopt | No macro rewrites program text: macros ignore scope and type, show the reader something different from what the compiler sees, and break tooling. Configuration-control `#ifdef` blocks remain acceptable; stringification and token pasting do not. |
| `ES.31` | Adopt | Constants are `constexpr` variables and pseudo-functions are templates or overloads, never object-like or function-like macros — untyped expansion and unevaluated-argument surprises ship free with the latter. |
| `ES.32` | Adopt | Any macro that survives the bans above is spelled `ALL_CAPS` so readers see the preprocessor at work; a lowercase macro is treated as a defect. |
| `ES.33` | Adopt | Macros ignore scope, so survivors carry long, prefix-qualified names unique enough to survive contact with third-party headers. |
| `ES.34` | Adopt | C-style variadic functions are not definable here: `va_arg` trusts unchecked casts and a miscounted call crashes. Variadic templates and overloads express the same shapes safely; `<cstdarg>` in a diff fails review. |
| `ES.40` | Adopt | Expressions read in one pass: no assignments or multi-object side effects buried in subexpressions, no reliance on subtle precedence or undefined behavior. The counter-duty holds too — splitting every operation into its own statement is its own obfuscation. |
| `ES.41` | Adopt | Arithmetic, comparison, and logical precedence are assumed knowledge; anything mixing bitwise operators with other operators takes explicit parentheses (`(a & flag) != 0`). Assignments sit leftmost or nowhere. |
| `ES.42` | Covered elsewhere | Pointer simplicity — no pointer arithmetic, sequences as spans, no array decay — is owned by [Memory and Ownership](./memory-and-ownership.md), with the span-at-the-boundary rules in [Performance](./performance.md). |
| `ES.43` | Adopt | Expressions with undefined order of evaluation do not exist here: a value written in an expression is not read elsewhere in it (`v[i] = ++i` shape). C++17 tightened some sequencing, but code gets pasted into pre-C++17 builds, so no cleverness. |
| `ES.44` | Adopt | Function-argument evaluation order is unspecified even after C++17, so interdependent arguments are sequenced into separate statements instead of `f(++i, ++i)` shapes. |
| `ES.45` | Adopt | Unnamed literals beyond the trivial set (`0`, `1`, `nullptr`, `'\n'`, `""`) become named `constexpr` constants; a number needing a comment deserves a name. Wider compile-time-constant conventions live in [Quality Guidelines](./quality-guidelines.md). |
| `ES.47` | Adopt | Null pointers are `nullptr`, never `0` or `NULL` — literal zero quietly resolves `f(0)` onto the integer overload, and deduction misfires around `NULL`. |
| `ES.55` | Adopt | Prefer constructs that cannot go out of range — range-`for`, position-returning algorithms — over indexed access wrapped in checks. An explicit bounds check is usually the tell that the wrong abstraction was picked. |
| `ES.60` | Covered elsewhere | No naked `new` or `delete` outside resource-management code: the ownership ladder in [Memory and Ownership](./memory-and-ownership.md) bans them outright in favor of RAII holders. |
| `ES.61` | Covered elsewhere | Matching `delete[]` to array news matters only where a bare `delete` exists; [Memory and Ownership](./memory-and-ownership.md) removes the mismatch by removing owning raw pointers. |
| `ES.62` | Adopt | Relational comparison or subtraction of pointers into different arrays is undefined; ordering and differences mean something only within one array. |
| `ES.63` | Covered elsewhere | Slicing is prevented structurally — polymorphic bases suppress copying (`C.67`) and deliberate partial copies demand a named operation — per [Classes and Hierarchies](./classes-and-hierarchies.md). |
| `ES.64` | Adopt | Construction is spelled `T{e}`: it announces construction, refuses narrowing, and stays safe where cast forms are not. The container wart — `(10)` for size versus `{10}` for one element — remains confined to that idiom and is stated plainly at call sites. |
| `ES.65` | Covered elsewhere | Never dereferencing an invalid pointer — null, dangling, or invalidated — is the lifetime-safety core of [Memory and Ownership](./memory-and-ownership.md), including its container-invalidation table. |
| `ES.71` | Adopt | Range-`for` is the default loop: it cannot mis-index and states intent. Index-based `for` survives only when the body truly needs the index — neighbor elements, strides, deliberate counter work — and the loop variable binds by reference, never by value copy. |
| `ES.72` | Adopt | With an obvious loop variable, a classic `for` beats `while`: the whole mechanism sits up front and the counter's scope ends with the loop. |
| `ES.73` | Adopt | With no loop variable, `while` wins: an event-driven condition wedged into a `for` frame with an unrelated increment misleads every reader. |
| `ES.77` | Adopt | `break` and `continue` stay rare: a loop needing `break` usually wants extraction into a function where it becomes `return`, and `continue` chains collapse into one positive `if`. Kept ones are visible at a glance. |
| `ES.79` | Adopt | `default` handles the genuinely common case; when only specific cases matter, an explicit empty `default` records that decision so neither maintainer nor compiler assumes a missed enumerator. Switches over enums name every case or carry a default. |
| `ES.84` | Adopt | Unnamed locals do not exist: `lock_guard<mutex>{mx};` builds a temporary that unlocks immediately — a silent race. Scoped guards get names so their lifetime binds to the scope. |
| `ES.85` | Adopt | A deliberate no-op body is an empty block carrying a comment; a stray semicolon behind a loop head is invisible and flips the meaning of the program. |
| `ES.86` | Adopt | The `for` header alone steers the counter; mutating it inside the body destroys top-down reasoning about iterations. Skip logic uses a separate flag — two concepts, two variables — or a restructured loop. |
| `ES.105` | Adopt | Integer `/` and `%` by a possibly-zero divisor take an explicit precondition at the boundary; the undefined crash is never left implicit. Precondition mechanics live in [Functions and Interfaces](./functions-and-interfaces.md); floating-point division by zero is a separate domain decision. |

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
