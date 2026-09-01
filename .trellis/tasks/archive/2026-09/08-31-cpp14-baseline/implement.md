# Implement: Lower C++ guideline baseline to C++14

## Order

1. **S0 tooling** — tools/rules_grammar.py (`MARKER_CXX17_RE`, `Fence.cxx17`),
   tools/check_snippets.py (CXX14_FLAGS + flag selection + docstring),
   tools/stubs/** (dialect guards). Verify: stubs compile at c++14/17/20.
2. **S1–S6 doc slices** — one parallel batch, files disjoint per design.md
   slice table. Each slice: apply Contracts 1–2 to its docs; mark fences per
   Contract 3; run `python3 tools/validate_rules.py` (0 violations) and
   `python3 tools/check_snippets.py 2>&1 | grep <own-doc>` (own rows ok);
   never run extract_rules.py.
3. **Integration (main session)** — extract_rules.py twice + determinism
   cmp; full gate suite; AC4 grep; AC6 hand-compiles; straggler fixes.

## Validation commands

```bash
# per-slice (read-only checks)
python3 tools/validate_rules.py
python3 tools/check_snippets.py 2>&1 | grep '<doc-name>'

# integration (writes rules.json)
python3 tools/extract_rules.py && cp specs/cpp/cpp/rules.json /tmp/rules-a.json \
  && python3 tools/extract_rules.py && cmp specs/cpp/cpp/rules.json /tmp/rules-a.json
python3 tools/check_snippets.py
python3 -c "import json; d=json.load(open('index.json')); import os; missing=[t['path'] for t in d['templates'] if not os.path.isdir(t['path'])]; print('missing:', missing) or exit(bool(missing))"
# link gate: python heredoc from registry index.md Quality Check
# AC6: g++ -std=c++14 -Wall -Wextra -isystem tools/stubs/include -fsyntax-only <stub+snippet>
```

## Review gates

- After S0: stub triple-dialect compile proof before doc slices trust the
  gate.
- After integration: all gates green + AC spot-checks before commit.

## Rollback

Single revert of the working tree (all slices disjoint; no interleaved
history). No data migrations; rules.json is derived.
