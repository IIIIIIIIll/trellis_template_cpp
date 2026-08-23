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

---

## Header Hygiene

### Include What You Use

Every header must be **self-contained**: it includes everything its own code names, and never relies on a transitive include arriving first by luck. Enforce mechanically: make each header the *first* include of its own `.cpp`.

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

### Include Guards: `#pragma Once`

Use `#pragma once`. It is non-standard but universally supported by GCC, Clang, and MSVC — decades of mainstream support. Classic guards are longer, invite copy-paste typos (`#endif // WRONG_NAME` fails silently), and collide when two directories contain identically named headers. Fall back to guards only if you must support exotic preprocessors.

```cpp
// Preferred
#pragma once

// Acceptable fallback, done correctly
#ifndef MYLIB_NET_WIDGET_H_
#define MYLIB_NET_WIDGET_H_
// ...
#endif  // MYLIB_NET_WIDGET_H_
```

### Internal Linkage: Anonymous Namespaces

File-local helpers in `.cpp` files go in an anonymous namespace (preferred over `static` for uniformity with type declarations). Anonymous namespaces in headers are forbidden: every including translation unit gets its own private copies, silently duplicating code and data and tripping ODR-sensitive tools.

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

Namespace-scope constants defined in headers must be `inline constexpr` so there is exactly one entity across all translation units. A plain `const` integral at namespace scope has internal linkage: legal, but each TU gets its own copy, and any address-taken use diverges or breaks.

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

---

## Complete Coverage: NL, SF, Enum

The sections above teach the rules that need explaining; this closing table sweeps up the remaining `NL` (naming and layout), `SF` (source files), and `Enum` (enumerations) rules from the ISO C++ Core Guidelines so no rule ID is left implicit. Rules marked **Adapt** are layout-shaped and delegated entirely to the committed clang-format configuration — they are deliberately not hand-policed.

| Rule | Stance | Disposition |
|------|--------|-------------|
| `NL.1` | Adopt | Comments that narrate what the code already says are rot-prone noise: compilers never read them and they drift. State it in code or delete the comment. |
| `NL.2` | Adopt | Comments earn their place stating intent the code cannot express — why, constraints, expected behavior. If a comment and its code disagree, treat both as wrong until reconciled. |
| `NL.3` | Adopt | Keep comments crisp, grammatical, and professional: verbosity spreads understanding thin, SMS spelling ages badly. Purely a review matter — no tool can catch it. |
| `NL.4` | Adapt | Consistent indentation prevents real defects (the swallowed-control-statement bug), but the decision is mechanical: delegated to committed .clang-format. |
| `NL.5` | Adopt | No Hungarian-style type warts: names describe functionality, overloading matches types automatically. Role prefixes stay legal (`size_`, `cnt_hits`) because they encode purpose, not type — exactly what the naming table permits. |
| `NL.7` | Adopt | Name length proportional to scope: short conventional names (`i`, `p`) locally, descriptive names for anything visible across functions; a cryptic one-letter global is always wrong. |
| `NL.8` | Adopt | One house style for our code, imported libraries keep theirs — the naming table above is that house style. Also bans reserved identifiers (`__`, leading `_X`). |
| `NL.9` | Adopt | `ALL_CAPS` is reserved for macros so a shouting identifier always means text-substitution hazard; constants and scoped-enum values take `k` names per the table, never caps. |
| `NL.10` | Adapt | Upstream prefers underscore_style across the board; we adopt snake_case where the table says so (functions, variables) and PascalCase for types — same intent (standard-library rhythm, consistency beats taste) with the split documented here. |
| `NL.11` | Adopt | Make literals readable: digit separators (`299'792'458`) and typed suffixes (`"..."s`, `100ms`) where the type matters; long bare digit runs are typo farms, and magic constants stay banned separately. |
| `NL.15` | Adapt | Whitespace restraint (no `< map >`-style padding) is purely mechanical formatting: delegated to committed .clang-format. |
| `NL.16` | Adopt | Conventional member order — types, constructors/assignment/destructor, functions, data, `public` before `protected` before `private`, no scattered access blocks. The formatter never reorders declarations, so this remains a review convention. |
| `NL.17` | Adapt | K&R-derived (Stroustrup) brace placement is a layout decision like any other: delegated to committed .clang-format, which encodes brace style once. |
| `NL.18` | Adapt | C++-style declarator layout (`T& name`, type-emphasized rather than expression-emphasized) is a formatter setting: delegated to committed .clang-format rather than re-litigated per review. |
| `NL.19` | Adopt | Reject easily misread names — `oO01lL`, near-twin pairs like `splunk`/`splonk`: screens differ and humans skim. A standing naming-review duty alongside the table. |
| `NL.20` | Adapt | Two statements on one line hide defects from skimmers and diff readers alike; line packing is the formatter's job: delegated to committed .clang-format. |
| `NL.21` | Adopt | One name per declaration: `int a, b;` invites declarator-syntax confusion, and splitting costs nothing while reading better. |
| `NL.25` | Adopt | Write `f()`, not `f(void)` — in C++ the empty parameter list already means no parameters, and the C-compat ceremony adds nothing. |
| `NL.26` | Adopt | West `const` (`const int x`, `const T&`): east const is logically defensible but unfamiliar to most readers; consistency wins and suffixed `const` is rejected in review. |
| `NL.27` | Adopt | `.h` for interface files, `.cpp` for implementation — longstanding defaults whose exact letters matter less than uniformity; same disposition as `SF.1` below. |
| `SF.1` | Adopt | `.cpp`/`.h` suffixes everywhere unless an existing project convention wins; identical in substance to `NL.27`. |
| `SF.2` | Adopt | Headers carry declarations, templates, class definitions, and `inline`/`constexpr` definitions — never namespace-scope object definitions or non-inline function bodies, which duplicate per TU and die in linkage errors. |
| `SF.3` | Adopt | Anything declared in multiple source files gets one home in a header; hand-written `extern` declarations drift silently until the linker complains late. |
| `SF.4` | Adopt | Includes go first in both `.h` and `.cpp`; upstream's include-after-code insulation trick protects exactly one level, which is why it is not adopted here. |
| `SF.5` | Adopt | Every `.cpp` includes its own interface header first, so declaration/definition mismatches surface at compile time instead of link time — the self-contained-header discipline above. |
| `SF.6` | Adapt | `using namespace` is tolerated sparingly inside `.cpp` files (upstream counts a translation unit as local scope) and during transitions; we stop short of blessing blanket `using namespace std;` — qualify when ambiguity threatens. Never in headers (`SF.7`). |
| `SF.7` | Adopt | `using namespace` at global scope in a header hijacks every includer's name lookup and makes include order semantically load-bearing; the `std::literals` exception stands because user-defined-literal rules prevent collisions. |
| `SF.8` | Adapt | Intent adopted — each header included at most once per translation unit; mechanism differs deliberately: `#pragma once` over classic guards per Include Guards above, with fallback guards still carrying component-keyed names (upstream's collision advice kept despite its ISO-guard preference). |
| `SF.9` | Adopt | Eliminate cyclic includes with better layering; do not paper over them with guards — the same stance as refusing forward-declaration chains to break artificial cycles. |
| `SF.10` | Adopt | Never depend on what a transitively included header happens to drag in: include what you name. Deliberate aggregation headers remain acceptable. |
| `SF.11` | Adopt | The self-contained-header rule above is this rule operationalized: a header compiles on its own, proven by making it the first include of its own `.cpp`. |
| `SF.12` | Adopt | Quoted includes for locally relative files, angle brackets for everything else; quoting a search-path header risks a future sibling file silently shadowing the intended one. |
| `SF.13` | Adopt | Header identifiers spelled exactly as on disk — matching case, `/` separators, never backslashes — because the standard leaves lookup unspecified and platform-specific paths do not survive porting. |
| `SF.20` | Adopt | Namespaces mirror logical structure — components and layers, short and lowercase per the naming table. |
| `SF.21` | Adopt | Anonymous namespaces in headers grant every includer private copies of everything inside: banned in the Internal Linkage section for exactly this reason. |
| `SF.22` | Adopt | The inverse of `SF.21`, codified above: `.cpp` internals (helpers, constants) live in an anonymous namespace, preferred over `static` for uniformity with type declarations; exported entities stay outside. |
| `Enum.3` | Adopt | Scoped `enum class` everywhere: plain enums convert to `int` too readily and unrelated enumerations collide on enumerator names. |
| `Enum.4` | Adopt | Define the operations enumeration users need, such as a wrapping `operator++`; the required `static_cast` round-trip is accepted idiom, while expressions repeatedly cast back into the enum signal a missing operation. |
| `Enum.6` | Adopt | Unnamed enumerations are unrelated integer constants in costume; declare each value as `constexpr` instead, which also gives it the right individual type — the constexpr-discipline section applied. |
| `Enum.7` | Adopt | Leave the underlying type at its default unless necessary; specifying it is required for forward-declarable enums and for fixed bit width — precisely the ABI-sensitive-header situations this guide flags. |
| `Enum.8` | Adopt | Explicit enumerator values only when meaning demands it: conventional numbering such as months starting at 1, or bit-flag sets; duplicate values are typos and hand-written consecutive values are noise. |

---

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
