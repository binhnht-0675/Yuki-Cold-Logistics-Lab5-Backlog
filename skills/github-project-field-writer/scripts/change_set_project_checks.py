"""Checks on the planned ops against the live Project, run after reading it and before the first write.

- error rows (a key that is not on the Project, an ambiguous comment to delete): `apply` writes nothing
  (exit 2), so a parent is never written while one of its leaves is missing.
- parent = sum of children AFTER the write, on the Project itself (parent links from the snapshot), for
  every parent whose own value or a direct child's value of the SWP / hours fields changes.
`revert-from-log` only warns: it must be able to restore what it can (old values, comments).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from change_set_apply import FOREIGN


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def row_errors(ops: List[dict]) -> List[str]:
    return [f"{o['key']} {o['field']}: {o['error']}" for o in ops if o.get("error")]


def project_parent_errors(snap: dict, ops: List[dict], fields) -> List[str]:
    items = {i["number"]: i for i in snap.get("items", [])}
    after = {n: dict(i.get("fields") or {}) for n, i in items.items()}
    touched = set()
    for o in ops:
        if o["kind"] == "field" and o["field"] in fields and not o["same"] and not o.get("error") \
                and o["number"] in after:
            after[o["number"]][o["field"]] = o["new"]
            touched.add((o["number"], o["field"]))
    kids: Dict[int, List[int]] = {}
    for n, i in items.items():
        if i.get("parentNumber") in items:
            kids.setdefault(i["parentNumber"], []).append(n)
    targets = set()
    for n, f in touched:
        targets |= {(p, f) for p in (n, items[n].get("parentNumber")) if p in kids}
    errors = []
    for p, f in sorted(targets):
        name = items[p].get("key") or f"#{p}"
        pv, parts = after[p].get(f), [after[k].get(f) for k in kids[p]]
        if pv in (None, "") and all(x in (None, "") for x in parts):
            continue
        if not _num(pv) or not all(_num(x) for x in parts):
            errors.append(f"{name}: 書き込み後の {f} で親 = 子の合計を確かめられない（親か子に値がない）")
        elif abs(sum(parts) - pv) > 1e-9:
            errors.append(f"{name}: 書き込み後の {f} {pv} が Project 上の子の合計 {sum(parts)} と一致しません")
    return errors


def stop_reasons(ops: List[dict], snap: dict, fields, revert: bool) -> Tuple[List[str], List[str]]:
    """-> (reasons that stop apply, warnings). revert-from-log: everything is a warning."""
    found = row_errors(ops) + project_parent_errors(snap, ops, fields)
    notes = [f"{o['key']} {o['field']}: GitHub の値がこの実行の書いた値ではないので戻しません"
             for o in ops if o.get("note") == FOREIGN]
    return ([], found + notes) if revert else (found, notes)
