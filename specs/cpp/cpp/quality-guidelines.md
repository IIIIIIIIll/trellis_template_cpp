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
