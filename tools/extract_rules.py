#!/usr/bin/env python3
"""extract_rules.py — generate the machine-readable rules digest (rules.json).

Parses the rule-block grammar (see rules_grammar.py) over the topic guides
and emits one JSON object per rule with exactly these fields:

  id         local rule ID, e.g. "MEM-7"
  strength   "hard" | "default" (marker, else the section's stated default)
  statement  first sentence of the rule block, markdown stripped
  doc        guide file basename, e.g. "memory-discipline.md"
  detector   verbatim `Caught by:` text (no trailing period); the explicit
             no-detector statement is normalized to "review"
  upstream   Core Guidelines IDs cited in the rule block, in first-appearance
             order (cross-reference anchors; no anchor/origin fields)

Output is sorted by doc, then numeric ID, and regenerates byte-identical.
rules.json is a generated artifact: never hand-edit it; regenerate instead.

Exit status: 0 = digest written, 2 = rules with unresolvable strength or
detector (regenerate only after the validator is green), or usage/IO error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rules_grammar as rg  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DIR = REPO / "specs" / "cpp" / "cpp"
DEFAULT_OUT = REPO / "specs" / "cpp" / "cpp" / "rules.json"


def default_docs():
    return [
        p
        for p in sorted(DEFAULT_DIR.rglob("*.md"))
        if p.name not in rg.EXEMPT_DOCS
    ]


def build_entries(docs):
    entries = []
    errors = []
    for path in docs:
        text = path.read_text(encoding="utf-8")
        doc = rg.parse(text, path.name, str(path))
        for rule in doc.rules:
            strength, why = rg.resolve_strength(rule, doc)
            caught, whyc = rg.resolve_caught_by(rule, doc)
            if strength is None or caught is None:
                detail = why if strength is None else whyc
                errors.append(f"{path}:{rule.line}: {rule.id}: {detail}")
                continue
            end = rule.block_end if rule.kind == "prose" else rule.line
            block_text = "\n".join(doc.lines[rule.line - 1 : end])
            entries.append(
                {
                    "id": rule.id,
                    "strength": strength,
                    "statement": rg.first_sentence(rg.clean_statement(rule.statement)),
                    "doc": path.name,
                    "detector": rg.normalize_detector(caught[1]),
                    "upstream": rg.upstream_ids(block_text),
                }
            )
    entries.sort(key=lambda e: (e["doc"], e["id"].split("-")[1].zfill(6)))
    return entries, errors


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate rules.json from the guideline rule blocks.",
        epilog="With no --path, reads the 14 topic guides under specs/cpp/cpp/. "
        "The output regenerates byte-identical; commit it, never hand-edit it.",
    )
    ap.add_argument(
        "--path",
        nargs="+",
        type=Path,
        help="markdown file(s) or directory to parse instead of the default "
        "topic-guide set",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"output path (default: {DEFAULT_OUT.relative_to(REPO)})",
    )
    args = ap.parse_args(argv)

    if args.path:
        docs = []
        for p in args.path:
            if p.is_dir():
                docs.extend(sorted(p.rglob("*.md")))
            else:
                docs.append(p)
        docs = [d for d in docs if d.name not in rg.EXEMPT_DOCS]
        if not docs:
            print("error: --path matched no markdown files", file=sys.stderr)
            return 2
    else:
        docs = default_docs()

    entries, errors = build_entries(docs)
    if errors:
        for e in errors:
            print(f"error: unresolvable rule: {e}", file=sys.stderr)
        print(
            f"error: {len(errors)} rule(s) missing strength or detector; "
            "run tools/validate_rules.py and fix the marking first",
            file=sys.stderr,
        )
        return 2

    payload = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"
    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot write {args.out}: {exc}", file=sys.stderr)
        return 2
    print(f"extract_rules: wrote {len(entries)} rule(s) to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
