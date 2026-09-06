---
description: Naming conventions, enumerations, compile-time discipline
paths: [**/*.cpp, **/*.cc, **/*.cxx, **/*.hpp, **/*.hh, **/*.h, **/*.inl, **/*.ipp]
---

# Naming and Constants

> One documented house style applied without exception, scoped enums with `k`-prefixed enumerators, and compile-time evaluation used only where it clarifies — the written-code surface of the C++ guidelines.

---

## Overview

Names are the first API a reader meets: this guide commits to one documented mix — std call-site rhythm (`snake_case` functions and variables) with Google-style types and `k` constants — because consistency beats taste in a language whose ecosystem you cannot rename. Enumerations follow the same discipline: scoped `enum class` everywhere, `k`-prefixed enumerators, and explicit values only where meaning or a storage boundary demands them. Compile-time evaluation is a readability tool, not a flex — `constexpr` earns its place where the computation is naturally constant-evaluable, and template metaprogramming must buy measured benefit to justify its maintenance cost. Comments and layout round out the written-code surface: state intent rather than narration, and delegate formatting decisions to the committed clang-format configuration.

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
// QUAL-10: conforming names replace the four mixed styles
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

## Enumerations

Default strength: default.

Caught by: review — no automated detector.

**QUAL-57 (hard).** Scoped `enum class` everywhere (`Enum.3`): plain enums convert to `int` too readily, and unrelated enumerations collide on shared enumerator names.

```cpp
// QUAL-57: scoped enum class prevents implicit conversions
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
// QUAL-64: readable constexpr branches replace obfuscated metaprogramming
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

Before merging naming or constant changes, confirm:

- [ ] Names match the table: `PascalCase` types, `snake_case` functions, trailing `_` members, `k`-prefixed constants and scoped-enum values
- [ ] `constexpr` used only where it clarifies or measurably helps
- [ ] Scoped `enum class` with `k`-prefixed enumerators; unnamed enums standing in for constants are gone
- [ ] Comments state intent rather than narration; layout decisions live in .clang-format, not in review

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
