# Expressions and Flow

> Expression-level discipline for C++ in this project: initialization that cannot fail, `auto` where it helps, casts that announce themselves, consistent signedness, and control flow that stays flat enough to review.

---

## Overview

Most C++ defects below the ownership level are expression-shaped: a value read before it was written, a narrowing conversion that silently ate a counter, a C-style cast that quietly stripped `const` on its way to corruption. This document fixes the shape of individual expressions and statements so the compiler catches mistakes instead of absorbing them.

Baseline: C++14 (`std::make_unique`, generic lambdas, relaxed `constexpr`).
C++17 and C++20 additions appear as marked upgrades where they change the
recommendation — `std::string_view`, `std::optional`, `if constexpr`,
`[[nodiscard]]`, `std::span` — each with the C++14 spelling alongside, so a
C++14 project can follow every rule as written. Ownership and lifetime
questions live in [Memory and Ownership](./memory-and-ownership.md); failure
paths in [Error Handling](./error-handling.md).

Default strength: default.

Caught by: review — no automated detector.

At expression level the defaults come before the micro-decisions.

**EXPR-1.** Reach for suitable abstractions (`ES.2`) — library types and classes sit closer to the problem than bare language features and give shorter, clearer, better-tested code — and reach for the standard library before any third-party library or hand-written loop (`ES.1`); allocation-restricted contexts are the sole carve-out, escalating to the arena and pool patterns in [Memory and Ownership](./memory-and-ownership.md).

**EXPR-2.** Repeated expressions hoist into one function or collapse into a standard algorithm (`ES.3`) — duplicated logic obscures intent and diverges silently under maintenance; review plus static analysis catch what slips through.

---

## Initialization Discipline

Default strength: default.

Caught by: review — no automated detector.

**EXPR-3 (hard).** Every object holds a value from the moment it is created (`ES.20`). Declaring first and assigning later is how uninitialized reads survive refactors: someone inserts an early return between the declaration and the assignment.

Caught by: `-Wuninitialized` / `-Wmaybe-uninitialized` when the gap produces an actual uninitialized read; review for the declaration-to-assignment gap itself.

Caught by: review — no automated detector.

| Situation | Form |
|-----------|------|
| Any object, at declaration | Initialize immediately (`ES.20`) |
| **EXPR-4** Value known only mid-function | Declare at that point, initialized (`ES.22`) |
| **EXPR-5** Object never reassigned afterward | Mark it `const`; compile-time-known values are `constexpr` (`ES.25`) |
| Loop-local helper | Declare inside the loop body, smallest scope (`ES.74`) |

**Wrong**

```cpp
// compiles; UB at runtime
Status process(const Request& req) {
    Result out;                     // default-constructed into an unknown state
    if (!authorize(req)) {
        return Status::Denied;
    }
    out = evaluate(req);            // gap between birth and first value
    return out.status();
}
```

**Right**

```cpp
// EXPR-3: every object is born holding its value
Status process(const Request& req) {
    if (!authorize(req)) {
        return Status::Denied;
    }
    const Result out = evaluate(req);
    return out.status();
}
```

**EXPR-6.** Class members follow the same rule twice: in-class initializers for every member with a sensible default, and a constructor member-initializer list for everything else. Constructor bodies that assign members are initialization theater — by the time the body runs, members were already constructed.

### Scope and Declaration Hygiene

**EXPR-7.** A name lives in the smallest scope that can hold it (`ES.5`) and appears no earlier than its first use (`ES.21`); short scopes release resources early and shrink the state a reader tracks, and long stretches between a handle's last use and its scope end are the flagged smell.

**EXPR-8.** One declarator per statement (`ES.10`): comma lists hide an uninitialized variable among initialized ones and blur pointer decoration — function parameters and structured bindings (C++17) are the sanctioned exceptions.

Caught by: clang-tidy `readability-isolate-declaration`.

**EXPR-9.** Loop counters declare in the `for` initializer, and selection
variables live in the tightest enclosing scope (`ES.6`) — declare an
`if`/`switch` condition's variable in a block immediately wrapping the
construct so nothing outlives the branch that needed it. **C++17:** the
`if`/`switch` init-statement (`if (auto it = m.find(k); it != m.end())`)
confines the variable to the construct itself.

Caught by: review — no automated detector.

**EXPR-10 (hard).** Shadowing is forbidden (`ES.12`): an inner scope introduces a new name rather than reusing an outer one, members included; restating a base-class function name alongside a `using` declaration remains the exception.

Caught by: `-Wshadow`.

```cpp
// EXPR-10: inner scope renames instead of shadowing
// compiles; UB at runtime
// Wrong: the inner count hides the outer one -- which count reaches the log?
std::size_t count = pending();
if (streaming) {
    const auto count = estimate_size();   // shadows; outer count is frozen mid-value
    ship(count);
}
report(count);

// Right: the inner scope names its own value; the outer count keeps its meaning
std::size_t count = pending();
if (streaming) {
    const std::size_t streamed = estimate_size();
    ship(streamed);
}
report(count);
```

**EXPR-11.** One variable serves one purpose (`ES.26`). Deviation from `ES.26`: a scoped scratch buffer reused across iterations to dodge reallocation ([Performance](./performance.md)) is the single sanctioned overlap — the buffer holds the same job every pass, never two meanings, and stale contents from the previous round stay a reviewed hazard.

Caught by: review — no automated detector.

Naming conventions themselves — length by scope (`ES.7`), confusable look-alikes such as `l1`/`I0` (`ES.8`), and `ALL_CAPS` reserved for macros so constants cannot collide with preprocessor substitution (`ES.9`, see `Enum.5`) — are owned by the naming rules in [Quality Guidelines](./quality-guidelines.md).

### Braces Prevent Narrowing

**EXPR-12 (hard).** Prefer brace initialization (`ES.23`): the `{}` form turns a lossy conversion into a compile error instead of a silent truncation (`ES.46`).

Caught by: the narrowing error the `{}` form raises at compile time; `-Wconversion` for `=`-initialized conversions the discipline misses.

```cpp
// EXPR-12: brace init turns narrowing into a compile error
// Wrong: compiles, loses data
int samples = collect();
uint8_t quantized = samples;        // silent truncation
double ratio = 3 / 4;               // integer division happens first: 0.0

// Right: the compiler refuses
int samples = collect();
uint8_t quantized{samples};         // compile-error: narrowing
double ratio = 3.0 / 4.0;           // intent stated in types, not hoped for in results
```

**EXPR-13.** Use `=` where the type is spelled out and no conversion risk exists (`std::string name = req.user();`); use `{}` wherever a conversion could bite — integral-to-smaller-integral and floating-to-integral above all. Construction itself is spelled `T{e}` (`ES.64`): it announces construction, refuses narrowing, and stays safe where cast forms are not; the container wart — `(10)` for size versus `{10}` for one element — stays confined to that idiom and stated plainly at call sites.

Caught by: review — no automated detector.

### Member Initializer Lists Follow Declaration Order

**EXPR-14 (hard).** Members initialize in **declaration order**, not list order (`C.47`): reordering the list to look tidy initializes members in an order their dependencies do not expect, and `-Wreorder` flags it. Declare members in dependency order and mirror that order in every constructor's initializer list.

Caught by: `-Wreorder`.

```cpp
// compiles; UB at runtime
// Wrong: list order lies -- width_ initializes AFTER area_ needs it
class Window {
public:
    explicit Window(Size s)
        : width_(s.width()),
          height_(s.height()),
          area_(width_ * height_) {}   // area_ is declared FIRST, so it initializes FIRST
private:
    int area_;       // initialized before width_/height_ exist: reads garbage
    int width_;
    int height_;
};
```

```cpp
// EXPR-14: initializer list mirrors declaration order
// Right: members declared in dependency order; the list mirrors that order
class Window {
public:
    explicit Window(Size s)
        : width_(s.width()),
          height_(s.height()),
          area_(width_ * height_) {}
private:
    int width_;
    int height_;
    int area_;
};
```

### Named Constants

**EXPR-15.** Unnamed literals beyond the trivial set — `0`, `1`, `nullptr`, `'\n'`, `""` — become named `constexpr` constants (`ES.45`); a number needing a comment deserves a name. Wider compile-time-constant conventions live in [Quality Guidelines](./quality-guidelines.md).

Caught by: review — no automated detector.

---

## `auto`: When It Helps, When It Hides

Default strength: default.

Caught by: review — no automated detector.

**EXPR-16.** `auto` removes redundancy, not information (`ES.11`). Use it when the initializer already states the type; spell the type when the type *is* the information.

| Use `auto` | Spell the type |
|------------|----------------|
| Iterators: `auto it = map.find(key);` | Numeric contracts: `int64_t offset`, `size_t count` |
| Range-for over an obviously typed sequence | Anything crossing an API boundary (parameters, returns) |
| Calls whose name carries the type: `auto conn = open_connection(cfg);` | Domain-typed values (`Meters`, `SampleRate`) |
| Lambda parameters and expression templates nobody could spell | Conversions you want checked — `auto` hides truncation |

```cpp
// EXPR-16: spell the type when it is the contract
// compiles; UB at runtime
// Wrong: the reader must resolve the whole call chain to know what `r` is
auto r = service.rate(id);

// Right: the contract is visible at the call site
SampleRate r = service.rate(id);
```

**EXPR-17.** Public function signatures spell their return types; a signature is documentation, and `auto` deletes the relevant line.

---

## Cast Discipline

Casts are declarations of distrust toward the type system, so they are rare, precise, and searchable (`ES.48`).

Default strength: default.

Caught by: review — no automated detector.

| Intent | Tool |
|--------|------|
| **EXPR-18** Deliberate arithmetic conversion | `static_cast` |
| **EXPR-19** Polymorphic downcast | `dynamic_cast`, result checked |
| **EXPR-20** Bit-level reinterpretation of trivially copyable bytes | `memcpy`, `std::bit_cast` (C++20) |
| **EXPR-21 (hard)** Strip `const` to mutate | Forbidden (`ES.50`); Caught by: clang-tidy `cppcoreguidelines-pro-type-const-cast` |
| **EXPR-22 (hard)** Pointer reinterpretation | `reinterpret_cast` plus a review comment justifying alignment and lifetime |

**EXPR-23 (hard).** Forbidden outright: C-style casts `(T)x`. A C-style cast asks the compiler to silently pick the cheapest of five different operations — including `const_cast` and `reinterpret_cast` — which is exactly why it must never appear (`ES.49`).

Caught by: clang-tidy `cppcoreguidelines-pro-type-cstyle-cast`.

```cpp
// EXPR-23: C-style casts forbidden; fix the const contract
// compiles; UB at runtime
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

## Pointers and Arrays

Default strength: hard.

Caught by: review — no automated detector.

**EXPR-24.** Fixed-size stack arrays are `std::array` (`ES.27`): the bound travels in the type and nothing decays to a pointer — built-in arrays with non-local bounds and VLA-style runtime bounds are rejected outright as the security risks they are.

Caught by: `-Wvla` for runtime bounds; review for built-in arrays with non-local bounds.

**EXPR-25.** Null pointers are `nullptr`, never `0` or `NULL` (`ES.47`): literal zero quietly resolves `f(0)` onto the integer overload, and deduction misfires around `NULL`.

Caught by: clang-tidy `modernize-use-nullptr`.

**EXPR-26.** Relational comparison or subtraction of pointers into different arrays is undefined (`ES.62`); ordering and differences mean something only within one array.

Everything else about pointers is owned by sibling guides. Owning pointers travel in smart pointers, `unique_ptr<T>` by default (`ES.24`), and neither naked `new` nor naked `delete` appears outside resource-management code (`ES.60`) — the ownership ladder in [Memory and Ownership](./memory-and-ownership.md) owns both end to end, and dissolves the `delete[]` mismatch question by removing owning raw pointers entirely (`ES.61`). Never dereferencing an invalid pointer — null, dangling, or invalidated — is that guide's lifetime-safety core, container-invalidation table included (`ES.65`). Pointer simplicity itself — no pointer arithmetic, sequences as spans — lives there too (`ES.42`), with spans at API boundaries per [Performance](./performance.md). Slicing is prevented structurally at the class level (`ES.63`) per [Classes and Hierarchies](./classes-and-hierarchies.md).

---

## Signedness Consistency

Default strength: default.

Caught by: the sign-comparison and sign-conversion warnings enabled by default in the build; suppressing one requires a comment naming the reason.

**EXPR-27 (hard).** An expression commits to one signedness and keeps it (`ES.100`): signed types do arithmetic (`ES.102`), unsigned types do bit manipulation (`ES.101`). The classic failure is choosing unsigned "because counts are never negative" (`ES.106`):

```cpp
// EXPR-27: reverse iterators instead of unsigned countdown
// compiles; UB at runtime
// Wrong: unsigned wraps instead of going negative
std::vector<Item> pending = remaining();
for (std::size_t i = pending.size() - 1; i >= 0; --i) {   // broken for every input: i >= 0 is a tautology; after i == 0, --i wraps to SIZE_MAX and indexes out of bounds -- immediately when empty
    ship(pending[i]);
}

// Right: walk backwards with reverse iterators, or use signed indices
std::vector<Item> pending = remaining();
for (auto it = pending.rbegin(); it != pending.rend(); ++it) {
    ship(*it);
}
```

Rules:

- **EXPR-28.** Indices, counts, offsets, and differences are signed — `int64_t` unless profiling says narrower. Subscripts gain nothing from being unsigned (`ES.107`).
- **EXPR-29.** Bit masks, flags, and hashes are `uint32_t`/`uint64_t` (`ES.101`).
- **EXPR-30.** Mixed-sign comparisons get fixed at the source: restructure the condition or convert the value with a genuinely bounded domain. Never sprinkle casts until the warning disappears.
- **EXPR-31 (hard).** Buffer math and length fields near limits carry explicit precondition checks (`ES.103`, `ES.104`); wraparound is a bug, not a feature.

  Caught by: review — no automated detector.

- **EXPR-32 (hard).** Integer `/` and `%` by a possibly-zero divisor take an explicit precondition at the boundary (`ES.105`); the undefined crash is never left implicit. Precondition mechanics live in [Functions and Interfaces](./functions-and-interfaces.md); floating-point division by zero is a separate domain decision.

  Caught by: review — no automated detector.

**EXPR-33 (hard).** Shifts need the same suspicion the arithmetic above gets: the count must be `>= 0` and strictly below the width of the promoted left operand, and a signed left shift that overflows is UB (`ES.103`). Small unsigned types promote first — `uint16_t` arithmetic happens in `int`, so `uint16_t{0xFFFF} << 17` overflows the promoted signed type and is UB, where the same shift on `uint32_t` would merely wrap. Keep shifted operands in their full `uint32_t`/`uint64_t` domain and treat non-constant shift counts as preconditions.

Caught by: UBSan's shift checks in sanitizer builds.

---

## Expression Shape and Evaluation Order

Default strength: default.

Caught by: review — no automated detector.

**EXPR-34.** Expressions read in one pass (`ES.40`): no assignments or multi-object side effects buried in subexpressions, no reliance on subtle precedence or undefined behavior. The counter-duty holds too — splitting every operation into its own statement is its own obfuscation. Arithmetic, comparison, and logical precedence are assumed knowledge; anything mixing bitwise operators with other operators takes explicit parentheses — `(a & flag) != 0` — and assignments sit leftmost or nowhere (`ES.41`).

**EXPR-35 (hard).** A value written in an expression is not read elsewhere in the same expression (`ES.43`): the `v[i] = ++i` shape does not exist here. C++17 tightened some sequencing, but code gets pasted into pre-C++17 builds, so no cleverness.

**EXPR-36.** Function-argument evaluation order is unspecified even after C++17 (`ES.44`), so interdependent arguments sequence into separate statements instead of `f(++i, ++i)` shapes.

---

## Control Flow Shape

Default strength: default.

Caught by: review — no automated detector.

**EXPR-37.** Functions read top-down: guard clauses first, main path last. Early returns are the default; single-exit is not a goal — one extra `return` that removes three indent levels is a win. The real budget is nesting depth: past two levels of compound conditionals, extract named predicates and delete cleverness.

```cpp
// EXPR-37: guard clauses first, main path last
// compiles; UB at runtime
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

- **EXPR-38 (hard).** No `goto` (`ES.76`).
- **EXPR-39.** No `do/while` unless it removes worse duplication between the prologue and the tail (`ES.75`) — in practice, almost never.
- **EXPR-40 (hard).** Every non-empty `case` ends with `break` or an obvious `return`; an intentional fallthrough carries `[[fallthrough]]` (`ES.78`) — the annotation that satisfies `-Wimplicit-fallthrough` — with the adjacent comment stating why falling through is correct.

  Caught by: `-Wimplicit-fallthrough`.

- **EXPR-41.** Redundant boolean dressing is noise: `if (found)`, not `if (found == true)` (`ES.87`). Conditions contain no assignments and no hidden side effects.

  Caught by: review — no automated detector.

- **EXPR-42.** Range-based `for` is the default loop (`ES.71`): it cannot mis-index and states intent. Index-based `for` survives only when the body truly needs the index — neighbor elements, strides, deliberate counter work — and binds its variable by reference, never by value copy.
- **EXPR-43.** Prefer constructs that cannot go out of range (`ES.55`) — range-`for`, position-returning algorithms — over indexed access wrapped in checks; an explicit bounds check is usually the tell that the wrong abstraction was picked.
- **EXPR-44 (hard).** Never mutate a container's structure while iterating it — reallocation invalidates the iterator.
- **EXPR-45 (hard).** Range-for extends only the final range expression's temporary to the loop: a direct value-returning init such as `make_rows()` is safe, but in a chained init like `connection_pool().acquire().rows()` the intermediate temporaries die at the end of the full-expression, leaving the extended range viewing destroyed owners — own the outer object. (C++23 extends every temporary in the range-init and closes this trap; pre-C++23 dialects do not.) The invalidation table lives in [Memory and Ownership](./memory-and-ownership.md).

```cpp
// EXPR-45: own the outer object of a chained range-init
// compiles; UB at runtime
// Wrong: only the final range expression is lifetime-extended -- the pool and
// connection temporaries die at the end of the full-expression, so rows() views dead owners
for (const Row& row : connection_pool().acquire().rows()) { consume(row); }

// Right: own the outer object for the duration of the iteration
auto conn = connection_pool().acquire();
for (const Row& row : conn.rows()) { consume(row); }
```

- Variables live in the smallest scope that can hold them (`ES.5`); a loop variable is dead the moment its loop ends.
- **EXPR-46.** With an obvious loop variable, a classic `for` beats `while` (`ES.72`): the whole mechanism sits up front and the counter's scope ends with the loop. With no loop variable, `while` wins (`ES.73`): an event-driven condition wedged into a `for` frame with an unrelated increment misleads every reader.
- **EXPR-47.** `break` and `continue` stay rare (`ES.77`): a loop needing `break` usually wants extraction into a function where it becomes `return`; `continue` chains collapse into one positive `if`. Kept ones are visible at a glance.
- **EXPR-48.** The `for` header alone steers the counter (`ES.86`); mutating it inside the body destroys top-down reasoning about iterations. Skip logic uses a separate flag — two concepts, two variables — or a restructured loop.
- **EXPR-49 (hard).** Unnamed locals do not exist (`ES.84`): `lock_guard<mutex>{mx};` builds a temporary that unlocks immediately — a silent race. Scoped guards get names so their lifetime binds to the scope.
- **EXPR-50 (hard).** A deliberate no-op body is an empty block carrying a comment (`ES.85`); a stray semicolon behind a loop head is invisible and flips the meaning of the program.

  Caught by: `-Wempty-body`.

- **EXPR-51.** `default` handles the genuinely common case (`ES.79`); when only specific cases matter, an explicit empty `default` records that decision so neither maintainer nor compiler assumes a missed enumerator. Switches over enums name every case or carry a default.

  Caught by: review — no automated detector.

---

## Macros and Variadics

Default strength: hard.

Caught by: review — no automated detector.

The preprocessor has no seat at the expression table.

**EXPR-52.** No macro rewrites program text (`ES.30`): macros ignore scope and type, show the reader something different from what the compiler sees, and break tooling — configuration-control `#ifdef` blocks remain acceptable, stringification and token pasting do not.

**EXPR-53.** Constants are `constexpr` variables and pseudo-functions are templates or overloads, never object-like or function-like macros (`ES.31`).

**EXPR-54.** Any macro surviving review is spelled `ALL_CAPS` so readers see the preprocessor at work (`ES.32`) — a lowercase macro is treated as a defect — and carries a long, prefix-qualified name unique enough to survive contact with third-party headers (`ES.33`).

**EXPR-55.** C-style variadic functions are not definable here (`ES.34`): `va_arg` trusts unchecked casts, and a miscounted call crashes. Variadic templates and overloads express the same shapes safely; `<cstdarg>` in a diff fails review.

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
- [ ] No structural container mutation inside a range-for; chained range-inits own the outer object, never an intermediate temporary

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
