"""Content guard for what this skill writes out (JA HTML and 照合表), via ../_shared/content_guard.py.

Both files go to a public repository, so before writing them every text a reader can see (body text,
link targets, the embedded provenance JSON, the whole 照合表) is scanned with the same rules as the
GitHub writers (Vietnamese, control chars, internal paths, secrets, emails, internal terms, internal
URLs / company names, GitHub URLs to other repositories). Only `--repo` (or, without it, the one
repository of the payload's issueRefs) may appear as a GitHub URL.
"""
from __future__ import annotations

import html
import os
import re
import shlex
from typing import List, Optional

from content_guard import report, scan_entries

PATH_OPTIONS = ("--html", "--ja", "--out", "--verification-md", "--translations")


def allowed_repo(payload: dict, repo: Optional[str]) -> Optional[str]:
    if repo:
        return repo
    repos = {i["issueRef"].rsplit("#", 1)[0].lower() for i in payload.get("issues", []) if "#" in i["issueRef"]}
    return repos.pop() if len(repos) == 1 else None


def html_entries(doc: str):
    body = re.sub(r"<style\b.*?</style>", " ", doc, flags=re.S | re.I)
    embedded = " ".join(re.findall(r"<script\b[^>]*>(.*?)</script>", body, flags=re.S | re.I))
    body = re.sub(r"<script\b.*?</script>", " ", body, flags=re.S | re.I)
    links = "\n".join(html.unescape(h) for h in re.findall(r'\b(?:href|src)="([^"]*)"', body, flags=re.I))
    return [("日本語版 HTML", "本文", html.unescape(re.sub(r"<[^>]+>", " ", body))),
            ("日本語版 HTML", "リンク", links), ("日本語版 HTML", "埋め込みデータ", embedded)]


def findings(entries, allow: Optional[str]) -> List[str]:
    """BLOCKED lines + the summary line of content_guard.report (empty when clean)."""
    lines: List[str] = []
    found = scan_entries(entries, allow)
    if found:
        report(found, lines.append)
    return [s for s in lines if s.startswith(("BLOCKED", "内容検査", "…"))]


def command_line(argv) -> str:
    """Recorded command: every file argument is reduced to its file name (no work-folder or machine paths)."""
    shown, prev = [], ""
    for a in argv:
        opt, eq, val = a.partition("=")
        if eq and opt in PATH_OPTIONS:
            a = f"{opt}={os.path.basename(val)}"
        elif prev in PATH_OPTIONS or os.path.isabs(a):
            a = os.path.basename(a)
        shown.append(a)
        prev = a if a.startswith("--") else ""
    return "python3 scripts/render-estimate-report-ja.py " + " ".join(shlex.quote(a) for a in shown)
