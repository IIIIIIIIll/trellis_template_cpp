# C++17 fence marker worklist (2026-08-31)

Derived with tools/rules_grammar.py fence parsing; comments stripped before
symbol matching, so every entry names the symbol in CODE, not prose.
Policy (design.md Contract 3): each listed fence gets a `// C++17` comment
line at/near the fence top. No fence uses `std::span` in code (see
dialect-probes.md), so no span markers exist today.

## functions-and-interfaces.md — 14 fences (slice S1)

35, 108, 127, 158, 167, 177, 185, 195, 259 (string_view+nodiscard), 290
(optional), 320, 333, 352 (nodiscard), 487 (optional+nodiscard)

## classes-and-hierarchies.md — 6 fences (slice S4)

35 (nodiscard), 340, 378, 416, 472, 515 (variant)

## quality-guidelines.md — 3 fences (slice S4)

335 (inline-var), 377, 489 (if constexpr)

## error-handling.md — 4 fences (slice S5)

44 (optional), 121 (expected — include guarded to >= 201703L in stubs), 140,
345

## performance.md — 2 fences (slice S5)

149, 181 (inline-var)

## memory-and-ownership.md — 4 fences (slice S2)

38, 121, 184, 199

## templates-and-generics.md — 3 fences (slice S3)

114 (optional), 130 (optional), 282 (if constexpr)

## core-guidelines-disposition.md — 1 fence (slice S6)

42

Totals: 37 fences; symbol counts — string_view 22, nodiscard 8, optional 5,
inline-var 2, if constexpr 2, variant 1, expected 1.

Note for slices: line numbers are the fence MARKER lines from today's tree;
they shift as prose edits land — re-locate fences by content, not by line.
