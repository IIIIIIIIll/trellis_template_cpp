#!/usr/bin/env python3
"""check_snippets.py — compile gate over fenced ```cpp guideline examples.

For every fenced ```cpp block (with its doc, line, and preceding lead hint)
the harness prepends tools/stubs/stubs.hpp plus a #line directive and runs
`g++ -Wall -Wextra -fsyntax-only` on the combined source (baseline dialect
`-std=c++14`; fences annotated `// C++17` compile with `-std=c++17` and
`// C++20` with `-std=c++20`), so
diagnostics carry the guideline's own doc:line coordinates. A per-doc stub
file (tools/stubs/per-doc/<doc>.hpp) may append names one guide spells
differently, and -isystem exposes tools/stubs/include for stub headers the
examples reference (tl/expected.hpp, result.h).

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
STUBS_INC = STUBS.resolve().parent / "include"
PER_DOC_STUBS = STUBS.resolve().parent / "per-doc"

CXX = "g++"
# Baseline dialect is C++14; `// C++17` / `// C++20` comments in a fence
# upgrade that block to -std=c++17 / -std=c++20 (see rules_grammar
# MARKER_CXX17_RE / MARKER_CXX20_RE).
ISYSTEM = ["-isystem", str(STUBS_INC)]
CXX14_FLAGS = ["-std=c++14", "-Wall", "-Wextra", *ISYSTEM, "-fsyntax-only"]
CXX17_FLAGS = ["-std=c++17", "-Wall", "-Wextra", *ISYSTEM, "-fsyntax-only"]
CXX20_FLAGS = ["-std=c++20", "-Wall", "-Wextra", *ISYSTEM, "-fsyntax-only"]


def flags_for(fence: rg.Fence) -> list:
    """Compiler flags for one fence: `// C++20` wins, then `// C++17`, else
    the C++14 baseline."""
    if fence.cxx20:
        return CXX20_FLAGS
    if fence.cxx17:
        return CXX17_FLAGS
    return CXX14_FLAGS


PROXIMITY = 2  # primary diagnostic may drift this many lines from the marker
DIAG_RE = re.compile(
    r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+"
    r"(?P<kind>fatal error|error|warning|note):\s+(?P<msg>.*)$",
    re.MULTILINE,
)
# Messages that mean "the block is a statement fragment compiled at namespace
# scope", not a defect in the example itself. When every error of the plain
# compile looks like this, the block is retried wrapped in a function body.
FRAGMENT_MSG_RE = re.compile(
    r"expected (?:unqualified-id|declaration|constructor, destructor, or type "
    r"conversion|primary-expression|nested-name-specifier|initializer) before"
    r"|expected '}'"
)
STATEMENT_START_RE = re.compile(
    r"^(?:try|if|while|for|do|return|switch|else|throw|break|continue|"
    r"delete\b|co_(?:await|yield|return)\b|assert\s*\()"
)
# A bare call statement (`install(HttpHandler{});`) is only legal inside a
# function body; a section opening with declaration keywords may still hold
# one within its first few significant lines (mixed decl+call example).
CALL_STMT_RE = re.compile(
    r"^[A-Za-z_]\w*(?:\s*(?:\.|->|::)\s*\w+)*\s*\(.*\)\s*;(\s*//.*)?$"
)
# A function definition (`Logger& logger() {`) needs namespace scope; a line
# with a control keyword still wins because `if (...) {` shares the shape.
FUNC_DEF_RE = re.compile(
    r"^[A-Za-z_][\w:&*<>,\s]*\([^;{}]*\)\s*(?:const\s*)?(?:noexcept\s*)?"
    r"(?:->\s*[\w:<>&*]+\s*)?\{"
)
TYPE_KEYWORD_RE = re.compile(
    r"^(?:void|bool|char|short|int|long|float|double|signed|unsigned|"
    r"size_t|ssize_t|auto|const|constexpr|consteval|constinit|static|"
    r"inline|extern|struct|class|union|enum|template|using|namespace|"
    r"typedef|typename|mutable|virtual|explicit|operator|friend)\b"
)


def default_docs():
    return sorted(DEFAULT_DIR.rglob("*.md"))


def stubs_for(path: Path, base_stubs: str) -> str:
    """Base prelude plus the doc-specific stub file when one exists.

    Most invented names live in the shared header; a per-doc file resolves
    names a single guide spells differently from the rest (e.g. a concrete
    `Result` where every other guide uses the templated alias).
    """
    per_doc = PER_DOC_STUBS / (path.stem + ".hpp")
    if per_doc.is_file():
        return base_stubs + per_doc.read_text(encoding="utf-8")
    return base_stubs

def marker_sections(fence: rg.Fence):
    """Split a fence carrying both Wrong and Right markers into sections.

    Returns None for fences without both markers (compile as one unit). For
    combined fences the wrong and right halves usually (re)define the same
    example types, so each section is wrapped in its own namespace and the
    halves never see each other. Content before the first marker compiles at
    namespace scope untouched.
    """
    if not (fence.wrong_count and fence.right_count):
        return None
    marks = []  # (index into content, "wrong"|"right")
    for k, cl in enumerate(fence.content):
        w = rg.MARKER_WRONG_RE.search(cl)
        r = rg.MARKER_RIGHT_RE.search(cl)
        if w or r:
            marks.append((k, "wrong" if w else "right"))
    if len(marks) < 2:
        return None
    prelude_probe = "\n".join(fence.content[: marks[0][0]])
    prelude_probe = re.sub(r"//.*", "", prelude_probe)
    if prelude_probe.count("{") != prelude_probe.count("}"):
        # markers sit inside an unfinished construct (e.g. inline comments in a
        # class body): the halves cannot be separated, compile as one unit and
        # let the fragment retries place trailing statements.
        return None
    sections = []
    prelude = fence.content[: marks[0][0]]
    for i, (start, kind) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(fence.content)
        sections.append((kind, start, fence.content[start:end]))
    return prelude, sections


def split_directive_prefix(lines):
    """Split a section into (global prefix, wrapped remainder).

    Preprocessor directives are position-sensitive: inside a namespace the
    included header's contents would land in that namespace, so a section that
    opens with comments and/or directives keeps those lines at namespace
    scope. A directive buried after real code forces the whole section to
    namespace scope as a fallback.
    """
    prefix = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("//") or s.startswith("/*") or s.startswith("#"):
            prefix.append(ln)
            continue
        break
    rest = lines[len(prefix) :]
    if any(ln.lstrip().startswith("#") for ln in rest):
        return lines, []
    return prefix, rest


def is_statement_section(lines) -> bool:
    """True when the section holds bare statements and must go inside a
    function body: it opens with a statement keyword or a bare call statement
    appears within its first three significant lines."""
    significant = 0
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("//") or s.startswith("#") or s.startswith("/*"):
            continue
        if STATEMENT_START_RE.match(s) or (
            significant < 3 and CALL_STMT_RE.match(s) and not TYPE_KEYWORD_RE.match(s)
        ):
            return True
        if FUNC_DEF_RE.match(s):
            return False  # function definitions need namespace scope
        significant += 1
        if significant >= 3:
            break
    return False


def build_source(stubs: str, doc: rg.ParsedDoc, fence: rg.Fence, wrapped: bool):
    """Render the translation unit for one fence.

    wrapped=False: stubs, #line anchor, block as-is (combined fences: per-marker
    namespaces). wrapped=True: the block goes inside `void snippet() { ... }`
    so statement fragments compile; only used when the plain attempt failed.
    """
    first = fence.content_first_line
    body = "\n".join(fence.content)
    sections = marker_sections(fence)
    if sections is None:
        if not wrapped:
            return f'{stubs}#line {first} "{doc.name}"\n{body}\n'
        return (
            f'{stubs}#line {first - 1} "{doc.name}"\n'
            f"auto snippet() {{\n{body}\n}}\n"
        )
    prelude, secs = sections
    parts = [stubs, f'#line {first} "{doc.name}"\n']
    if prelude:
        parts.append("\n".join(prelude) + "\n")
    for kind, start, lines in secs:
        doc_line = first + start
        if is_statement_section(lines):
            # statement section: a namespace cannot hold bare statements
            parts.append(
                f'namespace snippet_{kind} {{\n#line {doc_line - 1} "{doc.name}"\n'
                f"auto snippet_fn() {{\n" + "\n".join(lines) + "\n}\n}\n"
            )
            continue
        prefix, rest = split_directive_prefix(lines)
        if prefix:
            parts.append(f'#line {doc_line} "{doc.name}"\n')
            parts.append("\n".join(prefix) + "\n")
        if rest:
            head, tail = split_tail_statements(rest)
            parts.append(
                f'namespace snippet_{kind} {{\n#line {doc_line + len(prefix)} '
                f'"{doc.name}"\n'
            )
            if head:
                parts.append("\n".join(head) + "\n")
            if tail:
                parts.append(
                    f'#line {doc_line + len(prefix) + len(head) - 1} "{doc.name}"\n'
                )
                parts.append("static auto snippet_tail() {\n" + "\n".join(tail) + "\n}\n")
            parts.append("}\n")
    return "".join(parts)


def split_tail_statements(content, through_braces=False):
    """Split a block into (head declarations, tail statement lines).

    Walking back from the end, lines that are comments/blanks or bare
    statements (calls, control keywords) form the tail; the first declaration
    line stops the walk. Used for blocks like `template ... ; usage-call;`
    where the declaration part cannot go inside a function body (templates are
    block-scope-illegal) but the trailing call must.
    """
    tail = []
    i = len(content)
    while i > 0:
        s = content[i - 1].strip()
        if not s or s.startswith("//") or s.startswith("/*") or s.startswith("*"):
            tail.insert(0, content[i - 1])
            i -= 1
            continue
        if through_braces and s.startswith("}") and not s.startswith("};"):
            # a closing brace continues an if/for/try block opened above it;
            # when it actually closes a function definition the walk stops on
            # the definition line and this tail attempt simply fails to compile
            tail.insert(0, content[i - 1])
            i -= 1
            continue
        if STATEMENT_START_RE.match(s) or (
            CALL_STMT_RE.match(s) and not TYPE_KEYWORD_RE.match(s)
        ):
            tail.insert(0, content[i - 1])
            i -= 1
            continue
        break
    return content[:i], tail


def build_tail_source(stubs: str, doc: rg.ParsedDoc, fence: rg.Fence):
    """Namespace-wrapped block with its trailing statements inside a function.

    Returns None when the block ends in a declaration (nothing to move into a
    function body; the plain and function-wrapped attempts cover it).
    """
    head, tail = split_tail_statements(fence.content, through_braces=True)
    if not tail:
        return None
    first = fence.content_first_line
    prefix, rest = split_directive_prefix(head)
    parts = [stubs, f'#line {first} "{doc.name}"\n']
    if prefix:
        parts.append("\n".join(prefix) + "\n")
    parts.append("namespace snippet {\n")
    if rest:
        parts.append(f'#line {first + len(prefix)} "{doc.name}"\n')
        parts.append("\n".join(rest) + "\n")
    tail_doc = first + len(head)
    parts.append(f'#line {tail_doc - 1} "{doc.name}"\n')
    parts.append("static auto snippet_tail() {\n" + "\n".join(tail) + "\n}\n}\n")
    return "".join(parts)


def compile_once(flags, source: str, tmpdir: Path):
    src = tmpdir / "block.cpp"
    src.write_text(source, encoding="utf-8")
    try:
        proc = subprocess.run(
            [CXX, *flags, str(src)],
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
    """Compile stubs + #line-anchored block; return (rc, diagnostics list).

    Plain attempt first. Statement fragments get two retries: declarations at
    namespace scope with trailing statements in a function body (the template
    usage shape), then the whole block in a function body. When every attempt
    fails, report the first whose errors are not fragment artifacts.
    """
    flags = flags_for(fence)
    sectioned = marker_sections(fence) is not None
    rc, diags = compile_once(flags, build_source(stubs, doc, fence, False), tmpdir)
    if rc == 0 or rc is None or sectioned:
        if sectioned and fence.compile_error_lines:
            # A `// compile-error` contract is judged on the block as the doc
            # reader sees it — one unit. Namespace sectioning is harness
            # bookkeeping and can legalize namespace-scope-only defects (e.g.
            # `void main();` is ordinary snippet_wrong::main inside a
            # namespace), so re-compile un-sectioned for the verdict.
            plain = (
                f'{stubs}#line {fence.content_first_line} "{doc.name}"\n'
                + "\n".join(fence.content)
                + "\n"
            )
            prc, pdiags = compile_once(flags, plain, tmpdir)
            return prc, pdiags
        return rc, diags
    retries = []
    tail_src = build_tail_source(stubs, doc, fence)
    if tail_src:
        retries.append(compile_once(flags, tail_src, tmpdir))
    retries.append(compile_once(flags, build_source(stubs, doc, fence, True), tmpdir))
    for wrc, wdiags in retries:
        if wrc == 0:
            # A fragment wrap can legalize namespace-scope-only defects
            # (`void main();` is valid as a local declaration). That rescue is
            # for fragments, never for `// compile-error` blocks: their
            # contract is judged on the block as the doc reader sees it.
            if not fence.compile_error_lines:
                return 0, []
            break
    for crc, cdiags in [(rc, diags)] + retries:
        errs = [d for d in cdiags if d["kind"] in ("error", "fatal error")]
        if errs and not all(FRAGMENT_MSG_RE.search(d["msg"]) for d in errs):
            return crc, cdiags
    return retries[-1]


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
                docs.extend(sorted(p.rglob("*.md")))
            else:
                docs.append(p)
    else:
        docs = default_docs()
    if not docs:
        print("error: no markdown docs to check", file=sys.stderr)
        return 2

    base_stubs = STUBS.read_text(encoding="utf-8")
    if not base_stubs.endswith("\n"):
        base_stubs += "\n"

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
            stubs = stubs_for(path, base_stubs)
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
