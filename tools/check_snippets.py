#!/usr/bin/env python3
"""check_snippets.py — compile gate over fenced ```cpp guideline examples.

For every fenced ```cpp block (with its doc, line, and preceding lead hint)
the harness prepends tools/stubs/stubs.hpp plus a #line directive and runs
`g++ -std=c++17 -Wall -Wextra -fsyntax-only` on the combined source, so
diagnostics carry the guideline's own doc:line coordinates.

Per-block classification (design.md "Snippet harness"):

  clean                Right blocks and unmarked/illustrative blocks — must
                       compile without errors.
  must-fail            Wrong blocks annotated `// compile-error` — must fail,
                       and the primary diagnostic must fall within ±2 lines of
                       an annotated line.
  ub                   Wrong blocks annotated `// compiles; UB at runtime` —
                       must compile; reported as a distinct inventory for
                       manual sanitizer spot-checks.
  wrong-unclassified   Wrong blocks with neither marker — violation. Every
                       Wrong block must state which class it belongs to; the
                       gate never silently defaults.

Right/unmarked fences reached through a `Wrong:` / `Right:` prose lead inherit
the lead's side. A fence carrying both Wrong and Right markers counts as
Wrong (the wrong construct is part of the translation unit).

Exit status: 0 = all blocks satisfy their class, 1 = violations, 2 = usage or
environment error (missing g++, missing stubs header, unreadable docs).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rules_grammar as rg  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DIR = REPO / "specs" / "cpp" / "cpp"
STUBS = Path(__file__).resolve().parent / "stubs" / "stubs.hpp"

CXX = "g++"
CXX_FLAGS = ["-std=c++17", "-Wall", "-Wextra", "-fsyntax-only"]
PROXIMITY = 2  # primary diagnostic may drift this many lines from the marker
DIAG_RE = re.compile(
    r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+"
    r"(?P<kind>fatal error|error|warning|note):\s+(?P<msg>.*)$",
    re.MULTILINE,
)


def default_docs():
    return sorted(DEFAULT_DIR.glob("*.md"))


def preceding_hint(doc: rg.ParsedDoc, fence: rg.Fence) -> str:
    j = fence.marker_line - 2  # 0-based index of the line above the opening fence
    while j >= 0:
        if doc.masked[j]:
            j -= 1
            continue
        s = doc.lines[j].strip()
        if not s or s.startswith("```") or rg.HR_RE.match(s):
            j -= 1
            continue
        return s
    return ""


def classify(fence: rg.Fence, hint: str) -> str:
    if fence.ub:
        return "ub"
    if fence.compile_error_lines:
        return "must-fail"
    lead = rg.WRONG_RIGHT_LEAD_RE.match(hint)
    if (lead and lead.group(1) == "Wrong") or fence.wrong_count:
        return "wrong-unclassified"
    return "clean"


def compile_block(stubs: str, doc: rg.ParsedDoc, fence: rg.Fence, tmpdir: Path):
    """Compile stubs + #line-anchored block; return (rc, diagnostics list)."""
    directive = f'#line {fence.content_first_line} "{doc.name}"\n'
    block = "\n".join(fence.content) + "\n"
    src = tmpdir / "block.cpp"
    src.write_text(stubs + directive + block, encoding="utf-8")
    try:
        proc = subprocess.run(
            [CXX, *CXX_FLAGS, str(src)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=tmpdir,
        )
    except subprocess.TimeoutExpired:
        return None, []
    diags = []
    for m in DIAG_RE.finditer(proc.stderr or ""):
        diags.append(
            {
                "file": m.group("file"),
                "line": int(m.group("line")),
                "col": int(m.group("col")),
                "kind": m.group("kind"),
                "msg": m.group("msg"),
            }
        )
    return proc.returncode, diags


def fmt_diag(diag, doc_name):
    mark = "" if diag["file"] == doc_name else " [stubs region]"
    return f"{diag['file']}:{diag['line']}:{diag['col']}: {diag['kind']}: {diag['msg']}{mark}"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Compile every fenced ```cpp guideline example against "
        "the stub header.",
        epilog="Classes: clean (Right/unmarked) must compile; `// compile-error` "
        "must fail near the annotation; `// compiles; UB at runtime` must "
        "compile and is inventoried; unclassified Wrong blocks are violations.",
    )
    ap.add_argument(
        "--path",
        nargs="+",
        type=Path,
        help="markdown file(s) or directory to check instead of the default "
        "guideline set",
    )
    args = ap.parse_args(argv)

    cxx = shutil.which(CXX)
    if cxx is None:
        print(f"error: {CXX} not found on PATH", file=sys.stderr)
        return 2
    if not STUBS.is_file():
        print(f"error: stubs header missing: {STUBS}", file=sys.stderr)
        return 2

    if args.path:
        docs = []
        for p in args.path:
            if p.is_dir():
                docs.extend(sorted(p.glob("*.md")))
            else:
                docs.append(p)
    else:
        docs = default_docs()
    if not docs:
        print("error: no markdown docs to check", file=sys.stderr)
        return 2

    stubs = STUBS.read_text(encoding="utf-8")
    if not stubs.endswith("\n"):
        stubs += "\n"

    rows = []  # (status, doc, fence, cls, hint, details)
    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        for path in docs:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                print(f"error: cannot read {path}: {exc}", file=sys.stderr)
                return 2
            doc = rg.parse(text, path.name, str(path))
            for fence in doc.fences:
                if fence.lang != "cpp":
                    continue
                hint = preceding_hint(doc, fence)
                cls = classify(fence, hint)
                rc, diags = compile_block(stubs, doc, fence, tmpdir)
                errors = [d for d in diags if d["kind"] in ("error", "fatal error")]
                details = []
                if cls == "clean":
                    ok = rc == 0
                    if not ok:
                        details.append("must compile clean; g++ failed")
                elif cls == "must-fail":
                    if rc == 0:
                        ok = False
                        details.append(
                            "marked `// compile-error` but the block compiles"
                        )
                    else:
                        primary = errors[0] if errors else None
                        if primary is None:
                            ok = False
                            details.append("compilation failed with no parsable diagnostic")
                        else:
                            near = any(
                                abs(primary["line"] - a) <= PROXIMITY
                                for a in fence.compile_error_lines
                            )
                            ok = near
                            if not near:
                                annotated = ", ".join(
                                    str(a) for a in fence.compile_error_lines
                                )
                                details.append(
                                    f"primary diagnostic at line {primary['line']} "
                                    f"is not within ±{PROXIMITY} of the "
                                    f"`// compile-error` annotation(s) at line(s) "
                                    f"{annotated}"
                                )
                elif cls == "ub":
                    ok = rc == 0
                    if not ok:
                        details.append(
                            "marked `// compiles; UB at runtime` but the block "
                            "fails to compile"
                        )
                else:  # wrong-unclassified
                    ok = False
                    outcome = "fails to compile" if rc not in (0, None) else "compiles"
                    details.append(
                        f"Wrong block not classified ({outcome}): annotate it "
                        "with `// compile-error` (must fail near the marker) or "
                        "`// compiles; UB at runtime` (must compile; inventoried)"
                    )
                if rc is None:
                    details.append("g++ timed out")
                if not ok and errors:
                    for d in errors[:3]:
                        details.append(fmt_diag(d, doc.name))
                rows.append(("ok" if ok else "VIOLATION", doc, fence, cls, hint, details))

    ub_inventory = [r for r in rows if r[3] == "ub"]
    violations = [r for r in rows if r[0] != "ok"]
    for status, doc, fence, cls, hint, details in rows:
        hint_show = (hint[:57] + "...") if len(hint) > 60 else hint
        print(f"{status:<10} {doc.name}:{fence.marker_line:<5} [{cls}] {hint_show}")
        for d in details:
            print(f"           -> {d}")

    print()
    if ub_inventory:
        print("UB inventory (manual sanitizer spot-checks; compiles by design):")
        for _s, doc, fence, _c, hint, _d in ub_inventory:
            print(f"  - {doc.name}:{fence.marker_line}  {hint[:70]}")
    counts = {}
    for _s, _doc, _f, cls, *_rest in rows:
        counts[cls] = counts.get(cls, 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(
        f"check_snippets: {len(rows)} cpp block(s) in {len(docs)} doc(s) "
        f"[{summary}]; {len(violations)} violation(s)"
    )
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
