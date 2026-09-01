# Dialect probe results (2026-08-31, g++ 13.3.0, Ubuntu 24.04)

Method: /tmp probes, `g++ -Wall -Wextra -fsyntax-only`, one construct each.
Grounds design.md Contract 4; verified before any repo file changes.

| Probe | Result | Consequence |
|-------|--------|-------------|
| `#include <optional>` / `<string_view>` / `<variant>` at `-std=c++14` | Compiles (contents guarded out; names absent) | Includes survive, but any stub *declaration naming* `std::optional` / `std::string_view` / `std::variant` fails at C++14 → guard declarations (portability: guard includes too — libc++ hard-errors these includes pre-C++17) |
| `inline` namespace-scope variable at `-std=c++14` | Warning `-Wc++17-extensions` only; compiles | Stub inline variables need no rewrite (gate has no `-Werror`); fence policy still marks C++17-idiom fences |
| `std::span<int>` at `-std=c++17` | Does not exist (with or without `<span>`) | Today's green gate at C++17 proves **no fence currently names `std::span` in code** — span is prose-only; nothing to marker-annotate for span |
| `tl/expected.hpp` (stub backfill) at `-std=c++14` | Fails: internal `std::variant<T,E>` store_ (line 47) | Guard the expected include behind `#if __cplusplus >= 201703L`; error-handling fences naming `expected` carry `// C++17`; ERR prose gets a C++14 fallback note (status enum / bool+value pair) |
| Generic lambda at `-std=c++14` | Compiles | Baseline paragraph parenthetical valid |
| Relaxed `constexpr` (loop + static_assert) at `-std=c++14` | Compiles | Baseline paragraph parenthetical valid |

Implications for S0:

1. stubs.hpp: guard C++17-only declarations (optional/string_view/variant
   signatures, `BytesView` alias) behind `#if __cplusplus >= 201703L`; guard
   the `tl/expected.hpp` / `result.h` include the same way. Inline variables
   stay.
2. No fence needs a span marker today; `// C++20` marker grammar remains for
   prose-mandated C++20 idioms only.
3. C++14 fallback spellings needed in prose: `string_view` → `const
   std::string&`; `optional<T>` value results → named result struct /
   status enum (per ERR-12) / nullable `T*` for positions; `if constexpr` →
   tag dispatch / overload resolution; `[[nodiscard]]` → comment convention;
   inline variables → function-local static accessors; structured bindings →
   `.first/.second` or named struct fields.
