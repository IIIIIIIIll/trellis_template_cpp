#!/usr/bin/env python3
"""validate_rules.py — repo gate over the cpp guideline rule-block grammar.

Normative grammar and author-facing contract:
.trellis/spec/registry/guideline-authoring.md.

Checks per run:
  * lead-ins match `**<AREA>-<n> (hard|default).**` at paragraph start or after
    "- "; table first cells match `**<ID>**` / `**<ID> (hard|default)**`
  * prefixes match the allocation table; IDs unique across the run
  * strength present: block/cell marker, else the section's standalone
    `Default strength: hard.` / `Default strength: default.` line; otherwise a
    violation (no silent defaulting)
  * `Caught by:` present in the rule block or inherited from the nearest
    preceding line in the same section, else violation
  * Wrong/Right pairing per example group (exactly one Wrong and one Right;
    all three encodings)
  * footer contract per shipped guide (--- + **Language** line + attribution)
  * relative markdown links resolve; anchor fragments must match a heading slug

Scope: the 14 topic guides under specs/cpp/cpp/ (design/, implement/,
verification/), which rglob discovers; index.md, the three phase routers,
and core-guidelines-disposition.md are exempt. Pass --path to validate other
files or directories (e.g. the grammar fixtures under tools/testdata/).
Footer checks bind shipped guides only; rule checks bind non-exempt docs.

Exit status: 0 = no violations, 1 = violations reported, 2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rules_grammar as rg  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DIR = REPO / "specs" / "cpp" / "cpp"


def default_docs():
    return [
        p
        for p in sorted(DEFAULT_DIR.rglob("*.md"))
        if p.name not in rg.EXEMPT_DOCS
    ]


def docs_from_paths(paths):
    docs = []
    for p in paths:
        if p.is_dir():
            docs.extend(sorted(p.rglob("*.md")))
        else:
            docs.append(p)
    if not docs:
        raise SystemExit(2)
    return docs


def footer_violations(doc: rg.ParsedDoc):
    out = []
    nonblank = [i for i, ln in enumerate(doc.lines) if ln.strip()]

    def at(pos):
        return doc.lines[nonblank[pos]].strip() if -len(nonblank) <= pos < len(nonblank) else None

    if not nonblank:
        return [(1, "E-FOOTER", "document has no content")]
    if at(-1) != rg.ATTRIB_LINE:
        out.append(
            (
                nonblank[-1] + 1,
                "E-FOOTER",
                "last non-blank line is not the Core Guidelines attribution footer",
            )
        )
    if at(-2) != rg.LANG_LINE:
        out.append(
            (
                nonblank[-1] + 1,
                "E-FOOTER",
                "second-to-last non-blank line is not the `**Language**:` note",
            )
        )
    if at(-3) != "---":
        out.append(
            (nonblank[-1] + 1, "E-FOOTER", "footer must be preceded by a `---` rule")
        )
    return out


def link_violations(doc: rg.ParsedDoc, doc_dir: Path):
    out = []
    slug_cache = {}

    def slugs_for(md_path: Path):
        if md_path not in slug_cache:
            text = md_path.read_text(encoding="utf-8")
            parsed = rg.parse(text, md_path.name, str(md_path))
            slug_cache[md_path] = {rg.slugify(t) for _l, _lv, t in parsed.headings}
        return slug_cache[md_path]

    for i, raw in enumerate(doc.lines):
        if doc.masked[i]:
            continue
        line = rg.INLINE_CODE_RE.sub(" ", raw)
        for m in rg.MD_LINK_RE.finditer(line):
            target = m.group(1)
            if rg.SCHEME_RE.match(target):
                continue  # external reference
            file_part, _, frag = target.partition("#")
            if file_part:
                resolved = (doc_dir / file_part).resolve()
                if not resolved.exists():
                    out.append(
                        (
                            i + 1,
                            "E-LINK-FILE",
                            f"relative link target does not exist: {target}",
                        )
                    )
                    continue
            else:
                resolved = Path(doc.path)
            if frag and resolved.suffix == ".md":
                if frag not in slugs_for(resolved):
                    out.append(
                        (
                            i + 1,
                            "E-LINK-FRAGMENT",
                            f"fragment #{frag} does not match any heading in {resolved.name}",
                        )
                    )
    return out


def check_doc(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc}")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid UTF-8: {exc}")
    doc = rg.parse(text, path.name, str(path))
    violations = [(v[0], v[1], v[2]) for v in doc.grammar_violations]

    expected = rg.DOC_PREFIX.get(path.name)
    binds_rules = path.name not in rg.EXEMPT_DOCS
    for rule in doc.rules:
        if expected and rule.prefix != expected:
            violations.append(
                (
                    rule.line,
                    "E-PREFIX-DOC",
                    f"{rule.id} uses prefix {rule.prefix}; {path.name} allocates "
                    f"{expected}- (see the ID allocation table)",
                )
            )
        if not binds_rules:
            continue
        strength, why = rg.resolve_strength(rule, doc)
        if strength is None and not rule.strength_error:
            violations.append((rule.line, "E-STRENGTH-MISSING", f"{rule.id}: {why}"))
        caught, whyc = rg.resolve_caught_by(rule, doc)
        if caught is None:
            violations.append((rule.line, "E-CAUGHT-BY-MISSING", f"{rule.id}: {whyc}"))

    for g in doc.groups:
        w, r = g.wrong_count, g.right_count
        if w > 1:
            violations.append(
                (
                    g.start,
                    "E-PAIR-MULTIPLE-WRONG",
                    f"{w} Wrong markers in one example group; one rule block "
                    "carries exactly one Wrong and one Right",
                )
            )
        if r > 1:
            violations.append(
                (
                    g.start,
                    "E-PAIR-MULTIPLE-RIGHT",
                    f"{r} Right markers in one example group; one rule block "
                    "carries exactly one Wrong and one Right",
                )
            )
        if w == 1 and r == 0:
            violations.append(
                (
                    g.start,
                    "E-PAIR-UNPAIRED-WRONG",
                    "Wrong without a Right sibling in the same example group",
                )
            )
        if w == 0 and r == 1:
            violations.append(
                (
                    g.start,
                    "E-PAIR-UNPAIRED-RIGHT",
                    "Right without a Wrong sibling in the same example group",
                )
            )

    if path.name in rg.DOC_PREFIX or path.name in rg.EXEMPT_DOCS:
        violations.extend(footer_violations(doc))
    violations.extend(link_violations(doc, path.parent))
    return doc, violations


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Validate the cpp guideline rule-block grammar.",
        epilog="With no --path, validates the 14 topic guides under "
        "specs/cpp/cpp/ (index.md, the three phase routers, and "
        "core-guidelines-disposition.md are exempt from rule checks).",
    )
    ap.add_argument(
        "--path",
        nargs="+",
        type=Path,
        help="markdown file(s) or directory (all *.md directly inside) to "
        "validate instead of the default topic-guide set",
    )
    args = ap.parse_args(argv)

    try:
        docs = docs_from_paths(args.path) if args.path else default_docs()
    except SystemExit:
        print("error: --path matched no markdown files", file=sys.stderr)
        return 2

    all_violations = []
    seen_ids = {}
    for path in docs:
        if not path.exists():
            print(f"error: no such file: {path}", file=sys.stderr)
            return 2
        doc, violations = check_doc(path)
        for rule in doc.rules:
            if rule.id in seen_ids:
                violations.append(
                    (
                        rule.line,
                        "E-DUP-ID",
                        f"{rule.id} already defined at {seen_ids[rule.id]}",
                    )
                )
            else:
                seen_ids[rule.id] = f"{path.name}:{rule.line}"
        for line, code, msg in violations:
            all_violations.append((str(path), line, code, msg))

    all_violations.sort(key=lambda v: (v[0], v[1], v[2]))
    for rel, line, code, msg in all_violations:
        print(f"{rel}:{line}: {code}: {msg}")
    print(
        f"validate_rules: {len(docs)} doc(s) checked, "
        f"{len(all_violations)} violation(s)"
    )
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
