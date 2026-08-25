# Quality Guidelines

> Code quality standards for C++ code: naming conventions, header hygiene, ODR/ABI safety, and compile-time discipline.

---

## Overview

These rules are opinionated defaults chosen for one property above all: **uniformity with the standard library**, since every real-world C++ file interleaves project code with STL calls. The baseline is **C++17**; C++20/23 refinements are noted inline where they change the guidance.

---

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Types, classes, structs, enums | `PascalCase` | `HttpRequestParser` |
| Concepts (C++20) / template parameters | `PascalCase`, single word or `T` | `Sinkable`, `T` |
| Free functions, member functions | `snake_case` | `parse_header` |
| Local variables, parameters | `snake_case` | `retry_count` |
| Member variables | `snake_case` + trailing `_` | `size_`, `buffer_` |
| Constants (namespace/class scope) | `k` prefix + `PascalCase` | `kMaxRetries` |
| Scoped enum values | `k` prefix + `PascalCase` | `Status::kOk` |
| Namespaces | short, lowercase | `net`, `http` |
| Macros (unavoidable ones) | `PROJECT_PREFIX_ALL_CAPS` | `MYLIB_ASSERT` |

**Why `snake_case` for functions**: the standard library itself uses it (`push_back`, `find_if`, `to_string`). PascalCase functions would produce a permanently mixed-style file every time an algorithm is called. Pick one rhythm and keep it; consistency beats taste in a language whose ecosystem you cannot rename.

**Why trailing `_` for members**: constructor initializer lists read unambiguously (`width_(width)`), and no shadowing warnings from `-Wshadow`. Do not use `m_` or plain names plus setter/getter gymnastics.

```cpp
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

Comments that narrate what the code already says are rot-prone noise (`NL.1`): compilers never read them and they drift. State it in code or delete the comment. Comments earn their place by stating intent the code cannot express — why, constraints, expected behavior (`NL.2`). If a comment and its code disagree, treat both as wrong until reconciled. Keep comments crisp, grammatical, and professional: verbosity spreads understanding thin, SMS spelling ages badly (`NL.3`). Purely a review matter — no tool can catch a bad comment.

### House Style Beyond the Table

- No Hungarian-style type warts (`NL.5`): names describe functionality, and overloading matches types automatically. Role prefixes stay legal (`size_`, `cnt_hits`) because they encode purpose, not type — exactly what the table above permits.
- Name length proportional to scope (`NL.7`): short conventional names (`i`, `p`) locally, descriptive names for anything visible across functions; a cryptic one-letter global is always wrong.
- One house style for our code, imported libraries keep theirs (`NL.8`) — the table above is that house style. Reserved identifiers (`__`-prefixed or leading `_X`) stay banned along with everything else the standard reserves.
- `ALL_CAPS` is reserved for macros (`NL.9`) so a shouting identifier always means text-substitution hazard; constants and scoped-enum values take `k` names per the table, never caps.
- Deviation from `NL.10`: upstream prefers `underscore_style` names across the board; we adopt snake_case where the table says so (functions, variables) and PascalCase for types — same intent (standard-library rhythm, consistency beats taste) with the split documented here as the difference.
- Reject easily misread names (`NL.19`) — `oO01lL`, near-twin pairs like `splunk`/`splonk`: screens differ and humans skim. A standing naming-review duty alongside the table.
- One name per declaration (`NL.21`): `int a, b;` invites declarator-syntax confusion, and splitting costs nothing while reading better.
- Write `f()`, not `f(void)` (`NL.25`): in C++ the empty parameter list already means no parameters, and the C-compat ceremony adds nothing.
- West const (`const int x`, `const T&`) per conventional notation (`NL.26`): east const is logically defensible but unfamiliar to most readers; consistency wins and suffixed `const` is rejected in review.
- Interface files end `.h`, implementation files `.cpp` (`NL.27`); the exact letters matter less than uniformity — same disposition as `SF.1` under Header Hygiene below.

### Readable Literals

Make literals readable (`NL.11`): digit separators (`299'792'458`) and typed suffixes (`"..."s`, `100ms`) where the type matters. Long bare digit runs are typo farms, and magic constants stay banned separately.

### Layout Is Delegated to clang-format

Five Guidelines rules are layout-shaped, and hand-policing formatting wastes the exact attention reviews exist for. The committed `.clang-format` encodes each decision once:

- Indentation (`NL.4`): consistent indentation prevents real defects — the swallowed-control-statement bug — but the decision is mechanical.
- Whitespace restraint (`NL.15`): no `< map >`-style padding.
- Brace placement (`NL.17`): K&R-derived Stroustrup layout, encoded once by the formatter.
- Declarator layout (`NL.18`): C++ style, `T& name`, type-emphasized rather than expression-emphasized.
- Line packing (`NL.20`): two statements on one line hide defects from skimmers and diff readers alike; keeping them apart is the formatter's job.

Deviation from each of `NL.4`, `NL.15`, `NL.17`, `NL.18`, and `NL.20`: the intent is adopted and the mechanism delegated entirely to the committed clang-format configuration — deliberately not hand-policed.

---

## Static Analysis Curation

clang-tidy earns its keep on changed sources only when curated — wholesale category dumps bury signal under hundreds of hits.

Worth enabling (low noise, high yield):

| Checks | Why |
|--------|-----|
| `bugprone-*` | Real defect patterns: use-after-move, dangling references, suspicious casts |
| `performance-*` | Unnecessary copies, pass-by-value misses, inefficient calls |
| `modernize-*` | Mechanical language hygiene (`use-override`, `use-nullptr`, `use-emplace`) |
| Selected `misc-*` (`misc-unused-*`) | Dead declarations and parameters |

Leave off by default:

| Checks | Why off |
|--------|---------|
| `bugprone-easily-swappable-parameters` | Notoriously noisy; the parameter-role contract in [Functions and Interfaces](./functions-and-interfaces.md) fixes the design instead |
| `modernize-use-trailing-return-type` | Style churn; the local return-type convention already decides |
| `readability-identifier-naming` without a committed config | Churn generator unless the naming table ships beside the repo (see Naming Conventions above) |
| House-style families (`llvm-*`, `fuchsia-*`, ...) | Someone else's conventions; mechanical style belongs to clang-format |

Individual `cppcoreguidelines-*` picks — slicing, uninitialized locals, old-style casts (`cppcoreguidelines-slicing`, `-init-variables`, `-pro-type-cstyle-cast`) — are curated with rationale in [Core Guidelines Alignment](./core-guidelines-alignment.md); enabling that family wholesale stays rejected.

---

## Header Hygiene

### File Suffixes and Namespaces

`.cpp` for code files, `.h` for interface files, everywhere unless an existing project convention wins (`SF.1`) — identical in substance to `NL.27` in the naming section; uniformity is the point, not the letters. Namespaces mirror logical structure (`SF.20`): components and layers, short and lowercase per the naming table — `net`, `http`.

### Include What You Use

Every header must be **self-contained** (`SF.11`): it includes everything its own code names — include what you name (`SF.10`), never depending on what a transitively included header happens to drag in; deliberate aggregation headers remain acceptable. Enforce mechanically (`SF.5`): make each header the *first* include of its own `.cpp`. Includes go first in both `.h` and `.cpp` (`SF.4`); upstream's include-after-code insulation trick protects exactly one level, which is why it is not adopted here.

```cpp
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

### Include Spelling and Form

Quoted includes for locally relative files, angle brackets for everything else (`SF.12`): quoting a search-path header risks a future sibling file silently shadowing the intended one. Spell header identifiers exactly as on disk (`SF.13`) — matching case, `/` separators, never backslashes — because the standard leaves lookup unspecified and platform-specific paths do not survive porting.

### Forward Declarations

Forward-declare only what you can: parameters, references, pointers, and return-pointer types in declarations. Anything requiring size, members, or base classes needs the full type.

```cpp
// widget.h

// OK: incomplete types suffice for these declarations
class Engine;
Widget(const Engine& engine);
Engine* engine() const;

// Wrong: member by value and inheritance need the complete type
#include "engine.h"
class Widget : public Engine { /*...*/ };   // include, do not forward-declare

// Forbidden: forward-declaring anything in namespace std
namespace std { class string; }             // undefined behavior per [namespace.std]
```

Rules of thumb:

- Never forward-declare `std::` types — it is UB. Include `<string>` etc.
- Prefer including over forward-declaring for project headers unless compile-time pain is measured, not assumed.
- One header declares one primary type; do not chain forward declarations to break artificial cycles that better layering would remove.

### Cycles Mean Layering Bugs

Eliminate cyclic includes with better layering; do not paper over them with guards (`SF.9`) — the same stance as refusing forward-declaration chains to break artificial cycles that better layering would remove.

### Include Guards: `#pragma Once`

Use `#pragma once`. It is non-standard but universally supported by GCC, Clang, and MSVC — decades of mainstream support. Classic guards are longer, invite copy-paste typos (`#endif // WRONG_NAME` fails silently), and collide when two directories contain identically named headers. Fall back to guards only if you must support exotic preprocessors.

Deviation from `SF.8`: the intent — every header included at most once per translation unit — is adopted wholesale, while the mechanism differs deliberately: `#pragma once` over classic guards, with fallback guards still carrying component-keyed names despite upstream's ISO-guard preference.

```cpp
// Preferred
#pragma once

// Acceptable fallback, done correctly
#ifndef MYLIB_NET_WIDGET_H_
#define MYLIB_NET_WIDGET_H_
// ...
#endif  // MYLIB_NET_WIDGET_H_
```

### What Belongs in a Header

Headers carry declarations, templates, class definitions, and `inline`/`constexpr` definitions (`SF.2`) — never namespace-scope object definitions or non-inline function bodies, which duplicate per translation unit and die in linkage errors. Inline Variables below shows the sanctioned shape for header constants. Anything declared in multiple source files gets one home in a header (`SF.3`): hand-written `extern` declarations drift silently until the linker complains late.

### `using namespace`

Deviation from `SF.6`: `using namespace` is tolerated sparingly inside `.cpp` files (a translation unit counts as local scope) and during transitions, but we stop short of blessing blanket `using namespace std;` — qualify when ambiguity threatens. Never in headers (`SF.7`): at global scope it hijacks every includer's name lookup and makes include order semantically load-bearing. The `std::literals` exception stands because user-defined-literal rules prevent collisions.

### Internal Linkage: Anonymous Namespaces

File-local helpers in `.cpp` files go in an anonymous namespace (`SF.22`: all internal, non-exported entities live there — preferred over `static` for uniformity with type declarations, with exported entities staying outside). Anonymous namespaces in headers are forbidden (`SF.21`): every including translation unit gets its own private copies, silently duplicating code and data and tripping ODR-sensitive tools.

```cpp
// parser.cpp

// Right: helpers invisible outside this translation unit
namespace {
constexpr int kMaxDepth = 64;

bool is_delim(char c) noexcept { return c == ',' || c == ';'; }
}  // namespace

// Wrong (in a header): one copy per including TU
namespace {
int helper_count = 0;                   // N distinct variables after inclusion
}
```

---

## ODR and ABI Pitfalls

### Inline Variables (C++17)

Namespace-scope constants defined in headers must be `inline constexpr` (`SF.2` bans object definitions in headers outright; this inline form is the sanctioned shape) so there is exactly one entity across all translation units. A plain `const` integral at namespace scope has internal linkage: legal, but each TU gets its own copy, and any address-taken use diverges or breaks.

```cpp
// config.h — included everywhere

// Right: one object program-wide, safe to take addresses of
inline constexpr std::array<Mode, 3> kModes{Mode::kFast, Mode::kSafe, Mode::kRaw};
inline constexpr int kMaxConnections = 128;

// Wrong (pre-C++17 habit): per-TU copies, ODR traps when addresses are compared
static const int kMaxConnections = 128;
```

### Static Initialization Order Fiasco

Initialization order of namespace-scope objects across translation units is unspecified. Any global whose constructor reads another global is reading garbage on some platforms. Use `constexpr` initialization where possible, otherwise function-local statics (thread-safe since C++11).

```cpp
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

// Best when expressible: compile-time init removes the question entirely
inline constexpr Config kDefaults{/* ... */};
```

C++20 note: mark such globals `constinit` to force compile-time initialization and turn order bugs into compile errors once the baseline moves.

### PIMPL for Published Libraries

Headers of libraries distributed as binaries must not expose private members: adding a member later changes `sizeof` and breaks ABI. Hide privates behind a pointer-to-implementation. Source-shipped internal code does not need this ceremony.

```cpp
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

`dynamic_cast` and `typeid` require identical RTTI representations on both sides of a module boundary. Independently built modules (different compiler versions or flags) cannot rely on them; use explicit interface virtuals, enum kind tags, or visitor patterns instead.

```cpp
// Wrong: works in unit tests, returns nullptr across mismatched modules
if (auto* http = dynamic_cast<const HttpEvent*>(&ev)) { /*...*/ }

// Right: dispatch through the interface contract
switch (ev.kind()) {
    case EventKind::kHttp: handle_http(static_cast<const HttpEvent&>(ev)); break;
    case EventKind::kTimer: handle_timer(static_cast<const TimerEvent&>(ev)); break;
}
```

The same caution applies to throwing custom exception types across module boundaries — see error-handling guidelines: exceptions stay inside one module world.

---

## Enumerations

Scoped `enum class` everywhere (`Enum.3`): plain enums convert to `int` too readily, and unrelated enumerations collide on shared enumerator names. Enumerators take constant naming — `k` prefix, `PascalCase` — never `ALL_CAPS`, which stays reserved for macros (`Enum.5`; see the scoped-enum row in the naming table).

```cpp
// Wrong: implicit conversion to int, shouting names, collision-prone
enum Color { RED, GREEN };
int x = RED;

// Right: scoped, quiet names, no implicit conversion
enum class Color { kRed, kGreen };
Color c = Color::kRed;
// int x = Color::kRed;   // does not compile
```

Define the operations enumeration users need (`Enum.4`) — a wrapping `operator++` for iteration-like sets, for instance. The required `static_cast` round-trip is accepted idiom, while expressions repeatedly casting back into the enum signal a missing operation. Unnamed enumerations are unrelated integer constants in costume: declare each value as `constexpr` instead (`Enum.6`), which also gives it the right individual type — the constexpr-discipline section below applied.

Leave the underlying type at its default unless necessary (`Enum.7`); specifying it is required for forward-declarable enums and fixed bit width — precisely the ABI-sensitive-header situations flagged under ODR and ABI above. Give enumerators explicit values only when meaning demands it (`Enum.8`): conventional numbering such as months starting at 1, or bit-flag sets. Duplicate values are typos, and hand-written consecutive values are noise. Cross-module kind tags (see the RTTI caution above) follow exactly this shape: scoped enum, `k`-named enumerators.

---

## Compile-Time Discipline: `constexpr` and Friends

Use compile-time evaluation **where it is free**: pure computations, lookup tables, literal formatting, trait-like dispatch. Do not obfuscate straightforward runtime logic as template metaprogramming without a measured benefit; unreadable zero-cost is usually negative-cost once maintenance is priced in.

```cpp
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

// Good: C++17 if constexpr replaces SFINAE towers with readable branches
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
- C++17 lambdas can be `constexpr`; prefer them over hand-unrolled tables.
- C++20 additions, adopt on upgrade: `consteval` for must-be-compile-time functions, `constinit` for guaranteed-initialized globals, `consteval`-checked formatting.

---

## Quality Check

Before merging, confirm:

- [ ] Names match the table: `PascalCase` types, `snake_case` functions, trailing `_` members, `k`-prefixed constants and scoped-enum values
- [ ] Every header compiles standalone (first include in its own `.cpp`)
- [ ] No reliance on transitive includes; no forward-declared `std::` types
- [ ] `#pragma once` present; anonymous namespaces appear only in `.cpp` files
- [ ] Namespace-scope globals in headers are `inline constexpr`
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
