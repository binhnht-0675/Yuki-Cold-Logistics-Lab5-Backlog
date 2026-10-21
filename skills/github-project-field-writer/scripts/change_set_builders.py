"""Build change-sets: from an estimate-swp report (+ hour rule) or from a sprint plan."""
from __future__ import annotations

import datetime as _dt
import math
from typing import Dict, List, Optional, Tuple

from change_set_checks import preflight_value_errors
from estimate_swp_payload import split_ref

SCHEMA = "change-set/1"


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def round_to(value: float, step: float) -> float:
    """Round half up to a multiple of step (0.5 -> 7.25 becomes 7.5)."""
    return math.floor(value / step + 0.5 + 1e-9) * step


def hours_for(swp: float, rule: Optional[dict]) -> Optional[float]:
    if not rule:
        return None
    return round_to(swp * float(rule["k"]) * float(rule.get("f", 1)), float(rule.get("round", 0.5)))


def children_index(backlog: List[dict]) -> Dict[str, List[str]]:
    kids: Dict[str, List[str]] = {}
    for item in backlog:
        if item.get("parentKey"):
            kids.setdefault(item["parentKey"], []).append(item["key"])
    return kids


def build_from_estimate(payload: dict, key_map: Dict[str, dict], backlog: List[dict], rule: Optional[dict],
                        repo: Optional[str], swp_field: str, hours_field: str) -> Tuple[dict, List[str]]:
    """Leaves from finalSWP, parents = sum of children. Gaps go to cs["blockingErrors"] (apply refuses)."""
    warns: List[str] = []
    errors: List[str] = []
    key_by_num = {e["number"]: k for k, e in key_map.items()}
    leaf: Dict[str, Tuple[float, Optional[float]]] = {}
    for issue in payload.get("issues", []):
        r, n = split_ref(issue.get("issueRef", ""))
        if n is None or (repo and r and r.lower() != repo.lower()):
            warns.append(f"対象外の issueRef: {issue.get('issueRef')}")
            continue
        key = key_by_num.get(n)
        if not key:
            warns.append(f"key-map にない issue: #{n}")
            continue
        swp = issue.get("finalSWP")
        if swp is None:
            warns.append(f"{key}: finalSWP がない")
            continue
        leaf[key] = (float(swp), hours_for(float(swp), rule))
    kids = children_index(backlog)
    values: Dict[str, Tuple[float, Optional[float]]] = {k: v for k, v in leaf.items() if k not in kids}
    for item in backlog:  # every backlog leaf (task) must have a value
        if item["key"] not in kids and item["key"] not in values:
            errors.append(f"末端 {item['key']}: SWP がない（レポートに含まれていない）")

    def total(key: str) -> Optional[Tuple[float, Optional[float]]]:
        if key in values:
            return values[key]
        if key not in kids:
            return None
        parts = [total(c) for c in kids[key]]
        if any(p is None for p in parts):
            missing = [c for c, p in zip(kids[key], parts) if p is None]
            warns.append(f"{key}: 子の値がそろわないため親の合計を出しません（不足 {missing[:3]}…）")
            errors.append(f"親 {key}: 子の値がそろわないため書けない")
            return None
        hrs = None if rule is None else sum(p[1] for p in parts)
        values[key] = (sum(p[0] for p in parts), hrs)
        return values[key]

    for parent in kids:
        total(parent)
    for key in sorted(set(leaf) & set(kids)):  # the report scored a parent directly
        if key in values and leaf[key][0] != values[key][0]:
            errors.append(f"{key}: レポートの値 {leaf[key][0]} が子の合計 {values[key][0]} と一致しません")
    for p in payload.get("parents", []):  # cross-check with the report's own rollup
        _r, n = split_ref(p.get("issueRef", ""))
        key = key_by_num.get(n) if n is not None else None
        if key in values and p.get("finalSWP") is not None and float(p["finalSWP"]) != values[key][0]:
            msg = f"{key}: 親の合計 {values[key][0]} がレポートの {p['finalSWP']} と一致しません"
            warns.append(msg)
            errors.append(msg)
    order = {i["key"]: n for n, i in enumerate(backlog)}
    changes = []
    for key in sorted(values, key=lambda k: order.get(k, 10 ** 6)):
        swp, hrs = values[key]
        fields = {swp_field: _num(swp)}
        if hrs is not None:
            fields[hours_field] = _num(hrs)
        change = {"key": key, "fields": fields, "derived": "sum-of-children" if key in kids else "payload"}
        if key in kids:
            change["children"] = kids[key]
        changes.append(change)
    return {"schema": SCHEMA, "source": {"kind": "estimate-swp", "createdAt": now(), "hourRule": rule},
            "changes": changes, "blockingErrors": errors}, warns


def _num(v: float):
    return int(v) if float(v).is_integer() else v


def build_from_sprint_plan(plan: dict, status_field: str, iteration_field: str) -> Tuple[dict, List[str]]:
    changes, warns, seen = [], [], set()
    for row in plan.get("items", []):
        key = row.get("key")
        if not key or key in seen:
            warns.append(f"key が空か重複: {key!r}")
            continue
        seen.add(key)
        fields = {}
        if "status" in row:
            fields[status_field] = row["status"]
        if "iteration" in row:
            fields[iteration_field] = row["iteration"]
        change = {"key": key, "fields": fields}
        for k in ("close", "reopen", "addLabels", "removeLabels", "comment"):
            if row.get(k):
                change[k] = row[k]
        changes.append(change)
    return {"schema": SCHEMA, "source": {"kind": "sprint-plan", "createdAt": now()}, "changes": changes}, warns


def validate_change_set(cs: dict, fmap: Optional[dict]) -> List[str]:
    errors = []
    if cs.get("schema") != SCHEMA:
        errors.append(f"schema が {SCHEMA} ではありません")
    keys = [c.get("key") for c in cs.get("changes", [])]
    if len(keys) != len(set(keys)):
        errors.append("key が重複しています")
    for c in cs.get("changes", []):
        if c.get("close") and c.get("reopen"):
            errors.append(f"{c['key']}: close と reopen が同時指定")
        for field in (c.get("fields") or {}):
            if fmap and field not in fmap["fields"]:
                errors.append(f"{c['key']}: Project にないフィールド {field}")
    return errors + preflight_value_errors(cs, fmap)
