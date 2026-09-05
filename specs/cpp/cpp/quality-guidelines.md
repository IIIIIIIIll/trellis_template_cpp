# Quality Guidelines

> Code quality standards for C++ code: naming conventions, header hygiene, ODR/ABI safety, and compile-time discipline.

---

## Overview

These rules are opinionated defaults whose sources are honestly mixed: functions and variables keep **std call-site rhythm** — `snake_case`, because every real-world C++ file interleaves project code with STL calls — while types and constants take **Google style** (`PascalCase`, `k` prefix), the vocabulary the standard library does not itself supply. The property that actually binds it together is **consistency beats taste**: one documented mix, applied without exception.

Baseline: C++14 (`std::make_unique`, generic lambdas, relaxed
`constexpr`). C++17 and C++20 additions appear as marked upgrades where
they change the recommendation — `std::string_view`, `std::optional`,
`if constexpr`, `[[nodiscard]]`, `std::span` — each with the C++14
spelling alongside, so a C++14 project can follow every rule as written.

---

## Naming Conventions

Default strength: hard.

Caught by: review — no automated detector.

| Element | Convention | Example |
|---------|------------|---------|
| **QUAL-1** Types, classes, structs, enums | `PascalCase` | `HttpRequestParser` |
| **QUAL-2** Concepts (C++20) / template parameters | `PascalCase`, single word or `T` | `Sinkable`, `T` |
| **QUAL-3** Free functions, member functions | `snake_case` | `parse_header` |
| **QUAL-4** Local variables, parameters | `snake_case` | `retry_count` |
| **QUAL-5** Member variables | `snake_case` + trailing `_` | `size_`, `buffer_` |
| **QUAL-6** Constants (namespace/class scope) | `k` prefix + `PascalCase` | `kMaxRetries` |
| **QUAL-7** Scoped enum values | `k` prefix + `PascalCase` | `Status::kOk` |
| **QUAL-8** Namespaces | short, lowercase | `net`, `http` |
| **QUAL-9** Macros (unavoidable ones) | `PROJECT_PREFIX_ALL_CAPS` | `MYLIB_ASSERT` |

**Why `snake_case` for functions**: the standard library itself uses it (`push_back`, `find_if`, `to_string`). PascalCase functions would produce a permanently mixed-style file every time an algorithm is called. Pick one rhythm and keep it; consistency beats taste in a language whose ecosystem you cannot rename.

**Why trailing `_` for members**: constructor initializer lists read unambiguously (`width_(width)`), and no shadowing warnings from `-Wshadow`.

**QUAL-10.** Do not use `m_` or plain names plus setter/getter gymnastics.

```cpp
// compiles; UB at runtime
// Wrong: four styles in ten lines
class PacketReader {
public:
    bool ReadNext();                    // camelCase method
private:
    uint8_t* buffer;                    // bare member name
    int m_len;                          // Hungarian-ish prefix
    static const int MAX_SIZE = 4096;   // macro-style constant
};

// Right
class PacketReader {
public:
    bool has_next() const;
    bool read_next();
private:
    uint8_t* buffer_;
    int len_;
    static constexpr int kMaxSize = 4096;
};
```

The `Right` class above also demonstrates the conventional member declaration order (`NL.16`): types, then constructors/assignment/destructor, then functions, then data — `public` before `protected` before `private`, never scattered access blocks. The formatter never reorders declarations, so member order stays a review convention rather than a formatting setting.

### Comment Discipline

**QUAL-11.** Comments that narrate what the code already says are rot-prone noise (`NL.1`): compilers never read them and they drift. State it in code or delete the comment.

**QUAL-12.** Comments earn their place by stating intent the code cannot express — why, constraints, expected behavior (`NL.2`). If a comment and its code disagree, treat both as wrong until reconciled.

**QUAL-13.** Keep comments crisp, grammatical, and professional: verbosity spreads understanding thin, SMS spelling ages badly (`NL.3`).

### House Style Beyond the Table

- **QUAL-14.** No Hungarian-style type warts (`NL.5`): names describe functionality, and overloading matches types automatically. Role prefixes stay legal (`size_`, `cnt_hits`) because they encode purpose, not type — exactly what the table above permits.
- **QUAL-15.** Name length proportional to scope (`NL.7`): short conventional names (`i`, `p`) locally, descriptive names for anything visible across functions; a cryptic one-letter global is always wrong.
- **QUAL-16.** One house style for our code, imported libraries keep theirs (`NL.8`) — the table above is that house style.
- **QUAL-17.** Reserved identifiers (`__`-prefixed or leading `_X`) stay banned along with everything else the standard reserves.
- **QUAL-18.** `ALL_CAPS` is reserved for macros (`NL.9`) so a shouting identifier always means text-substitution hazard; constants and scoped-enum values take `k` names per the table, never caps.
- Deviation from `NL.10`: upstream prefers `underscore_style` names across the board; we keep snake_case where the table says so (functions, variables — std call-site rhythm) and take PascalCase types and `k` constants from Google style — the mixed lineage named in the Overview, with the split documented here as the difference.
- **QUAL-19.** Reject easily misread names (`NL.19`) — `oO01lL`, near-twin pairs like `splunk`/`splonk`: screens differ and humans skim. A standing naming-review duty alongside the table.
- **QUAL-20.** One name per declaration (`NL.21`): `int a, b;` invites declarator-syntax confusion, and splitting costs nothing while reading better.
- **QUAL-21.** Write `f()`, not `f(void)` (`NL.25`): in C++ the empty parameter list already means no parameters, and the C-compat ceremony adds nothing.
- **QUAL-22.** West const (`const int x`, `const T&`) per conventional notation (`NL.26`): east const is logically defensible but unfamiliar to most readers; consistency wins and suffixed `const` is rejected in review.
- Interface files end `.h`, implementation files `.cpp` (`NL.27`); the exact letters matter less than uniformity — same disposition as `SF.1` under Header Hygiene below.

### Readable Literals

**QUAL-23.** Make literals readable (`NL.11`): digit separators (`299'792'458`) and typed suffixes (`"..."s`, `100ms`) where the type matters. Long bare digit runs are typo farms, and magic constants stay banned separately.

### Layout Is Delegated to clang-format

**QUAL-24.** Five Guidelines rules are layout-shaped, and hand-policing formatting wastes the exact attention reviews exist for. The committed `.clang-format` encodes each decision once:

- Indentation (`NL.4`): consistent indentation prevents real defects — the swallowed-control-statement bug — but the decision is mechanical.
- Whitespace restraint (`NL.15`): no `< map >`-style padding.
- Brace placement (`NL.17`): K&R-derived Stroustrup layout, encoded once by the formatter.
- Declarator layout (`NL.18`): C++ style, `T& name`, type-emphasized rather than expression-emphasized.
- Line packing (`NL.20`): two statements on one line hide defects from skimmers and diff readers alike; keeping them apart is the formatter's job.

Deviation from each of `NL.4`, `NL.15`, `NL.17`, `NL.18`, and `NL.20`: the intent is adopted and the mechanism delegated entirely to the committed clang-format configuration — deliberately not hand-policed.

Caught by: clang-format — the committed configuration is the single encoding of each layout decision.

---

## Static Analysis Curation

Default strength: default.

Caught by: review — no automated detector.

**QUAL-25.** clang-tidy earns its keep on changed sources only when curated — wholesale category dumps bury signal under hundreds of hits.

Worth enabling (low noise, high yield):

| Checks | Why |
|--------|-----|
| `bugprone-*` | Real defect patterns: use-after-move, dangling references, suspicious casts |
| `performance-*` | Unnecessary copies, pass-by-value misses, inefficient calls |
| `modernize-*` | Mechanical language hygiene (`use-override`, `use-nullptr`, `use-emplace`) |
| Selected `misc-*` (`misc-unused-*`) | Dead declarations and parameters |

**QUAL-26.** Individual `cppcoreguidelines-*` checks follow the same discipline — curated one by one, never enabled as a family.

Enable first — low noise, direct defect yield:

| Check | Guards against | Related rules |
|-------|----------------|---------------|
| `cppcoreguidelines-slicing` | Derived-to-base copies silently dropping the dynamic type | `C.67` |
| `cppcoreguidelines-init-variables` | Uninitialized locals | `ES.20` |
| `cppcoreguidelines-narrowing-conversions` | Lossy implicit conversions | `ES.46` |
| `cppcoreguidelines-pro-type-member-init` | Members left uninitialized | `C.48` |
| `cppcoreguidelines-special-member-functions` | Half-defined copy/move/destroy sets | `C.21` |
| `cppcoreguidelines-prefer-member-initializer` | Constructor-body assignments that belong in the init list | `C.49` |
| `cppcoreguidelines-pro-type-cstyle-cast` | C-style casts bypass every access check; named casts state intent | `ES.49` |

Slicing deserves the example: the compiler stays happy while behavior vanishes:

```cpp
// compiles; UB at runtime
// Wrong: HttpHandler sliced into Base on the way in; dispatch and fields gone.
void install(Base handler);
install(HttpHandler{});

// Right (C.67): borrow the object; storage decisions belong to the owner.
void install(const Base& handler);
```

Second wave — evaluate against your codebase before enabling:

| Check | Notes |
|-------|-------|
| `cppcoreguidelines-virtual-class-destructor` | Polymorphic bases need virtual destructors; noisy only where protected non-virtual destructors are deliberate |
| `cppcoreguidelines-no-malloc` | Flags `malloc`/`free`/`calloc`/`realloc`; aligns with the ownership ladder — drop the check if C interop dominates the tree |
| `cppcoreguidelines-pro-type-static-cast-downcast` | Unsound downcasts; the kind-tag dispatch under ODR and ABI Pitfalls below makes most of them unnecessary anyway |
| `cppcoreguidelines-avoid-non-const-global-variables` | Mutable globals are review bait; expect findings in legacy glue and fix or justify each one |
| `cppcoreguidelines-rvalue-reference-param-never-moved` | Sink parameters declared but never moved from; pairs with the pass-by rules in [Memory and Ownership](./memory-and-ownership.md) |

Skip with a written reason, not by omission:

| Check | Why skipped here |
|-------|------------------|
| `cppcoreguidelines-owning-memory` | Models `gsl::owner`; owning raw pointers are banned outright, so its findings duplicate review rules instead of adding yield |
| `cppcoreguidelines-avoid-magic-numbers` | High churn, low signal alongside normal review |

Leave off by default:

| Checks | Why off |
|--------|---------|
| `bugprone-easily-swappable-parameters` | Notoriously noisy; the parameter-role contract in [Functions and Interfaces](./functions-and-interfaces.md) fixes the design instead |
| `modernize-use-trailing-return-type` | Style churn; the local return-type convention already decides |
| `readability-identifier-naming` without a committed config | Churn generator unless the naming table ships beside the repo (see Naming Conventions above) |
| House-style families (`llvm-*`, `fuchsia-*`, ...) | Someone else's conventions; mechanical style belongs to clang-format |

**QUAL-27.** When a check lands in `.clang-tidy`, record it in the same change that adopts the corresponding rule; when a check is rejected, leave the reason here so the question is answered once.

---

## Header Hygiene

Default strength: hard.

Caught by: review — no automated detector.

### File Suffixes and Namespaces

**QUAL-28.** `.cpp` for code files, `.h` for interface files, everywhere unless an existing project convention wins (`SF.1`) — identical in substance to `NL.27` in the naming section; uniformity is the point, not the letters.

**QUAL-29.** Namespaces mirror logical structure (`SF.20`): components and layers, short and lowercase per the naming table — `net`, `http`.

### Include What You Use

**QUAL-30.** Every header must be **self-contained** (`SF.11`): it includes everything its own code names — include what you name (`SF.10`), never depending on what a transitively included header happens to drag in; deliberate aggregation headers remain acceptable.

```cpp
// compiles; UB at runtime
// Wrong: compiles today because <vector> happens to pull in <cstdint>
// widget.h
#include <vector>
class Widget {
    std::uint32_t id_;                  // uint32_t never included directly
};

// Right
#include <cstdint>
#include <vector>
class Widget {
    std::uint32_t id_;
};
```

Caught by: the compiler — building each `.cpp` with its own header first (QUAL-31) turns a missing include into a build error.

**QUAL-31.** Enforce mechanically (`SF.5`): make each header the *first* include of its own `.cpp`.

**QUAL-32.** Includes go first in both `.h` and `.cpp` (`SF.4`); upstream's include-after-code insulation trick protects exactly one level, which is why it is not adopted here.

Caught by: review — no automated detector.

### Include Spelling and Form

**QUAL-33.** Quoted includes for locally relative files, angle brackets for everything else (`SF.12`): quoting a search-path header risks a future sibling file silently shadowing the intended one.

**QUAL-34.** Spell header identifiers exactly as on disk (`SF.13`) — matching case, `/` separators, never backslashes — because the standard leaves lookup unspecified and platform-specific paths do not survive porting.

### Forward Declarations

**QUAL-35.** Forward-declare only what you can: parameters, references, pointers, and return-pointer types in declarations. Anything requiring size, members, or base classes needs the full type.

```cpp
// Right: incomplete types suffice for these declarations
class Engine;
class Widget {
    Widget(const Engine& engine);
    Engine* engine() const;
};

// Wrong: member by value and inheritance need the complete type
class Widget : public Engine { /*...*/ };   // compile-error: Engine is incomplete here — include, do not forward-declare
```

Caught by: the compiler — using an incomplete type where the complete type is required fails the build.

Rules of thumb:

- **QUAL-36.** Never forward-declare `std::` types — it is UB. Include `<string>` etc.

```cpp
// Wrong: forward-declaring anything in namespace std
namespace std { class string; }             // compiles; UB per [namespace.std]

// Right: include the real header
#include <string>
```

Caught by: review — no automated detector.

- **QUAL-37 (default).** Prefer including over forward-declaring for project headers unless compile-time pain is measured, not assumed.

- **QUAL-38.** One header declares one primary type; do not chain forward declarations to break artificial cycles that better layering would remove.

### Cycles Mean Layering Bugs

**QUAL-39.** Eliminate cyclic includes with better layering; do not paper over them with guards (`SF.9`) — the same stance as refusing forward-declaration chains to break artificial cycles that better layering would remove.

### Include Guards: `#pragma Once`

**QUAL-40.** Use `#pragma once`. It is non-standard but universally supported by GCC, Clang, and MSVC — decades of mainstream support. Classic guards are longer, invite copy-paste typos (`#endif // WRONG_NAME` fails silently), and collide when two directories contain identically named headers. Fall back to guards only if you must support exotic preprocessors.

```cpp
// Preferred
#pragma once

// Acceptable fallback, done correctly
#ifndef MYLIB_NET_WIDGET_H_
#define MYLIB_NET_WIDGET_H_
// ...
#endif  // MYLIB_NET_WIDGET_H_
```

Deviation from `SF.8`: the intent — every header included at most once per translation unit — is adopted wholesale, while the mechanism differs deliberately: `#pragma once` over classic guards, with fallback guards still carrying component-keyed names despite upstream's ISO-guard preference.

### What Belongs in a Header

**QUAL-41.** Headers carry declarations, templates, class definitions, and `inline`/`constexpr` definitions (`SF.2`) — never namespace-scope object definitions or non-inline function bodies, which duplicate per translation unit and die in linkage errors. Inline Variables below shows the sanctioned shape for header constants.

Caught by: the linker — non-inline bodies die in duplicate-symbol errors; per-TU object copies only surface under review or ODR-sensitive tools.

**QUAL-42.** Anything declared in multiple source files gets one home in a header (`SF.3`): hand-written `extern` declarations drift silently until the linker complains late.

### `using namespace`

**QUAL-43.** Deviation from `SF.6`: `using namespace` is tolerated sparingly inside `.cpp` files (a translation unit counts as local scope) and during transitions, but we stop short of blessing blanket `using namespace std;` — qualify when ambiguity threatens.

Caught by: review — no automated detector.

**QUAL-44.** Never in headers (`SF.7`): at global scope it hijacks every includer's name lookup and makes include order semantically load-bearing. The `std::literals` exception stands because user-defined-literal rules prevent collisions.

### Internal Linkage: Anonymous Namespaces

**QUAL-45.** File-local helpers in `.cpp` files go in an anonymous namespace (`SF.22`: all internal, non-exported entities live there — preferred over `static` for uniformity with type declarations, with exported entities staying outside).

**QUAL-46.** Anonymous namespaces in headers are forbidden (`SF.21`): every including translation unit gets its own private copies, silently duplicating code and data and tripping ODR-sensitive tools.

```cpp
// parser.cpp

// Right: helpers invisible outside this translation unit
namespace {
constexpr int kMaxDepth = 64;

bool is_delim(char c) noexcept { return c == ',' || c == ';'; }
}  // namespace

// compiles; UB at runtime
// Wrong (in a header): one copy per including TU
namespace {
int helper_count = 0;                   // N distinct variables after inclusion
}
```

---

## ODR and ABI Pitfalls

Default strength: hard.

Caught by: review — no automated detector.

### Namespace-Scope Constants in Headers

**QUAL-47.** A namespace-scope constant defined in a header must exist exactly once across all translation units. The C++14 spelling: declare it `extern` in the header (`extern const int kMaxConnections;`) and define it in exactly one `.cpp` — or hide it behind a function-local static accessor (`const std::array<Mode, 3>& modes()`) when a type or initializer makes the extern form clumsy. A plain non-`extern` `const` at namespace scope instead has internal linkage: legal, but each TU gets its own copy, and any address-taken use diverges or breaks. **C++17:** `inline constexpr` in the header — the one sanctioned object definition in a header (`SF.2` bans the rest).

```cpp
// C++17
// config.h — included everywhere

// Right: one object program-wide, safe to take addresses of
inline constexpr std::array<Mode, 3> kModes{Mode::kFast, Mode::kSafe, Mode::kRaw};
inline constexpr int kMaxConnections = 128;

// compiles; UB at runtime
// Wrong: per-TU copies, ODR traps when addresses are compared
static const int kMaxConnections = 128;
```

### Static Initialization Order Fiasco

**QUAL-48.** Initialization order of namespace-scope objects across translation units is unspecified. Any global whose constructor reads another global is reading garbage on some platforms. Use `constexpr` initialization where possible, otherwise function-local statics (thread-safe since C++11).

```cpp
// C++17
// compiles; UB at runtime
// Wrong: g_registry may initialize before g_logger exists
Registry g_registry(&g_logger);

// Right: initialized on first use, ordered within itself
Logger& logger() {
    static Logger instance;
    return instance;
}

Registry& registry() {
    static Registry instance(&logger());
    return instance;
}

// even better when expressible: compile-time init removes the question entirely
inline constexpr Config kDefaults{/* ... */};
```

**C++20:** mark such globals `constinit` to force compile-time initialization and turn order bugs into compile errors.

### PIMPL for Published Libraries

**QUAL-49.** Headers of libraries distributed as binaries must not expose private members: adding a member later changes `sizeof` and breaks ABI. Hide privates behind a pointer-to-implementation. Source-shipped internal code does not need this ceremony.

```cpp
// C++17
// parser.h — ABI-stable public header
#pragma once
#include <memory>

class Parser {
public:
    Parser();
    ~Parser();                                   // out-of-line: Impl must be complete here
    Parser(Parser&&) noexcept;
    Parser& operator=(Parser&&) noexcept;
    bool parse(std::string_view text);
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;                 // stable size: one pointer
};
```

The destructor and move operations are defined in the `.cpp`, where `Impl` is complete. Adding members to `Impl` stays ABI-compatible forever.

### No RTTI Assumptions in Cross-Module Headers

**QUAL-50.** `dynamic_cast` and `typeid` require identical RTTI representations on both sides of a module boundary. Independently built modules (different compiler versions or flags) cannot rely on them; use explicit interface virtuals, enum kind tags, or visitor patterns instead.

```cpp
// compiles; UB at runtime
// Wrong: works in unit tests, returns nullptr across mismatched modules
if (auto* http = dynamic_cast<const HttpEvent*>(&ev)) { /*...*/ }

// Right: dispatch through the interface contract
switch (ev.kind()) {
    case EventKind::kHttp: handle_http(static_cast<const HttpEvent&>(ev)); break;
    case EventKind::kTimer: handle_timer(static_cast<const TimerEvent&>(ev)); break;
}
```

The same caution applies to throwing custom exception types across module boundaries — see error-handling guidelines: exceptions stay inside one module world.

### Cross-Module Standard Library ABI

**QUAL-51.** The RTTI caution above has a quieter sibling: the standard library itself must be binary-compatible on both sides of a module boundary. On GCC/libstdc++, the dual ABI decides what `std::string` means — `_GLIBCXX_USE_CXX11_ABI` selects between the classic and `__cxx11` layouts, and modules built with different settings will not link, because the mangled names do not match. The full independent-binary caveat lives in [Error Handling](./error-handling.md); this is the same threat model arriving through the standard library instead of your own types. On MSVC the runtime flavor cannot be mixed either: `/MD` vs `/MT` and debug vs release CRT must agree across every module in the process — `_ITERATOR_DEBUG_LEVEL` is what turns a mismatch into a link error.

Caught by: the linker — unresolved `std::__cxx11::` symbols, `LNK2038`/`LNK4098` conflict errors; loud, but only at the final link of the combined binary.

**QUAL-52.** The review gate is earlier: ABI-relevant compiler flags and prebuilt dependencies (see Third-Party Dependencies below) are decided for the whole module graph, never per target.

Caught by: review — no automated detector.

---

## Third-Party Dependencies

Default strength: hard.

Caught by: review — no automated detector.

**QUAL-53.** The standard library is the default supplier (`SL.2`): it ships with the toolchain, is tested as a unit, and keeps every module on one ABI (see the pitfalls above).

**QUAL-54.** A third-party dependency is a permanent design decision — vet it before adopting on four axes (`SL.1`): maintenance activity, portability across the supported compilers, license compatibility, and supply-chain provenance.

Review gate: a dependency proposal states what it beats in the standard library and its answers on the four axes; adopting without that note is rejected in review.

**QUAL-55.** Adopted components are used within their contracts (`SL.4`): no relying on growth schedules, SSO capacities, or other implementation details.

**QUAL-56.** Nothing user-defined enters namespace `std` (`SL.3`) — the sanctioned escapes are the few specializations the standard itself blesses; the ODR rules above explain why this one is absolute: a stray addition to `std` poisons every translation unit that includes you, and no tool tells you where.

---

## Enumerations

Default strength: default.

Caught by: review — no automated detector.

**QUAL-57 (hard).** Scoped `enum class` everywhere (`Enum.3`): plain enums convert to `int` too readily, and unrelated enumerations collide on shared enumerator names.

```cpp
// compiles; UB at runtime
// Wrong: implicit conversion to int, shouting names, collision-prone
enum Color { RED, GREEN };
int x = RED;

// Right: scoped, quiet names, no implicit conversion
enum class Color { kRed, kGreen };
Color c = Color::kRed;
// int x = Color::kRed;   // rejected: no implicit conversion to int
```

Enumerators take constant naming — `k` prefix, `PascalCase` — never `ALL_CAPS`, which stays reserved for macros (`Enum.5`; see the scoped-enum row in the naming table).

**QUAL-58 (default).** Define the operations enumeration users need (`Enum.4`) — a wrapping `operator++` for iteration-like sets, for instance. The required `static_cast` round-trip is accepted idiom, while expressions repeatedly casting back into the enum signal a missing operation.

**QUAL-59 (hard).** Unnamed enumerations are unrelated integer constants in costume: declare each value as `constexpr` instead (`Enum.6`), which also gives it the right individual type — the constexpr-discipline section below applied.

**QUAL-60 (default).** Leave the underlying type at its default unless necessary (`Enum.7`); specifying it is required for forward-declarable enums and fixed bit width — precisely the ABI-sensitive-header situations flagged under ODR and ABI above.

**QUAL-61 (default).** Give enumerators explicit values only when meaning demands it (`Enum.8`): conventional numbering such as months starting at 1, or bit-flag sets. Duplicate values are typos, and hand-written consecutive values are noise.

**QUAL-62 (hard).** Enumerators whose integer values cross a module or storage boundary (published headers, serialized or logged forms) pin explicit values and grow only by appending. Inserting an enumerator mid-set silently renumbers the tail, and a stale module still dispatching on the old integers reads the wrong kind; no tool flags this, so it is a standing review gate on kind-tag enum changes.

Cross-module kind tags (see the RTTI caution above) follow exactly this shape: scoped enum, `k`-named enumerators.

---

## Compile-Time Discipline: `constexpr` and Friends

Default strength: default.

Caught by: review — no automated detector.

**QUAL-63.** Use compile-time evaluation **where it is free**: pure computations, lookup tables, literal formatting, trait-like dispatch.

**QUAL-64.** Do not obfuscate straightforward runtime logic as template metaprogramming without a measured benefit; unreadable zero-cost is usually negative-cost once maintenance is priced in.

```cpp
// C++17
// Good: free win — table computed at build time, zero startup cost
constexpr std::array<uint8_t, 256> kReverseBits = [] {
    std::array<uint8_t, 256> t{};
    for (int i = 0; i < 256; ++i) {
        uint8_t r = 0;
        for (int b = 0; b < 8; ++b) {
            r |= ((i >> b) & 1) << (7 - b);
        }
        t[i] = r;
    }
    return t;
}();

// Good: if constexpr (C++17; C++14: tag dispatch) replaces SFINAE towers with readable branches
template <typename T>
auto serialize(const T& value) {
    if constexpr (std::is_integral_v<T>) {
        return write_int(value);
    } else {
        return write_blob(to_bytes(value));
    }
}

// Bad: metaprogramming where a loop is clearer
template <int N> struct Fact { static const int value = N * Fact<N - 1>::value; };
```

Guidance:

- Mark functions/constructors `constexpr` when the body is naturally constant-evaluable; do not contort logic to earn the keyword.
- **C++17:** `constexpr` lambdas — prefer them over hand-unrolled tables.
- **C++20:** adopt on upgrade — `consteval` for must-be-compile-time functions, `constinit` for guaranteed-initialized globals, `consteval`-checked formatting.

---

## Quality Check

Before merging, confirm:

- [ ] Names match the table: `PascalCase` types, `snake_case` functions, trailing `_` members, `k`-prefixed constants and scoped-enum values
- [ ] Every header compiles standalone (first include in its own `.cpp`)
- [ ] No reliance on transitive includes; no forward-declared `std::` types
- [ ] `#pragma once` present; anonymous namespaces appear only in `.cpp` files
- [ ] Namespace-scope header constants exist once program-wide (`extern` + one definition, or `inline constexpr` on C++17+)
- [ ] No cross-TU global-constructor dependencies; accessor functions instead
- [ ] Binary-published library headers use PIMPL with out-of-line destructor/moves
- [ ] No `dynamic_cast`/`typeid` in cross-module headers
- [ ] `constexpr` used only where it clarifies or measurably helps
- [ ] Scoped `enum class` with `k`-prefixed enumerators; unnamed enums standing in for constants are gone
- [ ] Headers define no namespace-scope objects or non-inline functions; `using namespace` never appears in headers
- [ ] Comments state intent rather than narration; layout decisions live in .clang-format, not in review

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
