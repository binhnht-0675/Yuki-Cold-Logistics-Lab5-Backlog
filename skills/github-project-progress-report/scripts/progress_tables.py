"""Pure functions: snapshot -> JA tables (status, epic, role, simulated burndown)."""
from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List, Optional

from project_snapshot import leaf_items

STATUS_ORDER = ["未着手", "進行中", "レビュー中", "完了", "ブロック中"]
UNSET = "（未設定）"


def num(v) -> float:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0


def fmt(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.1f}"


def scope(snap: dict, iteration: Optional[str], iteration_field: str, include_parents: bool) -> List[dict]:
    items = snap["items"] if include_parents else leaf_items(snap["items"])
    if iteration:
        items = [i for i in items if i["fields"].get(iteration_field) == iteration]
    return items


def status_rows(items: List[dict], status_field: str, swp_field: str) -> List[dict]:
    groups: Dict[str, List[dict]] = OrderedDict((s, []) for s in STATUS_ORDER)
    for i in items:
        groups.setdefault(i["fields"].get(status_field) or UNSET, []).append(i)
    rows = []
    for status, members in groups.items():
        if not members and status not in ("未着手", "進行中", "完了"):
            continue
        closed = sum(1 for m in members if m.get("state") == "CLOSED")
        rows.append({"status": status, "count": len(members), "swp": sum(num(m["fields"].get(swp_field)) for m in members),
                     "note": f"クローズ済み {closed}" if closed else ""})
    return rows


def root_of(item: dict, by_number: Dict[int, dict]) -> dict:
    seen, cur = set(), item
    while cur.get("parentNumber") in by_number and cur["number"] not in seen:
        seen.add(cur["number"])
        cur = by_number[cur["parentNumber"]]
    return cur


def epic_rows(snap: dict, items: List[dict], status_field: str, swp_field: str, hours_field: str,
              done_status: str = "完了") -> List[dict]:
    by_number = {i["number"]: i for i in snap["items"]}
    groups: Dict[int, dict] = {}
    for i in items:
        root = root_of(i, by_number)
        g = groups.setdefault(root["number"], {"epic": f"{root.get('key') or '#' + str(root['number'])} {root['title']}",
                                               "sort": (root.get("key") or "", root["number"]),
                                               "count": 0, "done": 0, "swp": 0.0, "doneSwp": 0.0, "hours": 0.0})
        swp = num(i["fields"].get(swp_field))
        g["count"] += 1
        g["swp"] += swp
        g["hours"] += num(i["fields"].get(hours_field))
        if i["fields"].get(status_field) == done_status:
            g["done"] += 1
            g["doneSwp"] += swp
    return sorted(groups.values(), key=lambda g: g["sort"])


def role_rows(items: List[dict], role_field: str, swp_field: str, hours_field: str) -> List[dict]:
    groups: Dict[str, dict] = {}
    for i in items:
        r = i["fields"].get(role_field) or UNSET
        g = groups.setdefault(r, {"role": r, "count": 0, "swp": 0.0, "hours": 0.0})
        g["count"] += 1
        g["swp"] += num(i["fields"].get(swp_field))
        g["hours"] += num(i["fields"].get(hours_field))
    return sorted(groups.values(), key=lambda g: g["role"])


def burndown_rows(items: List[dict], days: List[str], done_on: Dict[int, str], swp_field: str) -> List[dict]:
    """done_on: issue number -> completion day (see progress_checks.done_dates) -> remaining SWP per day."""
    total = sum(num(i["fields"].get(swp_field)) for i in items)
    rows, n = [], len(days)
    for idx, day in enumerate(days):
        done_today = sum(num(i["fields"].get(swp_field)) for i in items if done_on.get(i["number"]) == day)
        burned = sum(num(i["fields"].get(swp_field)) for i in items
                     if done_on.get(i["number"]) and done_on[i["number"]] <= day)
        rows.append({"day": day, "ideal": round(total * (n - idx - 1) / n, 1),
                     "remaining": total - burned, "doneToday": done_today})
    return rows


def md_table(headers: List[str], rows: List[List[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)
