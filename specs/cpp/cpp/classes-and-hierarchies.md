# Classes and Hierarchies

> Type design for C++: concrete types by default, special-member discipline (Rule of Zero, Rule of Five), polymorphic-base obligations, and hierarchies that are earned rather than assumed.

---

## Overview

Most defects in type design come from two opposite failures: writing special members the compiler already generates correctly, and reaching for inheritance where a struct plus free functions would do. This document fixes the ladder — concrete value types first, five-member types only for manual resources, hierarchies only for open variation — plus the obligations a virtual base can never skip.

Parameter conventions live in [Functions and Interfaces](./functions-and-interfaces.md); ownership of what members hold lives in [Memory and Ownership](./memory-and-ownership.md). Baseline is C++17.

---

## Concrete Types First

Start as a concrete type: copyable, assignable, equality-comparable, no virtuals (`C.10`). Regular types behave like `int` — independent copies, replace-on-assign — and that predictability beats speculative extensibility (`C.11`).

| Situation | Shape |
|-----------|-------|
| Related data, no invariant | `struct`, public members, in-class initializers (`C.2`) |
| Data plus invariant | `class`; constructor establishes the invariant |
| Manual resource inside | Rule of Five (below) |
| Behavior varies over an *open* implementation set | Abstract interface + hierarchy (below) |

```cpp
// Wrong: a hierarchy for a closed set of two — vtables, heap copies, clone plumbing.
class Shape { public: virtual ~Shape() = default; virtual double area() const = 0; };

// Right: closed variation is a tag; dispatch is a branch, not a virtual call.
struct Shape {
    enum class Kind { Square, Circle } kind;
    double side_or_radius;
    [[nodiscard]] double area() const;
};
```

Reach for a hierarchy only when implementations are added by code you never see, across module boundaries you do not compile together. Closed variation inside one module is one `std::variant` away from being simpler.

Caught by: review; over-design surfaces later as maintenance drag, not as warnings.

---

## The Rule of Zero Is the Default

A type managing no resources by hand declares **none** of the five special members (`C.21` — the stance its rationale calls the Rule of Zero). RAII members and in-class initializers supply correct copy, move, and destruction semantics for free.

```cpp
// Wrong: members written to do exactly what the compiler would have done.
class Settings {
public:
    Settings(const Settings& o) : retries_(o.retries_), host_(o.host_) {}
    Settings& operator=(const Settings& o) { retries_ = o.retries_; host_ = o.host_; return *this; }
private:
    int retries_ = 3;
    std::string host_ = "localhost";
};

// Right: nothing declared, nothing to get wrong.
class Settings {
private:
    int retries_ = 3;
    std::string host_ = "localhost";
};
```

Every `std::string`, `std::vector`, or `unique_ptr` member already carries correct copy/move/destruction. Hand-written special members on such a type add only opportunities to forget one.

---

## Rule of Five When Resources Are Manual

Managing a raw resource directly — descriptor, handle, heap block outside a smart pointer — means defining **all five** or deleting them explicitly (`C.21`). Defining one while defaulting another is how double-frees happen. The destructor releases and never throws (`C.30`, `C.36`); moves steal the guts, leave the source empty-but-destructible, and are `noexcept` so container growth actually moves (`C.64`, `C.66`).

```cpp
class FileDesc {
public:
    explicit FileDesc(int fd) : fd_(fd) {}
    ~FileDesc() { if (fd_ >= 0) ::close(fd_); }

    FileDesc(const FileDesc& o) : fd_(::dup(o.fd_)) {}      // deep copy
    FileDesc& operator=(const FileDesc& o) {              // deep, self-safe
        if (this != &o) {
            if (fd_ >= 0) ::close(fd_);
            fd_ = ::dup(o.fd_);
        }
        return *this;
    }

    FileDesc(FileDesc&& o) noexcept : fd_(std::exchange(o.fd_, -1)) {}
    FileDesc& operator=(FileDesc&& o) noexcept {
        std::swap(fd_, o.fd_);                            // old fd closed by o's destructor
        return *this;
    }

private:
    int fd_ = -1;                                           // "empty" is representable
};
```

First re-check [Memory and Ownership](./memory-and-ownership.md): a `unique_ptr<T, Deleter>` deletes this entire class. Rule of Five is the fallback for resources standard wrappers cannot express, not the default.

Caught by: ASan/LSan expose missing destructors and double closes; clang-tidy special-member checks flag partial fives.

---

## `=default` and `=delete` Say What You Mean

Want generated behavior but must state it (out-of-line destructor, restored moves)? `=default` (`C.80`). Want behavior not to exist? `=delete` — on any function, not just special members (`C.81`).

```cpp
// Wrong: deleted copy silently suppresses move too — SessionBad is immovable,
// and nothing in this header says so.
class SessionBad {
public:
    SessionBad(const SessionBad&) = delete;
};

// Right: all five decided, in order, visible to reviewers.
class Session {
public:
    Session() = default;
    Session(const Session&) = delete;
    Session& operator=(const Session&) = delete;
    Session(Session&&) = default;
    Session& operator=(Session&&) = default;
private:
    std::unique_ptr<Conn> conn_;
};
```

The rule is symmetric (`C.21`): touching any special member means deciding all five. Caught by: clang-tidy `cppcoreguidelines-special-member-functions`; `-Wdeprecated-copy` for half-defined cases.

---

## Polymorphic Bases Carry Obligations

Deleting a derived object through a base pointer whose destructor is non-virtual is undefined behavior — the derived destructor never runs (`C.35`, `C.127`). Every polymorphic base therefore picks exactly one legal shape:

| Base role | Destructor | Copies |
|-----------|------------|--------|
| Interface, deleted polymorphically | `public virtual` | `=delete` (`C.67`) |
| Mixin, never deleted through base pointer | `protected`, non-virtual | `=delete` |

```cpp
struct Base {
    ~Base();                          // Wrong: public, non-virtual
    virtual void run();
};
Base* b = new Impl;
delete b;                             // UB: ~Impl never runs; derived state leaks

struct GoodBase {
    virtual ~GoodBase() = default;    // Right: public virtual, safe polymorphic delete
    GoodBase(const GoodBase&) = delete;
    GoodBase& operator=(const GoodBase&) = delete;
    virtual void run() = 0;
};
```

Spelling: overrides say `override`; leaves sealing the hierarchy say `final`; a declaration carries exactly one of `virtual`/`override`/`final`, never two (`C.128`). Virtual functions never declare default arguments — defaults bind statically while dispatch is dynamic, so callers disagree depending on static type (`C.140`).

Caught by: clang-tidy `cppcoreguidelines-virtual-class-destructor`; ASan reports leaked derived subobjects.

---

## Composition Before Inheritance

Inheritance models **is-a** over an open set (`C.120`). Implementation reuse is composition's job: a member function earns membership only through direct access to the representation (`C.4`), and helpers live beside the type in its namespace (`C.5`).

| Smell | Verdict |
|-------|---------|
| Base exists mainly to share protected helpers | Flatten into free functions |
| Convenience base with no polymorphic use sites | Delete it |
| Virtual nobody overrides past the leaf | De-virtualize (`C.132`) |
| Callers hold base pointers they cannot spell | Genuine interface — keep |

```cpp
// Wrong: three layers whose only job is sharing format_timestamp().
class Logger {
protected:
    std::string format_timestamp() const;
};

namespace logfmt {                    // Right: reusable without any inheritance
    [[nodiscard]] std::string format_timestamp(std::chrono::system_clock::time_point tp);
}
class LogSink {                       // Right: genuine interface, composition point
public:
    virtual ~LogSink() = default;
    virtual void write(std::string_view line) = 0;
};
class FileSink final : public LogSink { /* uses logfmt:: helpers */ };
```

Chains beyond roughly three levels without interface users at the top are refactoring backlog, not architecture.

---

## Abstract Interfaces Have No State

An interface is pure protocol: no data members, no constructor logic, virtual destructor, deleted copies (`C.122`). Data inside an abstract type forces every implementation into one layout — a base class wearing an interface's name.

```cpp
class Codec {
public:
    virtual ~Codec() = default;
    Codec() = default;                                  // no state, no ctor logic
    Codec(const Codec&) = delete;
    Codec& operator=(const Codec&) = delete;

    [[nodiscard]] virtual Bytes encode(BytesView raw) const = 0;
    [[nodiscard]] virtual std::string_view name() const = 0;
};
// Forbidden in interfaces: protected data, constructors with logic, any field at all.
```

Edge rules:

1. Hold and pass polymorphic objects by pointer or reference — by value slices (`C.145`; enforced by the signature tables in [Functions and Interfaces](./functions-and-interfaces.md)).
2. Never point a base pointer into an array of derived objects; element stride differs (`C.152`).
3. Prefer virtual dispatch; `dynamic_cast` only where navigation between siblings is genuinely unavoidable (`C.146`), reference form when absence of the target is an error.
4. Copying goes through a virtual `clone()` returning `std::unique_ptr<Codec>`, never through base-reference copy construction.

Caught by: clang-tidy `cppcoreguidelines-slicing`.

---

## Protected Data Is a Liability

Protected data members give every subclass — present and future — a vote on the base invariant (`C.133`). Protected **hook functions** upholding invariants are fine; protected **fields** are not.

```cpp
class RingBuffer {
protected:
    std::vector<int> buf_;                        // Wrong: SpyRing can bypass push()
    size_t tail_ = 0;
};
class SpyRing : public RingBuffer {
public:
    void poke(int v) { buf_[tail_++] = v; }       // skips capacity checks; corrupts state
};

class GuardedRing {                               // Right: one guarded mutation path
public:
    void push(int v);
protected:
    [[nodiscard]] const std::vector<int>& snapshot() const noexcept { return buf_; }
private:
    std::vector<int> buf_;
    size_t tail_ = 0;
};
```

Variant behavior belongs behind protected methods whose base implementation enforces the invariant — extension points are functions, not fields.

---

## Close Hierarchies with `final`

Seal classes whose hierarchy is deliberately closed (`C.128`): reviewers get warned before extending what was designed shut, and the compiler may de-virtualize hot calls.

```cpp
class HttpTransport : public Transport {};   // Wrong: open by omission — subclasses can
                                             // later bypass the timeout invariants
class HttpTransport final : public Transport {};   // Right: sealed leaf
```

Do not sprinkle `final` on documented extension points — seal what would break invariants, leave open contracts open.

---

## Quality Check

```bash
cmake --preset default && cmake --build --preset default
ctest --preset default --output-on-failure
clang-tidy -p build/default path/to/changed.cpp

# Hierarchy changes touch lifetime edges; repeat under sanitizers.
cmake --preset asan && cmake --build --preset asan
ctest --preset asan --output-on-failure
```

Review checklist:

- [ ] New types start concrete; hierarchies only behind genuinely open variation
- [ ] Resource-free types declare none of the five; partial fives completed or deleted (`C.21`)
- [ ] Manual-resource types release in destructors, deep-copy on copy, move `noexcept`
- [ ] Polymorphic bases: public virtual or protected non-virtual destructor; copies deleted
- [ ] Overrides spelled `override`; `final` only on deliberately sealed leaves
- [ ] Interfaces carry no fields and no constructor logic; no `protected` data anywhere
- [ ] Implementation reuse via composition and free functions; inheritance is is-a only
- [ ] Polymorphics passed/stored by reference or pointer — no slicing, no base pointers into arrays

---

## Complete Coverage: C

The narrative sections cite the load-bearing `C.*` rule IDs inline; the table below gives every remaining Guidelines section-C rule an explicit disposition. `Adopt` follows the rule as written, `Adapt` records a documented local difference, `Covered elsewhere` routes the substance to the sibling guide that owns it. Rows also flag where a rule above was already enforced without its ID named.

| Rule | Stance | Disposition |
|------|--------|-------------|
| `C.1` | Adopt | Related data travels as one type, not parallel loose parameters (`draw(x, y, x2, y2)` becomes two `Point`s); a simple class without virtuals adds no space or time overhead. |
| `C.3` | Adopt | Keep public interface and private representation apart inside one class so the representation can change without touching users; namespaces of free functions, abstract bases, or concept-constrained templates are equally valid spellings — the point is an explicit, stable seam. |
| `C.7` | Adopt | Never define a class or enum and declare a variable of it in the same statement (`struct Data { /*...*/ } data{/*...*/};`); split them. Upstream enforcement flags a missing semicolon after a type definition's closing brace. |
| `C.8` | Adopt | Any non-public member makes the spelling `class`, so the keyword itself announces that something is hidden; keep the public interface first inside the body. |
| `C.9` | Adopt | Minimize member exposure: data participating in an invariant is private, reachable only through checked operations; the checked-public / unchecked-protected hook pattern is acceptable; order members public before protected before private. |
| `C.12` | Adopt | No `const`, `&`, or `&&` data members in a type with any copy or move operation — they leave it copy-constructible but silently non-assignable; point instead (raw or smart pointer, `gsl::not_null` where null is excluded). |
| `C.13` | Adopt | A member using another member is declared after it: initialization follows declaration order and destruction reverses it, so the user would touch its dependency outside the dependency's lifetime. The same discipline joins asynchronous work before the data it accesses dies. |
| `C.20` | Adopt | If you can avoid defining default operations, do — this doc's Rule of Zero section states the stance without citing the ID. The analyzer-detectable smell is a hand-written `(pointer, size)` pair plus deleting destructor begging to become a container. |
| `C.22` | Adopt | Default operations are a matched set: copy construction that deep-copies while assignment shallow-copies surprises every user. Worth internalizing upstream's heuristics — copy/move pairs write the same members at the same dereference level; destructor-modified members appear in every copy/move path. |
| `C.31` | Adopt | Companion to C.30: once a class acquires resources, the destructor releases everything acquired, error paths included. Non-owned pointers/references are exempt from deletion; close failures are design errors to terminate on, since release operations rarely retry. Enforced by the Rule of Five section without this ID. |
| `C.32` | Covered elsewhere | Whether a raw member pointer or reference owns is decided outright by [Memory and Ownership](./memory-and-ownership.md): owning raw pointers are banned in favor of `unique_ptr`, containers, or RAII guards, and references never own — stricter than upstream's "consider whether it might own". |
| `C.33` | Adopt | A member owning through a raw pointer forces a destructor — and defining one obligates deciding all five operations, or the generated copy double-deletes. Simplest cure is replacing the pointer with a smart pointer; ABI friction is the acknowledged reason legacy code keeps raw owners. Enforced by the Rule of Five without this ID. |
| `C.37` | Adopt | Destructors are implicitly `noexcept` only when every member's destructor is, so one throwing member poisons the whole hierarchy — declare `noexcept` explicitly to freeze the contract against future members; blanket decoration is clutter even upstream declines to mandate. |
| `C.40` | Adopt | A class with an invariant gets a constructor whose job is establishing it (`Ensures` states the invariant cleanly); convenience constructors on invariant-free types remain fine, and brace-init lists retire many redundant ones. Enforced by the Concrete Types table's "constructor establishes the invariant" row without this ID. |
| `C.41` | Adopt | Every constructor delivers a fully initialized, usable object — no `init()`-before-use protocol, because compilers do not read comments; each member reaches initialized state explicitly, via delegation, or via defaults. Constructor-acquires/destructor-releases is RAII itself. |
| `C.42` | Adopt | A constructor that cannot build a valid object throws — no half-built object behind an `is_valid()` check users will forget. Hard-real-time domains get the exception, and must then check immediately and consistently; two-stage initialization stays rejected, delegating constructors and member initializers being better at its job. |
| `C.43` | Adapt | Copyable types complete the semiregular set with a default constructor — `vector<Date>(1000)` needs one — but only where a meaningful state exists: upstream argues against fake defaults like `{0, 0, 0}` dates and exempts bases and caller-provided-resource types such as `lock_guard`. Remember built-in members stay uninitialized unless given `{}` initializers. |
| `C.44` | Adopt | Prefer default constructors that cannot throw or allocate: an empty `{nullptr, nullptr, nullptr}` state is cheap to establish, trivial to restore after errors, and keeps arrays of the type inexpensive; throwing default constructors are flagged upstream. |
| `C.45` | Adopt | Do not write a default constructor that only assigns constants to members — put those constants in default member initializers and let the compiler generate the function. The Concrete Types table and Rule of Zero examples lean on this idiom without citing it. |
| `C.50` | Adopt | Virtual behavior during initialization moves into a factory: a protected-token constructor keeps imperfectly built objects from escaping while a static `create()` calls `post_initialize()`, where virtual dispatch is safe. Return `unique_ptr` by default; `shared_ptr` only when sharing is certain. |
| `C.51` | Adopt | Common constructor actions — validation especially — live once in the most complete constructor, and the others delegate rather than retype it and drift; upstream enforcement hunts similar-looking constructor bodies. |
| `C.52` | Adopt | `using Rec::Rec;` imports constructors into a derived class adding no data of its own, instead of reimplementing tricky ones. The canonical failure is the inherited constructor leaving a newly added derived member uninitialized — every derived member still needs an initializer. |
| `C.60` | Adopt | Copy assignment is non-virtual, takes `const&`, returns `T&` for chaining; the copy-and-swap shape provides the strong guarantee and ignores self-assignment. If hierarchy assignment truly beckons, name it `assign()` — a virtual `operator=` is dragons. |
| `C.61` | Adopt | A copy operation should copy: after `x = y`, `x == y`. Value semantics is the default posture; deliberate shallow "pointer semantics" is legal but must be coherent end to end, equality included. |
| `C.62` | Adopt | Self-assignment must not change the value. Member-wise assignment of well-behaved members makes the `this == &a` guard unnecessary — the branch-predictor economics favor handling the million-to-one case correctly by construction. |
| `C.63` | Adopt | Move assignment mirrors copy assignment: non-virtual, parameter by `&&`, return `T&`; base and member move assignments run implicitly or explicitly. |
| `C.65` | Adopt | Self-move is rare but reachable (`std::swap(a, a)`), so move assignment must leave the object valid; guaranteeing the value is literally unchanged requires the guard test, while null-out-then-delete-then-restore achieves safety without one. Upstream insists on more safety than the standard's valid-but-unspecified container promise. |
| `C.82` | Adopt | Virtual calls in constructors and destructors dispatch on the type constructed so far — the override never fires — and calling a pure virtual there is undefined behavior; qualified names (`Derived::g()`) honestly call the visible version, and factories deliver post-construction virtual effects safely. |
| `C.83` | Adopt | Value-like types provide a member `noexcept swap` plus a free two-argument overload in the same namespace — the machinery behind copy-assign-via-swap and guaranteed commit points. |
| `C.84` | Adopt | Swap must not fail: element-copying swap implementations both crawl and break standard-library algorithms that assume element swap succeeds. |
| `C.85` | Adopt | Therefore swap is declared `noexcept` — unwinding out of a swap is a design error the program should not survive quietly. |
| `C.86` | Adopt | `==` treats operands symmetrically (free function, matching parameter types) and is `noexcept`; a member `operator==` accepts conversions for its right operand only. Applies across the comparison operators; failure states prefer comparing equal to themselves and false against valid values over throwing. |
| `C.87` | Adopt | Beware `==` on base classes: a virtual `operator==` sees derived state or not depending on the static operand type, and naive fixes do not scale — flag virtual comparison operators through `<=>`. |
| `C.89` | Adopt | Hash specializations are `noexcept` — hashed-container users never expect access to throw; xor-combining standard-library hashes beats cleverness for non-specialists. |
| `C.90` | Adopt | Initialization and copying happen through constructors and assignment operators, never `memset`/`memcpy`: both overwrite vtables, and `memcpy` of a non-trivially-copyable type is undefined behavior. |
| `C.100` | Adapt | Custom containers follow STL conventions — conventional constructors, assignments, iterators, semantics — though partial conformance is respectable. Local difference: containers are normally bought, not written; authoring one carries the justification burden the ownership ladder places on bypassing the standard library. |
| `C.101` | Adopt | Containers give value semantics — Regular in the concept sense, a copy comparing equal to its original — so they reason like `int`. |
| `C.102` | Adopt | Containers get move operations: large immovable types tempt pointer-passing and its resource bugs, and callers reasonably assume returning a container by value is cheap. |
| `C.103` | Adopt | Containers take an initializer-list constructor so `{1, 3, -1, 7}` builds element sets as expected. |
| `C.104` | Adopt | A container's default constructor yields empty, completing Regularity — `vector<Sorted_seq<string>> vs(100)` produces a hundred usable elements. |
| `C.109` | Adopt | A resource handle with pointer semantics provides `*` and `->` — familiarity is the entire argument; upstream supplies no further example or enforcement. |
| `C.121` | Adopt | A base used as an interface is a pure abstract class: public pure virtual functions plus a virtual destructor, zero data — data-free interfaces stay stable. Already enforced above under the C.122 citation; upstream's leak example (missing virtual destructor drops the derived `string`) is that section's founding motivation. |
| `C.126` | Adopt | Abstract classes typically skip user-written constructors — no data exists to initialize. Exceptions: base constructors that do work (registration) and the rare shared-statistics data that tends to drag the hierarchy toward virtual inheritance. |
| `C.130` | Adopt | Deep-copy polymorphic types through a virtual `clone()` with covariant owner return, copy/move demoted to protected defaulted helpers serving clone implementations; public copy construction/assignment stays suppressed. Covariant smart pointers are impossible, so return `unique_ptr<Base>` uniformly or use `gsl::owner`. Edge rule 4 in Abstract Interfaces describes clone without this ID. |
| `C.131` | Adopt | Getters/setters indistinguishable from a public field beyond syntax add nothing — make the type a `struct` with public data instead. Accessors earn their keep by maintaining invariants or converting representations. |
| `C.134` | Adopt | All non-`const` data members share one access level: invariant-free members go public (the type is really a `struct`), invariant-bearing members go private or `const`; debug instrumentation is the acknowledged mixed case. Sharpens C.8 and C.9 into a mechanically checkable form. |
| `C.135` | Adopt | Multiple inheritance represents multiple distinct interfaces — breaking monolithic APIs into aspects (`iostream` unioning `istream` and `ostream`), typically with abstract bases. |
| `C.136` | Adapt | State-carrying implementation mixins (`enable_shared_from_this`, intrusive hooks) are upstream's rare sanctioned multiple inheritance. Here they pass review only where the mixin injects customization points or erases forwarding boilerplate; otherwise Composition Before Inheritance governs. |
| `C.137` | Adapt | Virtual bases separate shared implementation data (`virtual protected Utility`) from an interface root, keeping shared state out of one overly general god-base. Upstream concedes hierarchy linearization is often better; locally, reaching for a virtual base at all starts the flattening conversation. |
| `C.138` | Adopt | A derived member hides its bases' entire same-named overload sets — `d.f(2.3)` quietly calls `f(int)` — so `using B::f;` restores them, for virtual and non-virtual alike; C++17's variadic `using Ts::operator()...` powers the overloader idiom. |
| `C.139` | Adopt | `final` on classes is used sparingly and deliberately: sealing is a decision about extension, performance claims require substantiation, and misuses historically outnumber wins. Close Hierarchies above already carries the "do not sprinkle final" caveat without this ID. |
| `C.147` | Adopt | Use `dynamic_cast<T&>` when absence of `T` is an error: a reference cast throws on failure, declaring the intent to end up with a valid object. Extends the reference-form guidance already given under C.146 without this ID. |
| `C.148` | Adopt | Use `dynamic_cast<T*>` when absence is a valid alternative: null enables branching, and the result is always tested before dereference. The contrast stands — the reference form never substitutes for conditional logic. Across module boundaries, Quality Guidelines replaces RTTI with kind tags outright. |
| `C.149` | Covered elsewhere | Objects created with `new` are never handed to naked pointers; [Memory and Ownership](./memory-and-ownership.md) owns the rule: creation goes through `make_unique`/`make_shared`, owners are `unique_ptr`, containers, or RAII guards. |
| `C.150` | Covered elsewhere | `make_unique()` constructs everything a `unique_ptr` owns; the rule lives in [Memory and Ownership](./memory-and-ownership.md)'s creation ladder (upstream defers to R.23). |
| `C.151` | Covered elsewhere | `make_shared()` constructs everything a `shared_ptr` owns — exception safety plus a single allocation; likewise owned by [Memory and Ownership](./memory-and-ownership.md) (upstream defers to R.22). |
| `C.153` | Adapt | Prefer the virtual call: it lands on the most-derived override, while a cast may stop at an intermediate class and rot as the hierarchy evolves. Local difference: closed variation replaces both sides with kind-tag dispatch (Concrete Types First), reserving `dynamic_cast` for genuinely open navigation per C.146-C.148. |
| `C.160` | Adopt | Define operators primarily to mimic conventional usage — `+` adds, copies compare equal — because invented semantics tax every reader; non-member operators are friends or live with their operands. |
| `C.161` | Adopt | Symmetric operators are non-members: a member `operator==` converts arguments on one side only, making `a == b` and `b == a` subtly differ. Pairs with C.86's symmetry and `noexcept` requirements. |
| `C.162` | Adopt | Overload for roughly equivalent operations: one `print` name across argument types instead of `print_int`/`print_string` — encoded type names add verbosity and inhibit generic code. Complement of C.163. |
| `C.163` | Adopt | Overload only for roughly equivalent operations: `open(Gate&)` and `open(const char*, const char*)` collide confusingly despite the type system's partial rescue; watch popular names — `open`, `move`, `+`, `==`. |
| `C.164` | Adopt | Avoid implicit conversion operators — surprises range from unintended calls to dangling pointers into destroyed temporaries; conversions stay explicit until a fundamental, frequently needed case is demonstrated. Every non-explicit conversion operator is flagged upstream. |
| `C.165` | Adopt | Find customization points through `using`: `using std::swap;` before an unqualified call picks up `N::swap` when present and falls back to `std::swap` — precisely how generic code discovers C.83's free overloads. |
| `C.166` | Adopt | Overload unary `&` only inside a coherent smart-pointer/reference system whose `->`, `*`, and `[]` agree — `.` cannot be overloaded, so perfection is impossible, and `std::addressof` always recovers the built-in pointer. |
| `C.167` | Adopt | Use an operator only for its conventional meaning: `operator<<` composes with stream machinery where `cout_my_class()` does not; comparisons, arithmetic, access, and assignment all carry strong conventions — honor them or invent a named function. |
| `C.168` | Adopt | Define overloaded operators in the namespace of their operands so ADL finds them and no divergent second meaning appears elsewhere; binary operators spanning two namespaces are best avoided entirely. Same principle as helpers living beside their class (C.5). |
| `C.170` | Adopt | Lambdas cannot be overloaded — two same-named variables are an error — so a callable needing overload-style dispatch is written as a generic (`auto`) lambda; the compiler polices this one. |
| `C.180` | Adapt | Unions save memory when several members are never live simultaneously — short-string optimizations are the classic. Locally a union is the last resort behind enum-tag structs and `std::variant`, justified by measured memory pressure per Concrete Types First. |
| `C.181` | Adopt | Avoid naked unions: without a tag tracking which member is live, reading the wrong member is undefined behavior printing plausible garbage — an invisible type error. Wrap the union with a discriminant or reach for `std::variant`. |
| `C.182` | Adopt | Implement tagged unions as tag-plus-anonymous-union pairs; the explicit destroy/placement-new choreography for non-trivial members is elaborate enough that `std::variant` exists to spare you writing it. |
| `C.183` | Adopt | Unions never serve type punning: reading a member other than the stored one is undefined behavior. Pun visibly through `reinterpret_cast` to `std::byte` (defined behavior) or `std::bit_cast` where available; "sometimes it works as expected" is not an argument. |

---

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
