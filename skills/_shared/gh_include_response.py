"""Parse what `gh api --include` prints: status line + response headers, a blank line, then the body.

gh writes `HTTP/x <status>` and `Name: value` lines (CRLF), then an empty line, then the body, on stdout
for every response (also for HTTP errors, where the error message goes to stderr). Header lines never
contain an empty line, so the first empty line ends the headers; the body is returned untouched.
Output that does not start with a status line (e.g. a test double without headers) is all body.
"""
from __future__ import annotations

import json
import re
from typing import Tuple

STATUS_LINE_RX = re.compile(r"HTTP/\d")
BLANK_LINE_RX = re.compile(r"\r?\n\r?\n")


def split_include(out: str) -> Tuple[str, str]:
    """-> (headers text, body). Only the leading header block is split off."""
    if not out or not STATUS_LINE_RX.match(out):
        return "", out or ""
    m = BLANK_LINE_RX.search(out)
    if not m:  # headers only (e.g. HTTP 204 without the trailing blank line)
        return out, ""
    return out[:m.start()], out[m.end():]


def body_errors(out: str) -> str:
    """Error text inside a JSON response body (GraphQL `errors`, REST `message`); '' otherwise."""
    try:
        data = json.loads(out) if out and out.lstrip()[:1] == "{" else None
    except ValueError:
        return ""
    if not isinstance(data, dict):
        return ""
    parts = [f"{e.get('type', '')} {e.get('message', '')}" for e in data.get("errors") or [] if isinstance(e, dict)]
    if isinstance(data.get("message"), str):
        parts.append(data["message"])
    return "; ".join(parts)
