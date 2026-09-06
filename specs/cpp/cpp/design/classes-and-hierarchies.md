---
description: Class design and inheritance: invariants, composition versus virtual dispatch
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Classes and Hierarchies

> Type design for C++: concrete types by default, special-member discipline (Rule of Zero, Rule of Five), polymorphic-base obligations, and hierarchies that are earned rather than assumed.

---

## Overview

Most defects in type design come from two opposite failures: writing special members the compiler already generates correctly, and reaching for inheritance where a struct plus free functions would do. This document fixes the ladder — concrete value types first, five-member types only for manual resources, hierarchies only for open variation — plus the obligations a virtual base can never skip.

Parameter conventions live in [Functions and Interfaces](./functions-and-interfaces.md); ownership of what members hold lives in [Ownership Design](./ownership-design.md).

Baseline: C++14 (`std::make_unique`, generic lambdas, relaxed
`constexpr`). C++17 and C++20 additions appear as marked upgrades where
they change the recommendation — `std::string_view`, `std::optional`,
`if constexpr`, `[[nodiscard]]`, `std::span` — each with the C++14
spelling alongside, so a C++14 project can follow every rule as written.

---

## Concrete Types First

Default strength: default.

Caught by: review; over-design surfaces later as maintenance drag, not as warnings.

**CLS-1.** Start as a concrete type: copyable, assignable, equality-comparable, no virtuals (`C.10`). Regular types behave like `int` — independent copies, replace-on-assign — and that predictability beats speculative extensibility (`C.11`).

**CLS-2.** Related data travels as one type rather than parallel loose parameters — `draw(x, y, x2, y2)` becomes two `Point`s — and a simple class without virtuals adds no space or time overhead over the loose version (`C.1`).

**CLS-3.** Whatever carries the operations — a class, a namespace of free functions, an abstract base, a concept-constrained template — the requirement is an explicit, stable seam between public interface and private representation, so the representation can change without touching users (`C.3`).

| Situation | Shape |
|-----------|-------|
| **CLS-4** Related data, no invariant | `struct`, public members, in-class initializers (`C.2`) |
| **CLS-5 (hard)** Data plus invariant | `class`; constructor establishes the invariant |
| Manual resource inside | Rule of Five (below) |
| Behavior varies over an *open* implementation set | Abstract interface + hierarchy (below) |
| **CLS-6** Trivial getters/setters around a bare field | Drop the facade — plain `struct` with public data (`C.131`) |

```cpp
// C++17
// CLS-7: closed variation uses a tag, not a hierarchy
// compiles; UB at runtime
// Wrong: a hierarchy for a closed set of two — vtables, heap copies, clone plumbing.
class Shape { public: virtual ~Shape() = default; virtual double area() const = 0; };

// Right: closed variation is a tag; dispatch is a branch, not a virtual call.
struct Shape {
    enum class Kind { Square, Circle } kind;
    double side_or_radius;
    [[nodiscard]] double area() const;
};
```

**CLS-7 (hard).** Reach for a hierarchy only when implementations are added by code you never see, across module boundaries you do not compile together. Closed variation inside one module is one `std::variant` away from being simpler.

Mechanical rules keep the concrete type honest:

- **CLS-8 (hard).** Never define a class or enum and declare a variable of it in the same statement — `struct Data { /*...*/ } data{/*...*/};` is how the missing semicolon after the closing brace happens. Split them (`C.7`).
- **CLS-9.** Any non-public member makes the spelling `class`, so the keyword itself announces that something is hidden, and the public interface comes first inside the body (`C.8`).
- **CLS-10 (hard).** Minimize member exposure: data participating in an invariant is private, reachable only through checked operations; the checked-public / unchecked-protected hook pattern is acceptable.
- **CLS-11.** Order members public before protected before private (`C.9`), and keep all non-`const` data members at one access level — invariant-free members go public (the type is really a `struct`), invariant-bearing members go private or `const`; debug instrumentation is the acknowledged mixed case (`C.134`).
- **CLS-12.** Accessors earn membership by maintaining invariants or converting representations, never as syntax-only field wrappers.

---

## Constructors Deliver Finished Objects

Default strength: hard.

Caught by: review — no automated detector.

**CLS-13.** A class with an invariant gets a constructor whose job is establishing it — `Ensures()` states the invariant cleanly.

**CLS-14 (default).** Convenience constructors on invariant-free types remain fine, and brace-init lists retire many redundant ones (`C.40`).

**CLS-15.** Every constructor delivers a fully initialized, usable object: no `init()`-before-use protocol, because compilers do not read comments.

**CLS-16.** Each member reaches initialized state explicitly, through delegation, or through a default member initializer — constructor-acquires/destructor-releases is RAII itself (`C.41`).

**CLS-17.** A constructor that cannot build a valid object throws; there is no half-built object waiting behind an `is_valid()` flag users will forget (`C.42`).

**CLS-18 (default).** Deviation from `C.43`: copyable types complete the semiregular set with a default constructor — `vector<Date>(1000)` needs one — but only where a meaningful empty state exists. Upstream argues against fake defaults such as `{0, 0, 0}` dates and exempts bases and caller-provided-resource types like `lock_guard`; this guide applies the same bar instead of demanding defaults everywhere. Built-in members stay uninitialized unless given `{}` initializers.

**CLS-19 (default).** Prefer default constructors that neither throw nor allocate (`C.44`): an empty `{nullptr, nullptr, nullptr}` state is cheap to establish, trivial to restore after errors, and keeps arrays of the type inexpensive.

**CLS-20 (default).** Do not write a default constructor that only assigns constants to members — put the constants in default member initializers and let the compiler generate the function (`C.45`).

**CLS-21 (default).** Common constructor actions — validation especially — live once in the most complete constructor, and the others delegate rather than retype it and drift (`C.51`).

**CLS-22.** `using Rec::Rec;` imports constructors into a derived class adding no data of its own, instead of reimplementing tricky ones — but every derived member still needs an initializer, or the inherited constructor silently leaves it unconstructed (`C.52`).

```cpp
// CLS-15: constructor delivers a fully initialized object
// compiles; UB at runtime
// Wrong: two-stage construction; users forget initialize(), and the object
// spends its life half-built.
Session s;
s.initialize(config);

// Right: either the constructor succeeds or there is no object.
Session s(config);
```

**CLS-23 (default).** Virtual behavior during construction moves behind a factory: a protected-token constructor keeps imperfectly built objects from escaping while a static `create()` runs `post_initialize()`, where virtual dispatch is safe. Return `unique_ptr` by default; `shared_ptr` only when sharing is certain (`C.50`).

**CLS-24.** The same lifecycle logic bans virtual calls inside constructors and destructors: dispatch follows the type constructed so far, so the derived override never fires, and calling a pure virtual there is undefined behavior. Qualified names (`Derived::g()`) honestly call the visible version; factories deliver post-construction virtual effects safely (`C.82`).

---

## The Rule of Zero Is the Default

Default strength: hard.

Caught by: clang-tidy `cppcoreguidelines-special-member-functions`; review for hand-written member-wise copies.

**CLS-25.** A type managing no resources by hand declares **none** of the five special members (`C.21` — the stance its rationale calls the Rule of Zero). RAII members and in-class initializers supply correct copy, move, and destruction semantics for free.

```cpp
// CLS-25: Rule of Zero declares no special members
// compiles; UB at runtime
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

**CLS-26.** If you can avoid defining the default operations, avoid them (`C.20`) — the analyzer-detectable smell is a hand-written `(pointer, size)` pair plus a deleting destructor begging to become a container.

**CLS-27.** When a special member must be written, remember they are a matched set: copy construction that deep-copies while assignment shallow-copies surprises every user (`C.22`). Upstream's heuristics are worth internalizing — copy/move pairs write the same members at the same dereference level, and members touched by the destructor appear in every copy/move path.

**CLS-28.** Two innocent-looking member declarations quietly break the generated set. A `const`, `&`, or `&&` data member leaves the type copy-constructible but silently non-assignable — store a pointer instead (raw or smart, `gsl::not_null` where null is excluded) (`C.12`).

**CLS-29.** A member that uses another member is declared after it: initialization follows declaration order and destruction reverses it, so users would touch the dependency outside its lifetime; the same discipline joins asynchronous work before the data it accesses dies (`C.13`).

---

## Rule of Five When Resources Are Manual

Default strength: hard.

Caught by: ASan/LSan expose missing destructors and double closes; clang-tidy special-member checks flag partial fives.

**CLS-30.** Managing a raw resource directly — descriptor, handle, heap block outside a smart pointer — means defining **all five** or deleting them explicitly (`C.21`). Defining one while defaulting another is how double-frees happen.

```cpp
class FileDesc {
public:
    explicit FileDesc(int fd) : fd_(fd) {}
    ~FileDesc() { if (fd_ >= 0) ::close(fd_); }

    FileDesc(const FileDesc& o) : fd_(::dup(o.fd_)) {       // deep copy; failure throws (C.42)
        if (fd_ < 0) throw std::system_error(errno, std::generic_category(), "dup");
    }
    FileDesc& operator=(const FileDesc& o) {              // deep, self-safe; dup before close
        if (this != &o) {
            int next = ::dup(o.fd_);
            if (next < 0) throw std::system_error(errno, std::generic_category(), "dup");
            if (fd_ >= 0) ::close(fd_);
            fd_ = next;
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

`::dup` failing returns -1, and a copy operation that swallows it silently fabricates an empty object — the half-built state `C.42` bans — so a failed `dup` throws `std::system_error`; assignment dups before closing so a failure leaves the target untouched.

First re-check [Memory Discipline](../implement/memory-discipline.md): a `unique_ptr<T, Deleter>` deletes this entire class. Rule of Five is the fallback for resources standard wrappers cannot express, not the default.

**CLS-31.** Once resources arrive, the destructor releases everything acquired, error paths included (`C.31`). Non-owned pointers and references are exempt from deletion; failures from close/release paths are design errors to terminate on, since release operations rarely retry.

**CLS-32.** A member owning through a raw pointer forces that destructor — and defining one obligates deciding all five operations, or the generated copy double-deletes (`C.33`). The simplest cure is replacing the raw owner with a smart pointer; ABI friction is why legacy code keeps raw owners, not an endorsement.

**CLS-33 (default).** Destructors are implicitly `noexcept` only when every member's destructor is, so one throwing member poisons the whole chain — declare `noexcept` explicitly to freeze the contract against future members. Blanket decoration is clutter even upstream declines to mandate (`C.37`).

Ownership questions route elsewhere by design: whether a raw member pointer or reference owns (`C.32`), handing `new` results straight to an owner (`C.149`), and constructing through `make_unique` (`C.150`) or `make_shared` (`C.151`) are decided outright by [Memory Discipline](../implement/memory-discipline.md), which bans owning raw pointers entirely — stricter than upstream's "consider whether it might own".

---

## `=default` and `=delete` Say What You Mean

Default strength: default.

Caught by: clang-tidy `cppcoreguidelines-special-member-functions`; `-Wdeprecated-copy` for half-defined cases.

**CLS-34.** Want generated behavior but must state it (out-of-line destructor, restored moves)? `=default` (`C.80`).

**CLS-35.** Want behavior not to exist? `=delete` — on any function, not just special members (`C.81`).

```cpp
// CLS-36: decide all five special members together
// compiles; UB at runtime
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

**CLS-36 (hard).** The rule is symmetric (`C.21`): touching any special member means deciding all five.

---

## Copies Compare Equal, Moves Stay Valid, Swap Never Fails

Default strength: hard.

Caught by: review — no automated detector.

**CLS-37 (default).** Copy assignment is non-virtual, takes `const&`, returns `T&` for chaining; the copy-and-swap shape provides the strong guarantee and ignores self-assignment for free.

**CLS-38.** If hierarchy assignment truly beckons, name it `assign()` — a virtual `operator=` is dragons (`C.60`).

**CLS-39.** A copy operation should copy: after `x = y`, `x == y`. Value semantics is the default posture; deliberate shallow "pointer semantics" is legal but must be coherent end to end, equality included (`C.61`).

**CLS-40.** Self-assignment must not change the value — member-wise assignment of well-behaved members makes the `this == &a` guard unnecessary, and the branch-predictor economics favor handling the million-to-one case correctly by construction (`C.62`).

**CLS-41 (default).** Move assignment mirrors copy assignment: non-virtual, parameter by `&&`, return `T&`; base and member move assignments run implicitly or explicitly (`C.63`).

**CLS-42.** Self-move is rare but reachable (`std::swap(a, a)`), so move assignment must leave the object valid; guaranteeing the value is literally unchanged takes the guard test, while null-out-then-delete-then-restore achieves safety without one. Upstream insists on more safety than the standard's valid-but-unspecified container promise (`C.65`).

**CLS-43.** Initialization and copying happen through constructors and assignment operators, never `memset` or `memcpy`: both overwrite vtables, and `memcpy` of a non-trivially-copyable type is undefined behavior (`C.90`).

**CLS-44 (default).** Value-like types provide a member `noexcept` swap plus a free two-argument overload in the same namespace — the machinery behind copy-assign-via-swap and guaranteed commit points (`C.83`).

**CLS-45.** Swap must not fail: element-copying implementations both crawl and break standard-library algorithms that assume element swap succeeds (`C.84`), so swap is declared `noexcept` — unwinding out of a swap is a design error the program should not survive quietly (`C.85`).

**CLS-46 (default).** Comparisons behave like built-ins. `==` treats operands symmetrically — a free function with matching parameter types, `noexcept`; a member `operator==` accepts conversions for its right operand only. The same holds across the comparison operators, and failure states prefer comparing equal to themselves and false against valid values over throwing (`C.86`).

**CLS-47.** Beware `==` on base classes: a virtual `operator==` sees derived state or not depending on the static operand type, and naive fixes do not scale — flag virtual comparison operators on sight (`C.87`).

**CLS-48 (default).** Hash specializations are `noexcept`, because hashed-container users never expect access to throw; xor-combining standard-library hashes beats cleverness for non-specialists (`C.89`).

**CLS-49 (default).** Ordering: a regular value type writes `operator<` memberwise — `std::tie(x_, y_) < std::tie(o.x_, o.y_)` giving lexicographic order — and derives `>`, `<=`, `>=` from `==` and `<`, ideally once in a CRTP ordering base. **C++20:** defaulted comparisons arrive (`operator<=>`) and will replace this spelling.

---

## Containers and Handles Follow the Standard Library

Default strength: default.

Caught by: review — no automated detector.

**CLS-50.** Deviation from `C.100`: custom containers follow STL conventions — conventional constructors, assignments, iterators, semantics — though partial conformance is respectable. Locally, containers are normally bought, not written; authoring one carries the justification burden the ownership ladder places on bypassing the standard library.

When one is justified, it owes the standard vocabulary:

- **CLS-51.** Value semantics — Regular in the concept sense, a copy comparing equal to its original — so containers reason like `int` (`C.101`).
- **CLS-52.** Move operations, because large immovable types tempt pointer-passing and its resource bugs, and callers reasonably assume returning a container by value is cheap (`C.102`).
- **CLS-53.** An initializer-list constructor, so `{1, 3, -1, 7}` builds element sets as expected (`C.103`).
- **CLS-54.** A default constructor yielding empty, completing Regularity — `vector<Sorted_seq<string>> vs(100)` produces a hundred usable elements (`C.104`).

**CLS-55.** A resource handle with pointer semantics provides `*` and `->`; familiarity is the entire argument (`C.109`).

---

## Polymorphic Bases Carry Obligations

Default strength: hard.

Caught by: clang-tidy `cppcoreguidelines-virtual-class-destructor`; ASan reports leaked derived subobjects.

**CLS-56.** Deleting a derived object through a base pointer whose destructor is non-virtual is undefined behavior — the derived destructor never runs (`C.35`, `C.127`). Every polymorphic base therefore picks exactly one legal shape:

| Base role | Destructor | Copies |
|-----------|------------|--------|
| **CLS-57** Interface, deleted polymorphically | `public virtual` | `=delete` (`C.67`); protected defaulted when serving a `clone()` hierarchy |
| **CLS-58** Mixin, never deleted through base pointer | `protected`, non-virtual | `=delete` |

```cpp
// CLS-57: interface base deletes copies, public virtual destructor
// compiles; UB at runtime
struct Base {
    ~Base();                          // Wrong: public, non-virtual
    virtual void run();
};
struct Impl : Base { };               // derived with state
Base* b = new Impl;
delete b;                             // UB: ~Impl never runs; derived state leaks

struct GoodBase {
    virtual ~GoodBase() = default;    // Right: public virtual, safe polymorphic delete
    GoodBase(const GoodBase&) = delete;
    GoodBase& operator=(const GoodBase&) = delete;
    virtual void run() = 0;
};
```

**CLS-59 (default).** Spelling: overrides say `override`; leaves sealing the hierarchy say `final`; a declaration carries exactly one of `virtual`/`override`/`final`, never two (`C.128`).

**CLS-60.** Virtual functions never declare default arguments — defaults bind statically while dispatch is dynamic, so callers disagree depending on static type (`C.140`).

**CLS-61.** Name lookup hides too: a derived member hides its bases' entire same-named overload sets — `d.f(2.3)` quietly calls `f(int)` — so `using B::f;` restores them, for virtual and non-virtual alike; the overloader idiom writes one explicit `using Base::operator();` per base — or forwards through a small call set — to unhide each `operator()` at C++14. **C++17:** a variadic `using Ts::operator()...` does it in one line (`C.138`).

---

## Composition Before Inheritance

Default strength: default.

Caught by: review — no automated detector.

**CLS-62 (hard).** Inheritance models **is-a** over an open set (`C.120`).

**CLS-63.** Implementation reuse is composition's job: a member function earns membership only through direct access to the representation (`C.4`), and helpers live beside the type in its namespace (`C.5`).

| Smell | Verdict |
|-------|---------|
| **CLS-64** Base exists mainly to share protected helpers | Flatten into free functions |
| **CLS-65** Convenience base with no polymorphic use sites | Delete it |
| **CLS-66** Virtual nobody overrides past the leaf | De-virtualize (`C.132`) |
| **CLS-67** Callers hold base pointers they cannot spell | Genuine interface — keep |

```cpp
// C++17
// CLS-64: flatten helper-only base into free functions
// compiles; UB at runtime
// Wrong: three layers whose only job is sharing format_timestamp().
class Logger {
protected:
    std::string format_timestamp() const;
};

namespace logfmt {                    // Right: reusable without any inheritance — or a genuine
                                      // interface when callers hold base pointers
    [[nodiscard]] std::string format_timestamp(std::chrono::system_clock::time_point tp);
}
class LogSink {                       // genuine interface, composition point
public:
    virtual ~LogSink() = default;
    virtual void write(std::string_view line) = 0;
};
class FileSink final : public LogSink { /* uses logfmt:: helpers */ };
```

**CLS-68.** Chains beyond roughly three levels without interface users at the top are refactoring backlog, not architecture.

**CLS-69 (hard).** Multiple inheritance enters only as multiple distinct interfaces — breaking a monolithic API into aspects, the way `iostream` unions `istream` and `ostream` — typically with abstract bases (`C.135`).

**CLS-70 (default).** Deviation from `C.136`: state-carrying implementation mixins (`enable_shared_from_this`, intrusive hooks) pass review only where the mixin injects customization points or erases forwarding boilerplate; otherwise Composition Before Inheritance governs.

**CLS-71 (default).** Deviation from `C.137`: a virtual base separating shared implementation data (`virtual protected Utility`) from an interface root does keep shared state out of an overly general god-base — but upstream concedes hierarchy linearization is often better, and locally, reaching for a virtual base at all starts the flattening conversation.

---

## Abstract Interfaces Have No State

Default strength: hard.

Caught by: review — no automated detector.

**CLS-72.** An interface is pure protocol: no data members, no constructor logic, virtual destructor, deleted copies (`C.122`). A base used as an interface is therefore a pure abstract class — public pure virtual functions plus a virtual destructor, zero data — because data-free interfaces stay stable; upstream's founding example (a missing virtual destructor dropping the derived `string`) is this section's motivation (`C.121`). Data inside an abstract type forces every implementation into one layout — a base class wearing an interface's name.

```cpp
// C++17
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

**CLS-73 (default).** Abstract classes typically skip user-written constructors — no data exists to initialize. Exceptions exist: base constructors doing registration work, and the rare shared-statistics data that tends to drag the hierarchy toward virtual inheritance (`C.126`).

Edge rules:

- **CLS-74.** Hold and pass polymorphic objects by pointer or reference — by value slices (`C.145`; enforced by the signature tables in [Functions and Interfaces](./functions-and-interfaces.md)).

  Caught by: clang-tidy `cppcoreguidelines-slicing`.
- **CLS-75.** Never point a base pointer into an array of derived objects; element stride differs (`C.152`).

  Caught by: review — no automated detector.
- **CLS-76.** Prefer virtual dispatch; `dynamic_cast` only where navigation between siblings is genuinely unavoidable (`C.146`). Use `dynamic_cast<T&>` when absence of `T` is an error — a reference cast throws on failure, declaring the intent to end up with a valid object (`C.147`); use `dynamic_cast<T*>` when absence is a valid alternative — null enables branching, and the result is always tested before dereference. Across module boundaries, Headers and Dependencies replaces RTTI with kind tags outright (`C.148`).
- **CLS-77.** Copying goes through a virtual `clone()` returning `std::unique_ptr<Codec>`, never through base-reference copy construction (`C.130`): covariant smart pointers are impossible, so return `unique_ptr<Base>` uniformly; copy/move demote to protected defaulted helpers serving clone implementations, while public copy construction and assignment stay suppressed.
- **CLS-78 (default).** Deviation from `C.153`: prefer the virtual call, which lands on the most-derived override where a cast may stop at an intermediate class and rot as the hierarchy evolves. Closed variation replaces both sides with kind-tag dispatch (Concrete Types First), reserving `dynamic_cast` for genuinely open navigation per rule 3.

---

## Protected Data Is a Liability

Default strength: hard.

Caught by: review — no automated detector.

**CLS-79.** Protected data members give every subclass — present and future — a vote on the base invariant (`C.133`). Protected **hook functions** upholding invariants are fine; protected **fields** are not.

```cpp
// C++17
// CLS-79: guard invariants behind methods, never protected fields
// compiles; UB at runtime
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

Default strength: default.

Caught by: review — no automated detector.

**CLS-80.** Seal classes whose hierarchy is deliberately closed (`C.128`): reviewers get warned before extending what was designed shut, and the compiler may de-virtualize hot calls.

```cpp
// CLS-80: seal deliberately closed hierarchies with final
// compiles; UB at runtime
class HttpTransport : public Transport {};   // Wrong: open by omission — subclasses can
                                             // later bypass the timeout invariants
class HttpTransport final : public Transport {};   // Right: sealed leaf
```

**CLS-81.** Do not sprinkle `final` on documented extension points — seal what would break invariants, leave open contracts open (`C.139`). Sealing is a decision about extension; performance claims require substantiation, and misuses historically outnumber wins.

---

## Operators Mimic Conventional Usage

Default strength: default.

Caught by: review — no automated detector.

**CLS-82.** Define operators primarily to mimic conventional usage — `+` adds, copies compare equal — because invented semantics tax every reader; non-member operators are friends or live with their operands (`C.160`).

**CLS-83.** Use an operator only for its conventional meaning: `operator<<` composes with stream machinery where `cout_my_class()` does not, and comparisons, arithmetic, access, and assignment all carry strong conventions — honor them or invent a named function (`C.167`).

```cpp
// C++17
// CLS-84: symmetric operators are non-members found by ADL
// compiles; UB at runtime
// Wrong: member == converts the right side only — p == "p" compiles,
// "p" == p does not; symmetry silently depends on operand order.
struct Point {
    int x, y;
    bool operator==(const Point& other) const;   // member spelling
};

// Right: free function, matching parameter types, found by ADL beside the type.
[[nodiscard]] bool operator==(const Point& a, const Point& b) noexcept;
```

**CLS-84 (hard).** Symmetric operators are therefore non-members: a member `operator==` converts arguments on one side only, making `a == b` and `b == a` subtly differ (`C.161`) — the same symmetry and `noexcept` requirements as C.86 above.

**CLS-85.** Overload for roughly equivalent operations — one `print` name across argument types instead of `print_int`/`print_string`, since encoded type names add verbosity and inhibit generic code (`C.162`).

**CLS-86.** Overload *only* for roughly equivalent operations: `open(Gate&)` and `open(const char*, const char*)` collide confusingly despite the type system's partial rescue; watch popular names such as `open`, `move`, `+`, `==` (`C.163`).

**CLS-87 (hard).** Avoid implicit conversion operators: surprises range from unintended calls to dangling pointers into destroyed temporaries. Conversions stay explicit until a fundamental, frequently needed case is demonstrated (`C.164`).

**CLS-88.** Find customization points through `using`: `using std::swap;` before an unqualified call picks up `N::swap` when present and falls back to `std::swap` — precisely how generic code discovers the free swap overloads above (`C.165`).

**CLS-89.** Define overloaded operators in the namespace of their operands so ADL finds them and no divergent second meaning appears elsewhere; binary operators spanning two namespaces are best avoided entirely — the same principle as helpers living beside their class (`C.168`).

**CLS-90 (hard).** Overload unary `&` only inside a coherent smart-pointer/reference system whose `->`, `*`, and `[]` agree — `.` cannot be overloaded, so perfection is impossible, and `std::addressof` always recovers the built-in pointer (`C.166`).

**CLS-91.** Lambdas cannot be overloaded — two same-named variables are an error — so a callable needing overload-style dispatch is written as a generic (`auto`) lambda; the compiler polices this one (`C.170`).

---

## Unions Are a Last Resort

Default strength: default.

Caught by: review — no automated detector.

**CLS-92.** Deviation from `C.180`: unions save memory when several members are never live simultaneously — short-string optimizations are the classic use. Locally a union is the last resort behind enum-tag structs and `std::variant`, justified by measured memory pressure per Concrete Types First.

**CLS-93 (hard).** Avoid naked unions: without a tag tracking which member is live, reading the wrong member is undefined behavior printing plausible garbage — an invisible type error. Wrap the union with a discriminant or reach for `std::variant` (`C.181`).

**CLS-94.** Implement tagged unions as tag-plus-anonymous-union pairs; the explicit destroy/placement-new choreography for non-trivial members is elaborate enough that `std::variant` exists to spare you writing it (`C.182`).

```cpp
// C++17
// Last resort: measured pressure proves std::variant too fat.
struct Packed {
    enum class Kind : uint8_t { Empty, Num } kind = Kind::Empty;
    union { double num; };            // trivial members only
};
// Anything non-trivial belongs in a variant, which owns the choreography.
using CellValue = std::variant<std::monostate, double, std::string>;
```

**CLS-95 (hard).** Unions never serve type punning: reading a member other than the stored one is undefined behavior. Pun visibly through `reinterpret_cast` to `std::byte` (defined behavior) or `std::bit_cast` where available; "sometimes it works as expected" is not an argument (`C.183`).

---

## Quality Check

Gates before merging hierarchy work: format-clean (`clang-format --dry-run`) and tidy-clean on changed sources, the unit suite green, and — because hierarchies touch lifetime edges — the suite repeated under an ASan+UBSan build.

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

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
