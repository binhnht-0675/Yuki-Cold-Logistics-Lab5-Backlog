"""Backlog file model: load, validate, order (epic -> story -> task), render issue body (JA)."""
from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from key_map import KEY_CHARS, is_valid_key, marker
from key_refs import link_keys

LEVEL_RANK = {"epic": 0, "story": 1, "task": 2}
LEVEL_JA = {"epic": "エピック", "story": "ストーリー", "task": "タスク"}
SECTION_ORDER = ["概要", "対象FT", "参照", "規模の手がかり", "完了の定義", "依存", "備考"]
HEADINGS = {"対象FT": "対象機能（FT）", "参照": "参照（詳細設計）"}
MAX_CHILDREN = 100  # GitHub sub-issue limit per parent


@dataclass
class BodyContext:
    repo: str
    ref_style: str = "text"          # permalink | text
    ref: Optional[str] = None        # tag / commit for permalinks
    specs_root: str = ""             # path of the spec tree inside the repo
    edition: str = ""                # e.g. 「2026-10-12 提出版」 for text style
    numbers: Dict[str, int] = field(default_factory=dict)  # key -> issue number


def load_backlog(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["items"] if isinstance(data, dict) else data


def validate(items: List[dict]) -> List[str]:
    errors, keys = [], {}
    for i in items:
        k = i.get("key")
        if not k:
            errors.append("key がない項目があります")
            continue
        if not is_valid_key(k):  # the marker regex reads nothing else back -> re-runs would duplicate
            errors.append(f"{k!r}: key に使えない文字があります（{KEY_CHARS} のみ）")
            continue
        if k in keys:
            errors.append(f"{k}: key が重複")
        keys[k] = i
        if i.get("level") not in LEVEL_RANK:
            errors.append(f"{k}: level が不正 {i.get('level')!r}")
        if not (i.get("titleJa") or "").strip():
            errors.append(f"{k}: titleJa が空")
    kids: Dict[str, int] = {}
    for i in items:
        p = i.get("parentKey")
        if not p:
            continue
        kids[p] = kids.get(p, 0) + 1
        parent = keys.get(p)
        if parent is None:
            errors.append(f"{i['key']}: 親 {p} がない")
        elif LEVEL_RANK.get(parent.get("level"), 9) >= LEVEL_RANK.get(i.get("level"), -1):
            errors.append(f"{i['key']}: 親 {p} の level が子以下")
    errors += [f"{p}: 子が {n} 件（上限 {MAX_CHILDREN}）" for p, n in kids.items() if n > MAX_CHILDREN]
    return errors


def ordered(items: List[dict]) -> List[dict]:
    pos = {i["key"]: n for n, i in enumerate(items)}
    return sorted(items, key=lambda i: (LEVEL_RANK[i["level"]], pos[i["key"]]))


def _ref_line(ref: dict, ctx: BodyContext) -> str:
    path, section = ref.get("path", ""), (ref.get("section") or "").strip()
    tail = f" — {section}" if section else ""
    if ctx.ref_style == "permalink":
        full = "/".join(p for p in (ctx.specs_root.strip("/"), path) if p)
        url = f"https://github.com/{ctx.repo}/blob/{urllib.parse.quote(ctx.ref or 'main')}/{urllib.parse.quote(full)}"
        return f"- [{path}]({url}){tail}"
    edition = f"（{ctx.edition}）" if ctx.edition else ""
    return f"- `{path}`{tail}{edition}"


def _dep_line(dep: str, ctx: BodyContext) -> str:
    return f"- {link_keys(dep, ctx.numbers)}"


def _section(name: str, value, ctx: BodyContext) -> Optional[str]:
    if value in (None, "", []):
        return None
    head = f"## {HEADINGS.get(name, name)}"
    if name == "参照":
        lines = [_ref_line(r, ctx) if isinstance(r, dict) else f"- {r}" for r in value]
    elif name == "依存":
        lines = [_dep_line(d, ctx) for d in value]
    elif name == "完了の定義":
        lines = [f"- [ ] {v}" for v in value]
    elif name == "対象FT":
        lines = ["、".join(value)]
    elif isinstance(value, list):
        lines = [f"- {v}" for v in value]
    else:
        lines = [str(value)]
    if name not in ("参照", "依存"):  # file paths / already 「#n（key）」; every other section links its keys
        lines = [link_keys(line, ctx.numbers) for line in lines]
    return "\n".join([head] + lines)


def render_body(item: dict, ctx: BodyContext) -> str:
    body = item.get("bodyJa") or {}
    names = SECTION_ORDER + [k for k in body if k not in SECTION_ORDER]
    parts = [marker(item["key"])]
    parts += [s for s in (_section(n, body.get(n), ctx) for n in names) if s]
    meta = [f"種別: {LEVEL_JA[item['level']]}"]
    if item.get("layer"):
        meta.append(f"層: {item['layer']}")
    if item.get("assigneeRole"):
        meta.append(f"担当（仮）: {item['assigneeRole']}")
    meta.append(f"キー: {item['key']}")
    parts.append("---\n" + " ・ ".join(meta))
    return "\n\n".join(parts) + "\n"


def needed_labels(items: List[dict]) -> List[str]:
    return sorted({lab for i in items for lab in (i.get("labels") or [])})
