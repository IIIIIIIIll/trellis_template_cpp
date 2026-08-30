# Fixture: Invalid Rules

<!-- Grammar fixture for tools/validate_rules.py --path. Expected: named
     violations — missing strength (no section default above), strength outside
     the closed vocabulary, missing Caught by with nothing to inherit,
     duplicate ID via a table cell, unpaired Wrong, unresolvable relative link
     and anchor fragment. -->

## Section One

**ERR-10.** Missing strength with no section default to inherit.

**ERR-11 (strict).** Strength outside the closed hard|default vocabulary.

**ERR-12.** Missing strength; the section default below is not visible above it.

Default strength: default.

**ERR-13 (hard).** Owns its detector statement; the ID repeats in the table below.

Caught by: review — no automated detector.

## Section Two

Wrong:

```cpp
void f() {
    int* p = new int;   // leak-shaped but compiles
}
```

Prose between fences ends the example group, so the Wrong above has no Right.

| Rank | Owner | Use when |
|------|-------|----------|
| **ERR-10** | Owning raw `new` | Never |

A trailing paragraph ends the group. [Broken file](./nope.md) and [bad anchor](#nope-anchor) are reported too.
