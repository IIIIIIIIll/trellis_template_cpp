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
T median(std::vector<T>& values);

median("oops");   // 40 lines of errors ending somewhere useful, allegedly
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

1. Constrain every public template. The guideline phrased positively — state the requirements of each template argument up front (`T.10`) — is the whole section in one sentence. A pile of unrelated, barely-related parameters is a smell too (`T.11`): split the function instead of listing five type knobs.
2. A constraint must carry meaning, not just syntax. Requiring "has `size()`" says almost nothing; requiring "a range whose size query is O(1)" is a requirement. Concepts without semantics are documentation-shaped noise (`T.20`).
3. Prefer one concept over `enable_if` gymnastics wherever the dialect allows (`T.26`). Keep legacy SFINAE quarantined behind a named alias if it must exist.
4. Constrain to what the algorithm uses, nothing more (`T.46` asks for Regular-or-ordering arguments where applicable): do not demand `operator<<` inside a sorting routine because some caller once debugged through it.
5. An unconstrained template with a common, attractive name (`swap`, `begin`, `hash`) hijacks overload resolution far beyond its home directory; give such helpers a constrained or namespaced spelling (`T.47`).

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

Defaults: inside a module, on hot paths, with statically known types — templates. Across module boundaries, in plugin seams, in heterogeneous collections — erasure. A hand-rolled erased wrapper (constructor template plus small virtual interior) beats reaching for `std::any` when operations matter:

```cpp
class Task {
public:
    template <typename F>
        requires std::invocable<F&>          // C++17: constrain via static_assert instead
    explicit Task(F&& fn) : impl_(std::make_unique<Model<F>>(std::forward<F>(fn))) {}
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
2. Selecting between *overloads* visible to callers, or constraining a public API: concepts on C++20 (`T.26`); on C++17, a traits-based `enable_if` remains acceptable — but hide it behind a descriptive alias.
3. Class-template shape differences still belong to (partial) specialization; `if constexpr` does not replace choosing a different data layout.
4. Do not specialize function templates — overload or delegate instead (`T.144`); specialization interacts badly with overload resolution and surprises even experts.

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

Costs to weigh honestly: error messages worsen, the inheritance reads backwards to newcomers, and refactoring from CRTP to a runtime hierarchy later touches every derived class. If the set of variants is small and stability of the vtable cost is irrelevant, a plain virtual interface is the boring, correct choice. CRTP is an optimization with a readability price — pay it only where the profiler or a hard binary-size budget says so.

Caught by: review. Nothing mechanical distinguishes justified CRTP from habit.

---

## Quality Check

Before merging generic code, confirm:

```bash
cmake --preset default && cmake --build --preset default
ctest --preset default --output-on-failure

# Static analysis on changed sources
clang-tidy -p build/default path/to/changed.cpp
```

- [ ] Every new public template has written requirements: a C++20 concept or a C++17 `static_assert` trait check at the top of the definition
- [ ] Constraints describe semantics the algorithm actually needs, no more
- [ ] Template parameter lists contain no parameter removable without losing generality
- [ ] No new `std::enable_if`, tag dispatch, or function-template specialization where `if constexpr`, overloads, or concepts express it
- [ ] Type erasure introduced only where heterogeneous storage or a hidden-implementation boundary demands it
- [ ] CRTP additions carry a justification (hot-path dispatch, mixin reuse) in the declaring header
- [ ] New templates compile in the two-compiler CI matrix without warnings

---

## Complete Coverage: T

Every remaining rule ID from the Guidelines' T section, each with an explicit stance so the mapping contains no silent gaps. Vocabulary follows Core Guidelines Alignment; dialect notes resolve to the C++17 baseline with C++20 spellings preferred where available.

| Rule | Stance | Disposition |
|------|--------|-------------|
| `T.4` | Adapt | Upstream placeholder — Reason and Example are unfinished. Accepted in principle: compile-time syntax-tree manipulation is TMP's legitimate niche, but it enters the codebase only through the measured-payoff gate of `T.120`, never as casual cleverness |
| `T.12` | Adapt | A bare `auto` is the weakest possible concept; where a fitting concept exists and the toolchain speaks C++20, prefer the constrained spelling. On the C++17 baseline the notation does not exist and plain `auto` stays acceptable |
| `T.13` | Adapt | Prefer the shorthand for simple single-type-argument concepts — `template<Sortable T>`, or `Sortable auto&&` — because it reads the way we speak. Applies on C++20; the C++17 fallback remains the traits-based `static_assert` spelled out under Document Requirements with Concepts |
| `T.21` | Adopt | A concept must require a coherent, complete set of operations: `Subtractable` alone is meaningless without `+`, and comparison comes as the full six-operator set. Flag odd subsets such as `==` without `!=` — surprising for users and sometimes slower |
| `T.22` | Adopt | Concepts carry axioms — the mathematical assumptions (`a - a == 0`, distributivity) written as comments beside the `requires` clause until language support exists. An axiom is assumed like a precondition; early experimental concepts may ship incomplete, but are then explicitly not stable |
| `T.23` | Adopt | Refine by adding use patterns: a forward iterator is an input iterator plus suffix `++`, so the compiler derives subsumption from requirement sets alone. Two concepts with identical requirements are equivalents, not a hierarchy |
| `T.24` | Adopt | When two concepts differ only in semantics, separate them with a trait or tag class — contiguous is random-access plus `is_contiguous_v` — preferring standard-library traits and wrapping the trait back into a named concept |
| `T.25` | Adopt | Never write complementary `requires C<T>` / `requires !C<T>` pairs; provide an unconstrained primary plus a constrained refinement (or delete the primary). `enable_if` code commits this habit routinely, and two constraints already explode into four definitions |
| `T.40` | Adopt | Pass operations to algorithms as function objects — lambdas included — which carry state through the interface and inline well, rather than function pointers; enforcement flags function-pointer template arguments |
| `T.41` | Adopt | Require only what the algorithm essentially needs: debug streamability does not belong in `sort`'s concept. Deliberately leaving non-essential operations unchecked delays their failure to instantiation time — the price of a stable interface, and worth paying |
| `T.43` | Adopt | `using` aliases over `typedef`: the new name leads, the syntax parallels `auto`, and only `using` can form template aliases. Expect enforcement to flag legacy `typedef`s widely |
| `T.48` | Adapt | Without concept support, the guideline's best emulation is `enable_if` — with the warning that it drags in complementary-constraint designs. Our C++17 dialect prefers `static_assert` trait checks for stating contracts and quarantines SFINAE behind named aliases for genuine overload selection |
| `T.49` | Adopt | Type erasure buys flexibility at the price of an indirection hidden behind a compilation boundary; avoid it by default. Sanctioned exceptions map onto this guide's erasure-versus-template defaults: plugin seams, heterogeneous storage, `std::function`-style needs |
| `T.64` | Adopt | Class-template alternatives come from specialization: one general interface, specialized implementations for the shapes that need them — consistent with the `if constexpr` section's rule that data-layout changes stay specializations |
| `T.65` | Adapt | Tag dispatch selects function implementations from type properties at compile time — legitimate technique, demoted here: `if constexpr` and constrained overloads express the same selection more readably, so tag machinery survives only where those cannot |
| `T.67` | Adapt | Upstream content is largely unwritten; the usable intent is that types needing a different representation earn a dedicated specialization (the mechanism of `T.64`) rather than bending the primary template |
| `T.68` | Adopt | Inside templates prefer `{}` initialization: `()` invites both the parse where `T v1(T(u))` declares a function and silent casts like `f(1, "asdf")`. Braced form states variable-hood outright; enforcement flags paren initializers and function-style casts |
| `T.69` | Adopt | An unqualified call to a non-member with a dependent argument is an ADL customization point whether intended or not; private helpers live in a `detail` namespace and are called qualified. Unqualified calls remain only where callers are meant to hook in |
| `T.80` | Adopt | Templatizing a hierarchy multiplies every virtual into per-instantiation code the compiler must emit whether called or not. Keep the base unparameterized and stable; add type variation in thin derived wrappers |
| `T.81` | Covered elsewhere | Array-of-derived decaying into a base pointer is owned by [Classes and Hierarchies](./classes-and-hierarchies.md) — never point a base pointer into a derived array, element stride differs (`C.152`) — with slicing handled in the same guide |
| `T.82` | Adopt | Linearizing a hierarchy — shared non-virtual base machinery with static dispatch to the leaf — is this guide's CRTP charter exactly: vtable-free polymorphism where dispatch cost matters, paid for with worse errors and backwards-looking inheritance, so justify it in the declaring header |
| `T.83` | Adopt | A member function template cannot be virtual — the compiler rejects it, since vtables would need link-time generation. Route dynamic behavior through double dispatch, visitors, or computed dispatch instead |
| `T.84` | Covered elsewhere | ABI-stable published interfaces live in [Quality Guidelines](./quality-guidelines.md): PIMPL for binary-shipped headers. The non-template-core pattern (stable base plus typed wrapper) follows the same principle and stays sanctioned where instantiation volume meets a frozen interface |
| `T.100` | Adopt | Variadic templates are the tool for functions taking varied types in varying counts — efficient and type-safe. C varargs never appear in user code; enforcement flags `va_arg` outright |
| `T.101` | Adapt | Upstream placeholder whose one recorded caution is to beware move-only and reference arguments entering a pack. Working guidance until upstream fills in: forward deliberately (`T&&` plus `std::forward`) and otherwise take copies so nothing dangles once stored |
| `T.102` | Adapt | Also unfinished upstream, hinting at forwarding, type checking, and references. Process pack elements with fold expressions or recursion, validating each against traits or `static_assert` before use rather than trusting the caller |
| `T.103` | Adopt | Homogeneous argument lists have precise spellings — `initializer_list`, `std::array`, spans — so variadic machinery is reserved for genuinely mixed-type packs |
| `T.120` | Adopt | Template metaprogramming is hard to write, slow to compile, and harder to maintain; deploy it only when it measurably wins or expresses the fundamental idea better than runtime code. Value-shaped results become `constexpr` functions, and TMP hidden inside macros has gone too far |
| `T.121` | Adopt | Where TMP is unavoidable pre-C++20, its day job is emulating concepts: `enable_if`-selected overloads standing in for constrained ones. Real concepts retire that scaffolding entirely |
| `T.122` | Adopt | Computing types at compile time belongs to template aliases; classic trait-struct techniques survive mainly inside the standard library itself |
| `T.123` | Adopt | Values are computed at compile time by `constexpr` functions — the conventional, cheaper spelling; value-yielding TMP gets flagged for replacement. Operational detail lives in Quality Guidelines' Compile-Time Discipline section |
| `T.124` | Adopt | Reach for the standard library's TMP facilities first — `conditional`, `enable_if`, `tuple` — because they are portable and universally known; custom machinery has to beat them to appear |
| `T.125` | Adapt | Beyond the standard facilities, prefer an established TMP library to home-grown support. Locally, adopting such a dependency carries the usual justification bar, and hand-rolled advanced TMP infrastructure is rejected outright |
| `T.143` | Adopt | Do not commit accidentally to specifics in generic code: compare iterators with `!=` not `<`, test emptiness with `empty()`, accept the least-derived type providing what you use — or skip the ceremony with range-`for` where it applies |
| `T.150` | Adopt | When a class claims to model a concept, prove it early with `static_assert(Modelable<T>)` — the same idiom this guide mandates inside template bodies, pointed at concrete model types. Enforcement is review-visible and cheap |

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
