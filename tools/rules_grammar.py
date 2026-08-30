#!/usr/bin/env python3
"""Shared parser for the cpp guideline rule-block grammar.

Normative grammar: task 08-30-cpp-rules-machine-format, design.md, sections
"Rule-block grammar" and "Grammar details"; the authoring contract documents
the same rules for authors (.trellis/spec/registry/guideline-authoring.md).

Imported by validate_rules.py, extract_rules.py, and check_snippets.py.
Python 3 standard library only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- ID allocation (design.md "ID allocation") ------------------------------

PREFIX_ALLOCATION = {
    "memory-and-ownership": "MEM",
    "error-handling": "ERR",
    "quality-guidelines": "QUAL",
    "testing-conventions": "TEST",
    "functions-and-interfaces": "FN",
    "classes-and-hierarchies": "CLS",
    "templates-and-generics": "TPL",
    "concurrency": "CONC",
    "expressions-and-flow": "EXPR",
    "performance": "PERF",
}
PREFIXES = frozenset(PREFIX_ALLOCATION.values())
DOC_PREFIX = {name + ".md": prefix for name, prefix in PREFIX_ALLOCATION.items()}

# Validator scope (design.md "Grammar details"): the rule grammar binds the 10
# topic guides. index.md and the disposition doc carry stances, not rules, and
# are exempt from rule checks; the footer and link contracts still bind them.
EXEMPT_DOCS = frozenset({"index.md", "core-guidelines-disposition.md"})

STRENGTHS = ("hard", "default")

# --- Fixed contract strings -------------------------------------------------

LANG_LINE = "**Language**: All documentation should be written in **English**."
ATTRIB_LINE = (
    "> Aligned with the [ISO C++ Core Guidelines]"
    "(https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) "
    "© Standard C++ Foundation and its contributors. Rule IDs cited for "
    "cross-reference; original internal digest (internal business use)."
)
NO_DETECTOR_TEXT = "review — no automated detector."
NO_DETECTOR_RE = re.compile(
    r"^review\s*[—–-]\s*no automated detector\.?$", re.IGNORECASE
)

# Section-stated strength default: standalone line, exact spelling.
SECTION_DEFAULT_RE = re.compile(r"^Default strength: (hard|default)\.$")
CAUGHT_BY_RE = re.compile(r"^Caught by:\s*(.+?)\s*$")
# Prose example lead lines: Wrong / Wrong: / **Wrong** / **Wrong:** (and Right).
WRONG_RIGHT_LEAD_RE = re.compile(r"^(?:\*\*)?(Wrong|Right)(?:\*\*)?:?$")
FENCE_OPEN_RE = re.compile(r"^```(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
HR_RE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
TABLE_ROW_RE = re.compile(r"^\s*\|")
MARKER_WRONG_RE = re.compile(r"//\s*Wrong\b")
MARKER_RIGHT_RE = re.compile(r"//\s*Right\b")
MARKER_UB_RE = re.compile(r"//\s*compiles;\s*UB\b")
MARKER_COMPILE_ERROR_RE = re.compile(r"//\s*compile-error\b")

# Bold rule-ID token, anywhere on a line.
BOLD_ID_RE = re.compile(r"\*\*(?P<id>[A-Z]{2,4}-\d+)(?P<tail>[^*]*)\*\*")
# Prose lead-in: paragraph start or directly after "- " (design.md list-item form).
LEAD_RE = re.compile(r"^\*\*(?P<id>[A-Z]{2,4}-\d+)(?P<tail>[^*]*)\*\*(?P<rest>.*)$")
# Table-cell lead-in: first cell begins with the token; trailing dot optional.
CELL_RE = re.compile(
    r"^\*\*(?P<id>[A-Z]{2,4}-\d+)(?P<tail>(?:\s*\([^)]*\))?\.?)\*\*(?P<rest>.*)$"
)
CELL_ID_START_RE = re.compile(r"^\*\*[A-Z]{2,4}-\d+")

# Core Guidelines IDs cited as cross-reference anchors: F.21, ES.20, Con.1,
# Enum.5, FAQ.8 ... Never matches local AREA-n IDs (hyphen spelling).
UPSTREAM_RE = re.compile(
    r"(?<![\w#/.])([A-Z][a-zA-Z]{0,2}\.\d+(?:\.\d+)?)(?!\w)(?!\.\d)"
)
URL_RE = re.compile(r"https?://\S+")
MD_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
INLINE_CODE_RE = re.compile(r"`([^`]*)`")

SENT_END_RE = re.compile(r"[.!?](?=\s|$)")
WORD_TAIL_RE = re.compile(r"[\w.]*$")
_ABBREV = {
    "e.g", "i.e", "etc", "vs", "cf", "approx", "resp", "viz", "cf.", "no.",
}


# --- Data model --------------------------------------------------------------


@dataclass
class Fence:
    marker_line: int  # 1-based line of the opening fence marker
    lang: str
    content: list = field(default_factory=list)  # fence body lines
    wrong_count: int = 0
    right_count: int = 0
    ub: bool = False
    compile_error_lines: list = field(default_factory=list)  # 1-based doc lines

    @property
    def content_first_line(self) -> int:
        return self.marker_line + 1

    @property
    def close_line(self) -> int:
        return self.marker_line + 1 + len(self.content)


@dataclass
class Rule:
    id: str
    prefix: str
    num: int
    line: int  # 1-based lead-in / table-row line
    kind: str  # "prose" | "table"
    marker: str | None  # "hard" | "default" | None (section default may apply)
    strength_error: str | None  # set when the marker exists but is invalid
    statement: str  # raw markdown of the first paragraph / remaining cells
    caught_own: tuple | None  # (line, text) when the rule carries its own
    block_end: int  # last line (inclusive) of the rule block
    cells: list | None  # table rows only


@dataclass
class Group:
    start: int
    end: int
    wrong_count: int = 0
    right_count: int = 0
    fences: list = field(default_factory=list)
    leads: list = field(default_factory=list)  # (line, "Wrong"|"Right")


@dataclass
class ParsedDoc:
    name: str
    path: str
    lines: list
    masked: list  # per line: True inside a fence (body or closing marker)
    fences: list
    headings: list  # (line, level, title)
    caught_by: list  # (line, text) outside fences
    section_defaults: list  # (line, "hard"|"default")
    prose_rules: list
    table_rules: list
    groups: list
    grammar_violations: list  # (line, code, message)

    @property
    def rules(self):
        return self.prose_rules + self.table_rules


# --- Parsing -----------------------------------------------------------------


def _tail_marker_prose(tail):
    """Return (marker, violation) for a prose lead-in tail."""
    if tail == ".":
        return None, None
    m = re.fullmatch(r" \(([a-z]+)\)\.", tail)
    if m:
        if m.group(1) in STRENGTHS:
            return m.group(1), None
        return None, (
            "E-STRENGTH-VOCAB",
            f"strength `({m.group(1)})` is outside the closed vocabulary "
            f"{'|'.join(STRENGTHS)}",
        )
    return None, (
        "E-LEAD-MALFORMED",
        f"lead-in tail `{tail}` does not match the grammar "
        "`**<AREA>-<n> (hard|default).**`",
    )


def _tail_marker_cell(tail):
    """Return (marker, violation) for a table-cell lead-in tail."""
    if tail in ("", "."):
        return None, None
    m = re.fullmatch(r" \(([a-z]+)\)\.?", tail)
    if m:
        if m.group(1) in STRENGTHS:
            return m.group(1), None
        return None, (
            "E-STRENGTH-VOCAB",
            f"cell strength `({m.group(1)})` is outside the closed vocabulary "
            f"{'|'.join(STRENGTHS)}",
        )
    return None, (
        "E-LEAD-MALFORMED",
        f"cell tail `{tail}` does not match `**<ID>**` optionally followed by "
        "`(hard)` or `(default)`",
    )


def parse(text: str, name: str, path: str) -> ParsedDoc:
    lines = [ln.rstrip("\r") for ln in text.split("\n")]
    n = len(lines)
    masked = [False] * n
    fences = []
    fence_at = {}

    i = 0
    while i < n:
        m = FENCE_OPEN_RE.match(lines[i].lstrip())
        if not m:
            i += 1
            continue
        lang = m.group(1).strip()
        j = i + 1
        while j < n and not lines[j].lstrip().startswith("```"):
            masked[j] = True
            j += 1
        if j < n:
            masked[j] = True  # closing marker
        content = lines[i + 1 : j if j < n else n]
        f = Fence(marker_line=i + 1, lang=lang, content=content)
        for k, cl in enumerate(content):
            if MARKER_WRONG_RE.search(cl):
                f.wrong_count += 1
            if MARKER_RIGHT_RE.search(cl):
                f.right_count += 1
            if MARKER_UB_RE.search(cl):
                f.ub = True
            if MARKER_COMPILE_ERROR_RE.search(cl):
                f.compile_error_lines.append(i + 1 + 1 + k)
        fences.append(f)
        fence_at[i + 1] = f
        i = (j + 1) if j < n else n

    doc = ParsedDoc(
        name=name,
        path=path,
        lines=lines,
        masked=masked,
        fences=fences,
        headings=[],
        caught_by=[],
        section_defaults=[],
        prose_rules=[],
        table_rules=[],
        groups=[],
        grammar_violations=[],
    )

    group = None
    hr_lines = []
    table_row_lines = []

    def flush():
        nonlocal group
        if group is not None:
            doc.groups.append(group)
            group = None

    for idx in range(n):
        if masked[idx]:
            continue
        stripped = lines[idx].strip()
        lineno = idx + 1

        if stripped.startswith("```"):  # opening marker (closers are masked)
            f = fence_at[lineno]
            if group is None:
                group = Group(start=lineno, end=lineno)
            group.fences.append(f)
            group.wrong_count += f.wrong_count
            group.right_count += f.right_count
            group.end = lineno
            continue
        if not stripped:
            continue  # blank lines never end an example group
        wm = WRONG_RIGHT_LEAD_RE.match(stripped)
        if wm:
            if group is None:
                group = Group(start=lineno, end=lineno)
            group.leads.append((lineno, wm.group(1)))
            if wm.group(1) == "Wrong":
                group.wrong_count += 1
            else:
                group.right_count += 1
            group.end = lineno
            continue

        # Any other content line ends the current example group.
        flush()

        hm = HEADING_RE.match(stripped)
        if hm:
            doc.headings.append((lineno, len(hm.group(1)), hm.group(2)))
            continue
        if HR_RE.match(stripped):
            hr_lines.append(lineno)
            continue
        if TABLE_ROW_RE.match(stripped):
            table_row_lines.append(lineno)
            _parse_table_row(doc, stripped, lineno)
            continue
        cm = CAUGHT_BY_RE.match(stripped)
        if cm:
            doc.caught_by.append((lineno, cm.group(1)))
            continue
        sm = SECTION_DEFAULT_RE.match(stripped)
        if sm:
            doc.section_defaults.append((lineno, sm.group(1)))
            continue
        _scan_prose_line(doc, stripped, lineno)

    flush()

    # Rule block extents and own-detector attachment for prose rules.
    boundaries = sorted(
        {h[0] for h in doc.headings}
        | set(hr_lines)
        | set(table_row_lines)
        | {r.line for r in doc.rules}
    )
    for rule in doc.prose_rules:
        nxt = next((b for b in boundaries if b > rule.line), n + 1)
        rule.block_end = nxt - 1
        own = [c for c in doc.caught_by if rule.line < c[0] <= rule.block_end]
        if own:
            rule.caught_own = own[0]
    for rule in doc.table_rules:
        rule.block_end = rule.line
    return doc


def _parse_table_row(doc: ParsedDoc, stripped: str, lineno: int):
    cells = [c.strip() for c in stripped.split("|")]
    # split produces an empty head for a leading '|' and empty tail for trailing
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    if len(cells) < 2:
        return
    first = cells[0]
    if not CELL_ID_START_RE.match(first):
        return
    m = CELL_RE.match(first)
    if not m:
        doc.grammar_violations.append(
            (
                lineno,
                "E-LEAD-MALFORMED",
                f"table-cell lead-in `{first}` does not match `**<ID>**` "
                "optionally followed by `(hard)`/`(default)`",
            )
        )
        return
    rid = m.group("id")
    prefix = rid.split("-")[0]
    if prefix not in PREFIXES:
        return  # not a rule token
    marker, violation = _tail_marker_cell(m.group("tail"))
    if violation:
        doc.grammar_violations.append((lineno, violation[0], violation[1]))
    row_caught = None
    for cell in cells[1:]:
        cpos = cell.find("Caught by:")
        if cpos >= 0:
            row_caught = (lineno, cell[cpos + len("Caught by:"):].strip())
            break
    doc.table_rules.append(
        Rule(
            id=rid,
            prefix=prefix,
            num=int(rid.split("-")[1]),
            line=lineno,
            kind="table",
            marker=marker,
            strength_error="vocab" if violation and violation[0] == "E-STRENGTH-VOCAB" else None,
            statement="; ".join(c for c in cells[1:] if c),
            caught_own=row_caught,
            block_end=lineno,
            cells=cells,
        )
    )


def _scan_prose_line(doc: ParsedDoc, stripped: str, lineno: int):
    bullet = stripped.startswith("- ")
    offset = 2 if bullet else 0
    for m in BOLD_ID_RE.finditer(stripped):
        if m.start() != offset:
            doc.grammar_violations.append(
                (
                    lineno,
                    "E-ID-MISPLACED",
                    f"bold rule-ID token `{m.group('id')}` outside a lead-in "
                    "position (paragraph start or `- ` bullet); cite rule IDs "
                    "unbolded, or open a rule block",
                )
            )
            continue
        rid = m.group("id")
        prefix = rid.split("-")[0]
        if prefix not in PREFIXES:
            continue  # not a rule token
        marker, violation = _tail_marker_prose(m.group("tail"))
        if violation:
            doc.grammar_violations.append((lineno, violation[0], violation[1]))
            if violation[0] == "E-LEAD-MALFORMED":
                continue
        rest = stripped[m.end():].strip()
        parts = [rest]
        j = idx_of = lineno - 1
        j = idx_of + 1
        while j < len(doc.lines):
            if doc.masked[j]:
                break
            s = doc.lines[j].strip()
            if not s:
                break
            if (
                s.startswith("```")
                or s.startswith("#")
                or s.startswith("|")
                or HR_RE.match(s)
                or WRONG_RIGHT_LEAD_RE.match(s)
                or CAUGHT_BY_RE.match(s)
                or SECTION_DEFAULT_RE.match(s)
                or s.startswith("- **")
                or BOLD_ID_RE.match(s)
            ):
                break
            parts.append(s)
            j += 1
        doc.prose_rules.append(
            Rule(
                id=rid,
                prefix=prefix,
                num=int(rid.split("-")[1]),
                line=lineno,
                kind="prose",
                marker=marker,
                strength_error="vocab" if violation and violation[0] == "E-STRENGTH-VOCAB" else None,
                statement=" ".join(p for p in parts if p),
                caught_own=None,
                block_end=lineno,
                cells=None,
            )
        )


# --- Resolution helpers (shared by validator and extractor) ------------------


def scope_start(doc: ParsedDoc, line: int) -> int:
    """Line of the nearest preceding level-<=2 heading (section boundary)."""
    best = 0
    for hl, level, _title in doc.headings:
        if hl < line and level <= 2 and hl > best:
            best = hl
    return best


def resolve_strength(rule: Rule, doc: ParsedDoc):
    """Return (strength, None) or (None, reason)."""
    if rule.marker:
        return rule.marker, None
    if rule.strength_error:
        return None, "strength marker present but invalid (reported separately)"
    lo = scope_start(doc, rule.line)
    cands = [d for d in doc.section_defaults if lo < d[0] < rule.line]
    if cands:
        return max(cands, key=lambda d: d[0])[1], None
    return None, (
        "no (hard|default) marker and no preceding `Default strength: hard.` / "
        "`Default strength: default.` line in its section"
    )


def resolve_caught_by(rule: Rule, doc: ParsedDoc):
    """Return ((line, text), None) or (None, reason)."""
    if rule.caught_own:
        return rule.caught_own, None
    lo = scope_start(doc, rule.line)
    cands = [c for c in doc.caught_by if lo < c[0] < rule.line]
    if cands:
        return max(cands, key=lambda c: c[0]), None
    return None, (
        "no `Caught by:` line in the rule block and none to inherit in its "
        "section; state `Caught by: review — no automated detector.` explicitly"
    )


def normalize_detector(text: str) -> str:
    t = text.strip()
    if NO_DETECTOR_RE.match(t):
        return "review"
    return t[:-1].rstrip() if t.endswith(".") else t


def clean_statement(md: str) -> str:
    t = INLINE_CODE_RE.sub(lambda m: m.group(1), md)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = t.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", t).strip()


def first_sentence(text: str) -> str:
    for m in SENT_END_RE.finditer(text):
        head = text[: m.start()]
        tok = WORD_TAIL_RE.search(head).group(0)
        if tok.lower() in _ABBREV or (len(tok) == 1 and tok.isupper()):
            continue
        return text[: m.end()].strip()
    return text.strip()


def upstream_ids(block_text: str) -> list:
    t = URL_RE.sub(" ", block_text)
    seen = []
    for m in UPSTREAM_RE.finditer(t):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def slugify(title: str) -> str:
    t = INLINE_CODE_RE.sub(lambda m: m.group(1), title)
    t = t.replace("**", "").replace("`", "").strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return re.sub(r"\s+", "-", t.strip())
