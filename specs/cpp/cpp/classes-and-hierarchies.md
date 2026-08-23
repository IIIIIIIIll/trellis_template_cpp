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

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
