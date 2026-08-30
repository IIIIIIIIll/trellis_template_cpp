# Templates and Generics

> Generic code whose requirements live in the type system: concepts as documented interfaces (with C++17 fallbacks), deliberately small template surface, and explicit tradeoffs for erasure, dispatch, and CRTP.

---

## Overview

Templates are the project's abstraction workhorse, but an unconstrained template is an undocumented function: every caller discovers its requirements by compiler archaeology. This document sets the defaults for writing generic code that compiles fast, fails readably, and does not leak implementation into headers.

Baseline: **C++17**, so concepts keywords are unavailable by default; requirements are expressed as trait checks and `static_assert`. Where the toolchain provides C++20 (`requires`, named concepts), those become the preferred spelling and are marked inline. The intent is identical either way: a template argument's obligations are written down next to the declaration, not reverse-engineered from instantiation errors.

The standing questions before adding any template:

1. Does one algorithm genuinely serve many types (then template it), or is this two functions wearing a trench coat?
2. Can callers see the requirements without reading the body?

---

## Document Requirements with Concepts

A template parameter is a contract. On C++20, the contract is a named concept; on C++17 it is a `static_assert` over standard traits. What is forbidden in both dialects is the bare `template <typename T>` whose constraints surface only as a wall of instantiation errors three translation units away.

| Mechanism | Dialect | Use when |
|-----------|---------|----------|
| Named concepts + `requires` | C++20 | Default wherever available; best diagnostics |
| `static_assert` over type traits in the primary template | C++17 fallback | Every public template lacking concepts support |
| `enable_if` SFINAE | Legacy | Only to select between overloads; see below |
| Unconstrained parameters | Never for public APIs | Private implementation detail at most |

Wrong:

```cpp
// Contract discoverable only by instantiating it wrongly.
template <typename T>
T median(std::vector<T>& values) {
    std::sort(values.begin(), values.end());
    const auto mid = values.size() / 2;
    return (values[mid] + values[mid + 1]) / 2;   // arithmetic the element type may not support
}

std::vector<std::string> words{"a", "bc", "d"};
median(words);   // deduction succeeds (T = std::string); 40 lines of errors ending
                 // somewhere useful, allegedly — inside the body's `/ 2`, not at the call
```

Right (C++17):

```cpp
#include <type_traits>

template <typename T>
T median(const std::vector<T>& values) {
    static_assert(std::is_arithmetic_v<T> || std::is_same_v<T, std::chrono::milliseconds>,
                  "median() requires an arithmetic element type");
    // ...
}
```

Right (C++20):

```cpp
#include <concepts>

template <typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template <Numeric T>
T median(const std::vector<T>& values);
```

Rules:

1. Constrain every public template. The guideline phrased positively — state the requirements of each template argument up front (`T.10`) — is the whole section in one sentence. A pile of unrelated, barely-related parameters is a smell too: split the function instead of listing five type knobs.
2. A constraint must carry meaning, not just syntax. Requiring "has `size()`" says almost nothing; requiring "a range whose size query is O(1)" is a requirement. Concepts without semantics are documentation-shaped noise (`T.20`).
3. Prefer one concept over `enable_if` gymnastics wherever the dialect allows. Keep legacy SFINAE quarantined behind a named alias if it must exist.
4. Constrain to what the algorithm essentially needs, nothing more (`T.41`): debug streamability does not belong in `sort`'s concept, and nobody demands `operator<<` inside a sorting routine because some caller once debugged through it. Deliberately leaving non-essential operations unchecked delays their failure to instantiation time — the accepted price of a stable interface.
5. An unconstrained template with a common, attractive name (`swap`, `begin`, `hash`) hijacks overload resolution far beyond its home directory; give such helpers a constrained or namespaced spelling (`T.47`).
6. A concept must require a coherent, complete set of operations (`T.21`): `Subtractable` alone is meaningless without `+`, and comparison arrives as the full six-operator set. Flag odd subsets such as `==` without `!=` — surprising for users and sometimes slower.
7. Concepts carry axioms (`T.22`) — the mathematical assumptions (`a - a == 0`, distributivity) written as comments beside the `requires` clause until language support exists. An axiom is assumed like a precondition; early experimental concepts may ship incomplete, but are then explicitly not stable.
8. Differentiate a refined concept from its more general case by adding use patterns (`T.23`): a forward iterator is an input iterator plus suffix `++`, letting the compiler derive subsumption from requirement sets alone. Two concepts with identical requirements are equivalents, not a hierarchy.
9. When two concepts differ only in semantics, separate them with a trait or tag class (`T.24`) — *contiguous* is random-access plus `is_contiguous_v` — preferring standard-library traits and wrapping the trait back into a named concept.
10. Never write complementary constraints (`T.25`): paired `requires C<T>` / `requires !C<T>` definitions explode combinatorially, and legacy `enable_if` code commits this habit routinely. Provide an unconstrained primary plus a constrained refinement, or delete the primary.

Notation follows the dialect. Deviation from `T.12`: a bare `auto` is the weakest possible concept, so where a fitting C++20 concept exists prefer the constrained spelling; on the C++17 baseline the notation does not exist and plain `auto` stays acceptable. Deviation from `T.13`: the shorthand for simple single-type-argument concepts — `template <Sortable T>`, or `Sortable auto&&` — reads the way we speak and wins wherever C++20 is available; the C++17 fallback remains the traits-based `static_assert` spelled out above. Deviation from `T.48`: without concept support the guideline's best emulation is `enable_if`, which drags in complementary-constraint designs; this project's C++17 dialect instead prefers `static_assert` trait checks for stating contracts and quarantines SFINAE behind named aliases for genuine overload selection.

When a class claims to model a concept, prove it early: `static_assert(Modelable<T>)` pointed at concrete model types (`T.150`) — review-visible, cheap, and the same idiom this guide mandates inside template bodies.

Caught by: compile time itself — that is the point. Readability of the failure is review-visible: if a colleague cannot tell why their type fails within one screen of output, the constraint is missing or miswritten.

---

## Minimize the Template Surface

Every template parameter is a tax paid at every call site, in error messages, and in header coupling. The default is the smallest parameter list that expresses the real variation.

| Smell | Fix |
|-------|-----|
| Type parameter used only for a constant inside | Take the constant as a value parameter or runtime argument |
| Members templated though only some methods care | Hoist non-dependent members out of the template (`T.61`, `T.62`) |
| Same alias spelled out at ten call sites | One `using` alias near the definition (`T.42`) |
| Deduction ceremony repeated everywhere | Constructor or factory function letting CTAD work (`T.44`) |

Wrong:

```cpp
// CachePolicy exists only so one method can pick eviction; every get()/put() user pays for knowing it.
template <typename K, typename V, typename CachePolicy>
class LruCache {
public:
    std::optional<V> get(const K& key);
    void put(K key, V value);
    void set_policy(CachePolicy policy);   // the only dependent member
private:
    CachePolicy policy_;
};
```

Right:

```cpp
// Common case carries no extra parameter.
template <typename K, typename V>
class LruCache {
public:
    std::optional<V> get(const K& key);
    void put(K key, V value);
};

// The variant lives where the variation is.
template <typename K, typename V, typename EvictionPolicy>
class LruCacheWithPolicy : public LruCache<K, V> { /* ... */ };
```

Notes:

- Keep templates independent of their surroundings: fewer includes, fewer global names visible at instantiation (`T.60`). A helper template that reaches for six headers slows every includer.
- Name a template (or give it a stable home) only when reuse is real; an operation needed exactly once does not earn a header of its own (`T.140`, `T.141`).
- Spell aliases with `using`, never `typedef` (`T.43`): the new name leads, the syntax parallels `auto`, and only `using` can form template aliases; expect enforcement to flag legacy `typedef`s widely.
- CTAD (`T.44`) is authored, not lucky. Constructor CTAD fires when a constructor's parameters deduce the template arguments; write an explicit deduction guide — `template <typename Iter> Container(Iter b, Iter e) -> Container<typename std::iterator_traits<Iter>::value_type>;` — when no constructor exposes the intended mapping, or when the implicit one would deduce the wrong thing. Aggregate templates generate no constructor guides: on C++17, deducing one from brace-init requires a hand-written guide, with aggregate CTAD itself arriving in C++20. And guides generated from constructors inherited via `using Base::Base;` deduce against the base template, not the derived class — making a derived class template deducible from them only landed in C++23.
- Header-heavy instantiation volume has a relief valve in explicit instantiation declarations: `extern template class LruCache<K, V>;` in the header tells every other translation unit the definition is instantiated elsewhere, while the matching explicit instantiation (`template class LruCache<K, V>;`) is compiled once in a single source file. Judging when that trade pays lives in [Quality Guidelines](./quality-guidelines.md)' Compile-Time Discipline section.

---

## Inside the Template Body

Constraints guard the boundary; these rules keep the body honest. Ordinary-looking mistakes gain extra meanings inside a template, where every call and initializer participates in deduction.

1. Pass operations to algorithms as function objects (`T.40`) — lambdas included — which carry state through the interface and inline well, rather than function pointers; function-pointer template arguments get flagged by enforcement.
2. Initialize with `{}` rather than `()` inside templates (`T.68`): the paren form invites both the parse where `T v1(T(u));` declares a function and silent casts like `f(1, "asdf")`. Braced form states variable-hood outright, and enforcement flags paren initializers and function-style casts.
   Carve-out: where the type has an `initializer_list` constructor and paren semantics are intended — size or n-value construction (`std::vector<int> v(n)` sizes to `n`; `v{n}` makes a one-element vector), emplacement — use `()`; those cases are exempt from the paren flag.
3. An unqualified call to a non-member with a dependent argument is an ADL customization point whether intended or not (`T.69`); private helpers live in a `detail` namespace and are called qualified. Unqualified calls remain only where callers are meant to hook in.
4. Do not write unintentionally non-generic code (`T.143`): compare iterators with `!=` not `<`, test emptiness with `empty()`, accept the least-derived type providing what you use — or skip the ceremony entirely with range-`for` where it applies.

```cpp
// Wrong: `last - first` demands random-access iterators; unqualified helper invites ADL surprises.
template <typename It>
std::size_t count_passing(It first, It last) {
    if (last - first == 0) return 0;
    return count_matches(first, last);
}

// Right: forward-iterator friendly; qualified call keeps the helper private.
template <typename It>
std::size_t count_passing(It first, It last) {
    if (first == last) return 0;
    return detail::count_matches(first, last);
}
```

---

## When NOT to Template

Templates exist to express algorithms that apply across many argument types (`T.2`) and containers/ranges over them (`T.3`). Outside those cases they are complexity rented at everyone's expense. Raise the abstraction level when that helps (`T.1`) — but a template is not automatically an abstraction.

| Situation | Reach for |
|-----------|-----------|
| One concrete type suffices today | Plain function or class; generalize when the second type arrives |
| Exactly two known implementations, fixed at build time | Two overloads, or a small class hierarchy |
| Runtime-selected behavior from configuration or input | Virtual interface or type erasure, not compile-time dispatch |
| "Might be generic someday" | Not yet. YAGNI outranks foresight here |
| Algorithm over many numeric/container types | Template, constrained per the previous section |

```cpp
// Wrong: generic ceremony around exactly one type and one caller.
template <typename T>
std::string render_user(const T& user);

// Right: the concrete thing.
std::string render_user(const User& user);
```

Generic-plus-object techniques also combine: a virtual interface externally, templates internally, each paying only its own costs (`T.5`).

---

## Type Erasure versus Templates

When a boundary must accept "anything drawable" or "anything loggable", there are two doors, and the choice is architectural:

| Dimension | Template (`template <class T>`) | Type erasure (`std::function`, custom wrapper, `std::any` with visitors) |
|-----------|--------------------------------|--------------------------------------------------------------------------|
| Dispatch | Compile-time, inlinable | Runtime indirection |
| Heterogeneous containers | No | Yes |
| Header exposure | Implementation usually visible | Interface hides implementations |
| Compile time / binary size | Per-instantiation cost | One compiled body |
| Error discovery | Instantiation time | Compile time for the wrapper; misuse at runtime stays possible |

Defaults (`T.49`): inside a module, on hot paths, with statically known types — templates. Across module boundaries, in plugin seams, in heterogeneous collections — erasure. The guideline's warning stands behind both columns: avoid type-erasure by default, since it buys flexibility at the price of an indirection hidden behind a compilation boundary; the sanctioned exceptions are exactly the cases named above. A hand-rolled erased wrapper (constructor template plus small virtual interior) beats reaching for `std::any` when operations matter:

```cpp
class Task {
public:
    template <typename F>
        requires std::invocable<F&>          // C++17: constrain via static_assert instead
    explicit Task(F&& fn) : impl_(std::make_unique<Model<std::decay_t<F>>>(std::forward<F>(fn))) {
        static_assert(std::is_move_constructible_v<std::decay_t<F>>,
                      "erased callable must be move-constructible");
    }
    void run() { impl_->run(); }
private:
    struct Concept {
        virtual ~Concept() = default;
        virtual void run() = 0;
    };

    template <typename F>
    struct Model final : Concept {
        explicit Model(F fn) : fn_(std::move(fn)) {}
        void run() override { fn_(); }
        F fn_;
    };
    std::unique_ptr<Concept> impl_;
};
```

The deduce-then-decay constructor (`Model<std::decay_t<F>>`) is load-bearing: with the plain `Model<F>`, an lvalue argument deduces `F` to `L&`, and `Model` stores a reference member bound to the caller's object — the first `run()` after the caller's scope exits reads dead memory. Decay forces the copy (or move) that erasure needs, and the `static_assert` names the price: the stored callable must be move-constructible.

One such wrapper is a design; a forest of them is a sign the boundary should have been a plain virtual interface after all.

---

## `if constexpr` over SFINAE and Tag Dispatch

Branching on type properties inside a function body is `if constexpr` territory on C++17 and later. The legacy tools — `enable_if` SFINAE and tag dispatch — survive only for cases `if constexpr` cannot express.

Wrong:

```cpp
// Tag-dispatch overload pair, plus forwarding boilerplate not shown
template <typename It>
auto distance(It first, It last, std::random_access_iterator_tag)
    -> decltype(last - first);
template <typename It>
auto distance(It first, It last, ...) -> std::ptrdiff_t;
```

Right:

```cpp
template <typename It>
auto distance(It first, It last) {
    if constexpr (std::is_base_of_v<std::random_access_iterator_tag,
                                    typename std::iterator_traits<It>::iterator_category>) {
        return static_cast<std::ptrdiff_t>(last - first);
    } else {
        std::ptrdiff_t n = 0;
        for (; first != last; ++first) ++n;
        return n;
    }
}
```

Guidance:

1. Value-based selection between statements in one function: `if constexpr`. Discarded branches are not instantiated, which is precisely what tag dispatch and `enable_if` used to buy.
2. Selecting between *overloads* visible to callers, or constraining a public API: concepts on C++20; on C++17, a traits-based `enable_if` remains acceptable — but hide it behind a descriptive alias.
3. Class-template shape differences still belong to (partial) specialization (`T.64`) — one general interface, specialized implementations for the shapes that need them; `if constexpr` does not replace choosing a different data layout. Irregular types earn the same treatment: Deviation from `T.67`: upstream's entry is largely unwritten, but the usable intent stands — types needing a different representation get a dedicated specialization rather than bending the primary template.
4. Do not specialize function templates — overload or delegate instead (`T.144`); specialization interacts badly with overload resolution and surprises even experts.
5. Deviation from `T.65`: tag dispatch — selecting function implementations from type properties at compile time — is a legitimate technique, but demoted here: `if constexpr` and constrained overloads express the same selection more readably, so tag machinery survives only where those cannot.

```cpp
// Wrong: function template specialization
template <typename T>
const char* name_of();                    // primary
template <>
const char* name_of<int>();               // brittle: ordering, overload interplay

// Right: ordinary overloads
inline const char* name_of(int) { return "int"; }
template <typename T>
inline const char* name_of(T) { return "unknown"; }
```

Caught by: none reliably — reviewers watch for fresh `std::enable_if` and tag-dispatch scaffolding in C++17 code and ask whether `if constexpr` collapses it. clang-tidy flags several related modernization opportunities on changed sources.

---

## CRTP When Appropriate

The Curiously Recurring Template Pattern — `class Derived : Base<Derived>` — buys static polymorphism: shared machinery in a base template, dispatched to the derived class without a vtable. Use it where the derived type is known at compile time and the hot path cannot afford dynamic dispatch or object bloat; the guidelines sanction exactly this mix of OO structure with generic machinery (`T.5`, `C.129`).

Good fits:

- Mixin capabilities added to unrelated classes: comparability, printing, reference counting.
- Compile-time interfaces in embedded/hot loops where a virtual call per element is measurable.
- Enforcing that a base can only operate correctly on its derived type.

```cpp
template <typename Derived>
struct PrintableMixin {
    void print(std::ostream& os) const {
        // Static dispatch to the derived implementation; no vtable involved.
        static_cast<const Derived*>(this)->do_print(os);
    }
};

struct MeterReading : PrintableMixin<MeterReading> {
    int kilowatt_hours = 0;
    void do_print(std::ostream& os) const { os << kilowatt_hours << " kWh"; }
};
```

Costs to weigh honestly: error messages worsen, the inheritance reads backwards to newcomers, and refactoring from CRTP to a runtime hierarchy later touches every derived class. If the set of variants is small and stability of the vtable cost is irrelevant, a plain virtual interface is the boring, correct choice. CRTP is an optimization with a readability price — pay it when static dispatch is measured on a hot path, or when a mixin eliminates per-type virtual machinery without adding a vtable.

Two adjacent rules keep templates and hierarchies out of each other's hair. Do not naively templatize a class hierarchy (`T.80`): parameterizing the base multiplies every virtual into per-instantiation code the compiler must emit whether called or not — keep the base unparameterized and stable, adding type variation in thin derived wrappers. This is what CRTP offers in reverse: linearizing a hierarchy — shared non-virtual base machinery with static dispatch to the leaf (`T.82`) — vtable-free polymorphism paid for with worse errors and backwards-looking inheritance, justified in the declaring header. And respect the hard compiler boundary: a member function template cannot be virtual (`T.83`) — vtables would need link-time generation — so route dynamic behavior through double dispatch, visitors, or computed dispatch instead.

Covered elsewhere: mixing hierarchies and arrays (`T.81`) — a derived array decaying into a base pointer, where element stride differs (`C.152`) — and slicing are owned by [Classes and Hierarchies](./classes-and-hierarchies.md). ABI-stable published interfaces live in [Quality Guidelines](./quality-guidelines.md), whose PIMPL recipe pairs with this guide's non-template-core pattern (stable base plus typed wrapper, `T.84`), sanctioned where instantiation volume meets a frozen interface.

Caught by: review. Nothing mechanical distinguishes justified CRTP from habit.

---

## Variadic Templates

Variadic templates are the tool when a function takes a variable number of arguments of a variety of types (`T.100`) — efficient and type-safe where C varargs are neither; `va_arg` never appears in user code, and enforcement flags it outright. Homogeneous argument lists have precise spellings instead (`T.103`) — `std::initializer_list`, `std::array`, spans — so variadic machinery stays reserved for genuinely mixed-type packs.

Deviation from `T.101`: upstream's entry is a placeholder whose one recorded caution is to beware move-only and reference arguments entering a pack. Working guidance until upstream fills in: forward deliberately (`T&&` plus `std::forward`) and otherwise take copies, so nothing dangles once stored. Deviation from `T.102`: also unfinished upstream, hinting at forwarding, type checking, and references; process pack elements with fold expressions or recursion, validating each against traits or `static_assert` before use rather than trusting the caller.

```cpp
template <typename... Ts>
constexpr auto sum_all(Ts... values) {
    static_assert((std::is_arithmetic_v<Ts> && ...), "sum_all() needs numbers");
    return (values + ... + 0);   // fold expression; no recursion scaffolding
}
```

---

## Template Metaprogramming Is a Last Resort

Template metaprogramming is hard to write, slow to compile, and harder to maintain (`T.120`): deploy it only where it measurably wins or expresses the fundamental idea better than runtime code. Value-shaped results become `constexpr` functions, and TMP hidden inside macros has gone too far. Deviation from `T.4`: upstream's syntax-tree-manipulation entry is an unfinished placeholder; accepted in principle as TMP's legitimate niche, it enters the codebase only through `T.120`'s measured-payoff gate, never as casual cleverness.

Where TMP is unavoidable pre-C++20, its day job is emulating concepts (`T.121`): `enable_if`-selected overloads standing in for constrained ones, retired wholesale once real concepts land. Computing types at compile time belongs to template aliases (`T.122`); classic trait-struct techniques survive mainly inside the standard library itself. Values are computed at compile time by `constexpr` functions (`T.123`) — the conventional, cheaper spelling — and value-yielding TMP gets flagged for replacement; operational detail lives in [Quality Guidelines](./quality-guidelines.md)' Compile-Time Discipline section.

Reach for the standard library's TMP facilities first (`T.124`) — `std::conditional`, `std::enable_if`, `tuple` — because they are portable and universally known; custom machinery must beat them to appear. Deviation from `T.125`: beyond those facilities, prefer an established TMP library to home-grown support — such a dependency carries the usual justification bar, and hand-rolled advanced TMP infrastructure is rejected outright.

---

## Quality Check

Before merging generic code, confirm format-clean (`clang-format --dry-run`) and tidy-clean on changed sources plus a green unit suite:

- [ ] Every new public template has written requirements: a C++20 concept or a C++17 `static_assert` trait check at the top of the definition
- [ ] Constraints describe semantics the algorithm actually needs, no more
- [ ] Template parameter lists contain no parameter removable without losing generality
- [ ] No new `std::enable_if`, tag dispatch, or function-template specialization where `if constexpr`, overloads, or concepts express it
- [ ] Type erasure introduced only where heterogeneous storage or a hidden-implementation boundary demands it
- [ ] CRTP additions carry a justification (hot-path dispatch, mixin reuse) in the declaring header
- [ ] New templates compile warning-clean under at least two compilers

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
