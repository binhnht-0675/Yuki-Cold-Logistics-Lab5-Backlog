"""Content guard: check EVERY string a command would send to GitHub before the first write.

Callers collect (key, field, text) for issue titles / bodies, comments, label names and text
field values, call `scan_entries`, and on any finding print `report(...)` and exit
EXIT_CONTENT_BLOCKED (3) without writing anything (no half-written runs).

Categories: 1 vi (Vietnamese letters) · 2 ctrl (control / format / invisible chars except \\n \\t) ·
3 path (internal paths) · 4 secret (key patterns, DB URL with user:pass@, password values) · 5 email
(except noreply / example domains) · 6 term (internal terms) · 7 internal (Drive / company-login URLs,
company names, GitHub URLs to repos other than the allowed one, with or without https://).
Each line is checked on its NFKC view with the invisible characters removed (full-width letters,
soft hyphens, tag characters ... cannot hide a match); `ctrl` is checked on the original line and
reported positions are columns of the original line.
For a GitHub URL to an allowed repo (`--repo`, compared case-insensitively) only the
`https://github.com/<owner>/<repo>` part is exempt; the path / query after it is still scanned, both as
written and percent-decoded (all layers), and a `/..` that climbs out of the repo is blocked.
`github.com/users|orgs/<owner>/projects/N` is allowed for the owner of an allowed repo.
A bare allowed `owner/name` token (not inside a URL) is exempt too.
Secrets, emails and internal URLs are never echoed (rule + length only).
The patterns live in content_guard_rules.py (re-exported here).
"""
from __future__ import annotations

import re
import unicodedata
import urllib.parse
from collections import Counter
from typing import Callable, Iterable, List, NamedTuple, Optional, Sequence, Tuple, Union

from content_guard_rules import (  # noqa: F401  (public names kept for callers)
    CATEGORY_JA, CO1, CO2, COMPANY_RX, CTRL_RX, EMAIL_OK_RX, EMAIL_RX, GITHUB_URL_RX, INTERNAL_LINK_RX,
    KEY_RXS, MASKED, NO_SCHEME, PROJECT_OWNER_SEGMENTS, RULES, TRAVERSAL_RX, VI_RX)

EXIT_CONTENT_BLOCKED = 3
AllowRepo = Union[None, str, Sequence[str]]


class Finding(NamedTuple):
    key: str
    field: str
    category: str
    rule: str
    line: int
    col: int
    section: str
    excerpt: str


def normalized_view(line: str) -> Tuple[str, Optional[List[int]]]:
    """(NFKC view of `line` without invisible chars, view index -> original index or None if identical)."""
    if not CTRL_RX.search(line) and unicodedata.is_normalized("NFKC", line):
        return line, None
    out, idx, i, n = [], [], 0, len(line)
    while i < n:
        if CTRL_RX.match(line, i):
            i += 1
            continue
        j = i + 1  # a base char plus the combining marks after it is normalized together
        while j < n and unicodedata.combining(line[j]) and not CTRL_RX.match(line, j):
            j += 1
        piece = unicodedata.normalize("NFKC", line[i:j])
        out.append(piece)
        idx += [i] * len(piece)
        i = j
    return "".join(out), idx + [n]


def _excerpt(category: str, view: str, start: int, end: int, raw: str) -> str:
    if category in MASKED:
        return f"（非表示・長さ {end - start}）"
    if category == "ctrl":
        return "U+%04X" % ord(raw)
    return "「" + view[max(0, start - 8):min(len(view), end + 8)].replace("`", "'") + "」"


def _allowed(allow_repo: AllowRepo) -> Tuple[set, set]:
    repos = [allow_repo] if isinstance(allow_repo, str) else list(allow_repo or [])
    repos = {r.lower() for r in repos if r and "/" in r}
    return repos, {r.split("/", 1)[0] for r in repos}


def _fully_unquoted(text: str) -> str:
    """Percent-decode until stable (at most 4 layers, so %252f cannot hide a slash)."""
    for _ in range(4):
        decoded = urllib.parse.unquote(text)
        if decoded == text:
            break
        text = decoded
    return text


def _github_urls(view: str, repos: set, owners: set) -> Tuple[str, list, list]:
    """Blank the exempt part of allowed GitHub URLs.

    -> (cleaned view, [(start, label)] of other repos, [(start, decoded tail)] of allowed URLs whose tail
    changes when percent-decoded: the rules scan that decoded form too)."""
    clean, other, decoded = view, [], []
    for m in GITHUB_URL_RX.finditer(view):
        first, second = m.group(1).lower(), m.group(2).lower()
        ok = (first in PROJECT_OWNER_SEGMENTS and second in owners) or f"{first}/{second}" in repos
        raw = re.match(r"\S*", view[m.end():]).group(0)  # the rest of this URL
        tail = _fully_unquoted(raw)
        if ok and not TRAVERSAL_RX.search(tail.split("#", 1)[0].split("?", 1)[0]):
            clean = clean[:m.start()] + " " * (m.end() - m.start()) + clean[m.end():]
            if tail != raw:
                decoded.append((m.end(), normalized_view(tail)[0]))
        else:
            owner = m.group(2) if first in PROJECT_OWNER_SEGMENTS else m.group(1)
            other.append((m.start(), f"（{owner}/… 許可リポジトリ外）"))
    return clean, other, decoded


def _blank_repo_names(view: str, repos: set) -> str:
    """Blank a bare allowed `owner/name` token (e.g. a recorded `--repo` value): the repo is public by design, so its
    own name must not trip a term rule (the submission repo name itself contains a course term). Whole tokens only."""
    for repo in repos:
        rx = re.compile(r"(?<![\w./-])" + re.escape(repo) + r"(?![\w-])", re.I)
        view = rx.sub(lambda m: " " * len(m.group(0)), view)
    return view


def _first_hit(category: str, rx, targets):
    """(text, tail start or None, match) of the first match of `rx` over `targets`, or None."""
    for text, at in targets:
        for m in rx.finditer(text):
            if category == "email" and EMAIL_OK_RX.search(m.group(0)):
                continue
            return text, at, m
    return None


def scan_text(text: str, allow_repo: AllowRepo = None) -> List[Tuple[str, str, int, int, str, str]]:
    """-> [(category, rule, line_no, col, section, excerpt)], one per (rule, line).

    `allow_repo` is one `owner/name` or a list of them (compared case-insensitively)."""
    out, section = [], ""
    repos, owners = _allowed(allow_repo)
    for n, line in enumerate((text or "").split("\n"), 1):
        if line.startswith("## "):
            section = line[3:].strip()
        view, idx = normalized_view(line)
        col = (lambda p: p + 1) if idx is None else (lambda p: idx[p] + 1)
        clean, other, decoded = _github_urls(view, repos, owners)
        clean = _blank_repo_names(clean, repos)
        out += [("internal", "github-other-repo", n, col(s), section, label) for s, label in other]
        for category, rule, rx in RULES:
            if category == "ctrl":
                targets = [(line, None)]
            else:
                targets = [(clean, None)] + [(tail, at) for at, tail in decoded]
            hit = _first_hit(category, rx, targets)
            if hit:
                text, at, m = hit
                if at is None:
                    pos = m.start() + 1 if category == "ctrl" else col(m.start())
                    excerpt = _excerpt(category, view, m.start(), m.end(), m.group(0))
                else:  # found only in a percent-decoded URL tail: report the tail's column
                    pos = col(at)
                    excerpt = _excerpt(category, text, m.start(), m.end(), m.group(0))
                out.append((category, rule, n, pos, section, excerpt))
    return out


def scan_entries(entries: Iterable[Tuple[str, str, str]], allow_repo: AllowRepo = None) -> List[Finding]:
    found = []
    for key, field, text in entries:
        if isinstance(text, str) and text:
            found += [Finding(key or "-", field, *f) for f in scan_text(text, allow_repo)]
    return found


STOP_LINE = "公開リポジトリに出せない内容があるため、最初の書き込みの前に停止しました（GitHub への書き込み 0 件）。"


def report(findings: List[Finding], printer: Callable[[str], None] = print, limit: int = 200,
           closing: Optional[str] = None) -> None:
    """Print one line per finding, the per-category totals and `closing` (default: STOP_LINE)."""
    for f in findings[:limit]:
        where = f"行{f.line}:{f.col}" + (f" §{f.section}" if f.section else "")
        printer(f"BLOCKED [{CATEGORY_JA[f.category]}] {f.key} {f.field} {where} {f.rule} {f.excerpt}")
    if len(findings) > limit:
        printer(f"… 他 {len(findings) - limit} 件")
    by_cat = Counter(f.category for f in findings)
    printer("内容検査: " + " / ".join(f"{CATEGORY_JA[c]} {by_cat[c]}" for c in CATEGORY_JA if by_cat[c])
            + f"（計 {len(findings)} 件、対象キー {len({f.key for f in findings})} 件）")
    printer(STOP_LINE if closing is None else closing)


def guard(entries: Iterable[Tuple[str, str, str]], allow_repo: AllowRepo,
          printer: Callable[[str], None] = print) -> int:
    """0 when clean (prints one OK line), else prints the report and returns EXIT_CONTENT_BLOCKED."""
    entries = list(entries)
    findings = scan_entries(entries, allow_repo)
    if not findings:
        printer(f"内容検査: OK（{len(entries)} 件の文字列、7 分類すべて該当なし）")
        return 0
    report(findings, printer)
    return EXIT_CONTENT_BLOCKED
