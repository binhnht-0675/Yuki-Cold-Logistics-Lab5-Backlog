"""Backlog keys in issue bodies and documents -> issue references, one format everywhere (team review 21/10).

  outside full-width brackets: 「#123（E07-I05-S01）」
  inside 「（…）」 already:      「（#123 E07-I05-S01）」 / 「（API-006、#123 E07-I05-S01）」 — no nested brackets
With url_base (…/issues) the number becomes a Markdown link 「[#123](…/issues/123)」, for repository files
where GitHub does not autolink #123.

link_keys turns every key that has an issue number into a reference (other keys stay as they are); it first
undoes existing references, so applying it twice changes nothing. unlink_keys turns references back into bare
keys: update-body compares old and new bodies in that form, so a difference made only of references is not
mistaken for a hand edit. Key boundaries are ASCII only, so 「E07の」 is a key too.
"""
import re
from typing import Dict, Optional

KEY = r"E\d\d(?:-I\d\d(?:-S\d\d)?)?"
KEY_RX = re.compile(r"(?<![A-Za-z0-9_-])(" + KEY + r")(?![A-Za-z0-9_-])")
NUM = r"(?:\[#\d+\]\([^)\s]+\)|#\d+)"  # plain or Markdown-link issue number
REF_OUT_RX = re.compile(NUM + r"（(" + KEY + r")）")
REF_IN_RX = re.compile(NUM + r" (" + KEY + r")(?![A-Za-z0-9_-])")


def unlink_keys(text: str) -> str:
    return REF_IN_RX.sub(r"\1", REF_OUT_RX.sub(r"\1", text))


def _depth_before(text: str, pos: int) -> int:
    depth = 0
    for ch in text[:pos]:
        if ch == "（":
            depth += 1
        elif ch == "）" and depth:
            depth -= 1
    return depth


def link_keys(text: str, numbers: Dict[str, int], url_base: Optional[str] = None) -> str:
    plain = unlink_keys(text)

    def ref(m):
        key, n = m.group(1), numbers.get(m.group(1))
        if not n:
            return key
        num = f"[#{n}]({url_base}/{n})" if url_base else f"#{n}"
        return f"{num} {key}" if _depth_before(plain, m.start()) else f"{num}（{key}）"
    return KEY_RX.sub(ref, plain)
