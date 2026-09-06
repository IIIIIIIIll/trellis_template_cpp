---
description: Header hygiene, ODR and ABI pitfalls, third-party dependency vetting
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Headers and Dependencies

> A header is compiled once per translation unit that includes it: these rules keep that build surface deliberate — include hygiene, ODR-safe constants, ABI-stable published interfaces, and third-party dependencies vetted before they harden into design decisions.

---

## Overview

A header is a build-surface contract, executed once per translation unit that includes it — treat everything it exposes as a design decision with link-time consequences. Self-contained headers and spelled includes keep translation units independent; the namespace-scope-object and anonymous-namespace rules keep the one-definition rule from being violated quietly. Published-binary stability (PIMPL, pinned enumerator values, no cross-module RTTI) is decided at the header, because `sizeof` and mangling freeze the moment the header ships. Third-party dependencies sit on the same boundary: the standard library is the default supplier, and anything beyond it is a permanent design decision vetted on maintenance, portability, license, and provenance before adoption.

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
// QUAL-30: header includes everything its own code names
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
// QUAL-35: forward-declare where incomplete types suffice
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
// QUAL-36: include the real header, never forward-declare std
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
// QUAL-45: anonymous namespace keeps file-local helpers internal
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
// QUAL-47: inline constexpr gives one program-wide object
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
// QUAL-48: function-local statics order cross-TU initialization
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
// QUAL-50: kind-tag dispatch replaces cross-module RTTI
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

**QUAL-51.** The RTTI caution above has a quieter sibling: the standard library itself must be binary-compatible on both sides of a module boundary. On GCC/libstdc++, the dual ABI decides what `std::string` means — `_GLIBCXX_USE_CXX11_ABI` selects between the classic and `__cxx11` layouts, and modules built with different settings will not link, because the mangled names do not match. The full independent-binary caveat lives in [Error Propagation](../implement/error-propagation.md); this is the same threat model arriving through the standard library instead of your own types. On MSVC the runtime flavor cannot be mixed either: `/MD` vs `/MT` and debug vs release CRT must agree across every module in the process — `_ITERATOR_DEBUG_LEVEL` is what turns a mismatch into a link error.

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

## Quality Check

Before merging header or dependency changes, confirm:

- [ ] Every header compiles standalone (first include in its own `.cpp`)
- [ ] No reliance on transitive includes; no forward-declared `std::` types
- [ ] `#pragma once` present; anonymous namespaces appear only in `.cpp` files
- [ ] Namespace-scope header constants exist once program-wide (`extern` + one definition, or `inline constexpr` on C++17+)
- [ ] No cross-TU global-constructor dependencies; accessor functions instead
- [ ] Binary-published library headers use PIMPL with out-of-line destructor/moves
- [ ] No `dynamic_cast`/`typeid` in cross-module headers
- [ ] Headers define no namespace-scope objects or non-inline functions; `using namespace` never appears in headers

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
