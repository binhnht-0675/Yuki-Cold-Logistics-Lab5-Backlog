"""Checks run before the first write: field-map vs options / Project, and the Project title.

`apply` calls `field_map_errors` before any gh call, then `live_project_errors` after the read-only
snapshot and `live_field_errors` after one read of the Project's fields (same query as fetch-field-map):
the field name, field id, type and every option name -> id of the fields it writes (担当（仮） / Status)
must be the same on the Project as in field-map. Any difference stops the run with exit 2, zero writes.
"""
from __future__ import annotations

from typing import List, Optional

from content_guard import CATEGORY_JA, scan_text


def field_map_errors(fmap: dict, ns, items: List[dict], need_project: bool) -> List[str]:
    errors = []
    if need_project and ns.project is None:
        errors.append("--project が必要です")
    owner, number = str(fmap.get("owner") or ""), fmap.get("number")
    if (ns.project is not None and number != ns.project) or (ns.owner and owner.lower() != ns.owner.lower()):
        errors.append(f"field-map は {owner} の Project {number} 用です（--owner {ns.owner} --project {ns.project}"
                      " と不一致）。fetch-field-map をやり直してください")
    fields = fmap.get("fields") or {}
    wanted = ((ns.role_field, {i.get("assigneeRole") for i in items}), (ns.status_field, {ns.initial_status}))
    for field, values in wanted:
        spec = fields.get(field)
        if spec is None:
            errors.append(f"field-map にフィールド「{field}」がありません（あるもの: {', '.join(sorted(fields))}）")
            continue
        if spec.get("type") != "single_select":
            errors.append(f"{field} は単一選択フィールドではありません（{spec.get('type')}）")
            continue
        bad = sorted(v for v in values if v and v not in (spec.get("options") or {}))
        if bad:
            errors.append(f"{field} に選択肢がない値: {bad}")
    return errors


def live_project_errors(fmap: dict, snap: dict) -> List[str]:
    if snap.get("projectId") != fmap.get("projectId"):
        return [f"field-map の Project ID {fmap.get('projectId')} が、読み取った Project の ID "
                f"{snap.get('projectId')} と違います。fetch-field-map をやり直してください"]
    return []


def live_field_errors(fmap: dict, live: dict, names) -> List[str]:
    """field-map vs the Project as it is now, for the fields `apply` writes."""
    errors = []
    for name in names:
        want, have = (fmap.get("fields") or {}).get(name), (live.get("fields") or {}).get(name)
        if have is None:
            errors.append(f"Project にフィールド「{name}」がありません（名前が変わった・削除された可能性）")
            continue
        if want is None:
            continue  # reported by field_map_errors
        if (want.get("id"), want.get("type")) != (have.get("id"), have.get("type")):
            errors.append(f"{name}: field-map の id / 型 {want.get('id')} / {want.get('type')} が Project の "
                          f"{have.get('id')} / {have.get('type')} と違います")
        w, h = want.get("options") or {}, have.get("options") or {}
        diff = sorted(k for k in set(w) | set(h) if w.get(k) != h.get(k))
        if diff:
            errors.append(f"{name}: 選択肢（名前 → id）が Project と違います: {diff[:10]}")
    if errors:
        errors.append("fetch-field-map をやり直してください（書き込み 0 件）")
    return errors


def project_title_warnings(fmap: Optional[dict], allow_repo: str) -> List[str]:
    """The skill never writes the Project title, but a public Project shows it: warn, do not block."""
    title = (fmap or {}).get("title") or ""
    found = scan_text(title, allow_repo)
    if not found:
        return []
    kinds = "・".join(sorted({f"{CATEGORY_JA[c]}（{rule}）" for c, rule, *_ in found}))
    return [f"WARN Project 名に公開しない内容: {kinds}。このスキルは Project 名を書き込みませんが、"
            "公開 Project なら GitHub の画面で名前を変えてから fetch-field-map をやり直してください"]


def print_all(lines: List[str], prefix: str = "") -> None:
    for line in lines:
        print(prefix + line)
