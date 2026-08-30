# Fixture: Valid Rules

<!-- Grammar fixture for tools/validate_rules.py --path. Expected: zero
     violations. Not a snippet-harness fixture; the cpp fence is not meant to
     compile. Covers: block grammar, list-item form, table-cell markers with
     section-default inheritance, caught-by inheritance, single-fence
     Wrong/Right encoding, same-page anchor links. -->

## Section One

Default strength: default.

**MEM-1 (hard).** Never own a single object with `new`/`delete`; take RAII
ownership in one step (`R.11`).

```cpp
// Wrong: release wired to every return path by hand
void probe(const char* path) {
    FILE* f = std::fopen(path, "r");
    if (!load(f)) {
        std::fclose(f);
        return;
    }
    std::fclose(f);
}

// Right: ownership expressed in the type
```

Caught by: review — no automated detector.

- **ERR-1 (default).** Return an owning type or an `std::optional`; a sentinel
  is not a value.

Caught by: review — no automated detector.

Caught by: ASan for leak-shaped regressions in this section.

| Rank | Owner | Use when |
|------|-------|----------|
| **MEM-2** | `std::unique_ptr<T>` | Single owner, dynamic lifetime |
| **MEM-3 (hard)** | Owning raw `new`/`delete` | Never |

Same-page anchors resolve too: [Section One](#section-one).

## Section Two

**TPL-1 (default).** One template, one job; see [Section One](#section-one).

Caught by: review — no automated detector.
