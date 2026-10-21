"""Checks behind the tables: snapshot count / keys, parent = sum of children, sprint scope, burndown dates."""
from __future__ import annotations

import datetime as _dt
import re
from typing import Dict, List, Optional, Tuple

from progress_tables import num, scope

DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def snapshot_errors(snap: dict, key_map: Dict[str, dict], expect_items: Optional[int]) -> List[str]:
    """A snapshot only counts as official when its items match the expected count and the key map 1:1."""
    errors = []
    n = len(snap["items"])
    if expect_items is not None and n != expect_items:
        errors.append(f"件数が一致しません: スナップショット {n} 件 / 期待 {expect_items} 件")
    if key_map:
        keys = {i.get("key") for i in snap["items"]}
        no_key = [f"#{i['number']}" for i in snap["items"] if not i.get("key")]
        absent = sorted(set(key_map) - keys)
        if no_key:
            errors.append(f"key-map にない issue が {len(no_key)} 件: {no_key[:5]}")
        if absent:
            errors.append(f"key-map のキーが Project にない: {len(absent)} 件: {absent[:5]}")
    return errors


def parent_sum_check(items: List[dict], fields: List[str]) -> dict:
    """Every parent in the snapshot vs the sum of its direct children (all iterations, whole snapshot)."""
    kids: Dict[int, List[dict]] = {}
    for i in items:
        if i.get("parentNumber"):
            kids.setdefault(i["parentNumber"], []).append(i)
    rows, checked = [], 0
    for p in items:
        children = kids.get(p["number"])
        if not children:
            continue
        checked += 1
        for f in fields:
            pv, cvs = p["fields"].get(f), [c["fields"].get(f) for c in children]
            if pv is None and all(v is None for v in cvs):
                continue
            total = sum(num(v) for v in cvs)
            note = "子に未設定あり" if any(v is None for v in cvs) else ("親が未設定" if pv is None else "")
            if note or abs(num(pv) - total) > 1e-9:
                rows.append({"key": p.get("key") or f"#{p['number']}", "field": f, "parent": pv,
                             "childrenSum": total, "note": note})
    return {"checkedParents": checked, "mismatches": rows}


def status_state_mismatches(items: List[dict], status_field: str, done_status: str = "完了") -> List[dict]:
    """Counted issues whose Status and open / closed state disagree (完了 but open, or closed but not 完了):
    the status table counts by Status, the burndown by Status or closed, so both drift apart."""
    rows = []
    for i in items:
        done, closed = i["fields"].get(status_field) == done_status, i.get("state") == "CLOSED"
        if done != closed:
            rows.append({"key": i.get("key") or f"#{i['number']}", "number": i["number"],
                         "status": i["fields"].get(status_field), "state": i.get("state"),
                         "problem": f"Status {done_status} だが未クローズ" if done else f"クローズ済みだが Status ≠ {done_status}"})
    return rows


def sprint_scope(snap: dict, plan: Optional[dict], iteration: Optional[str], iteration_field: str,
                 include_parents: bool) -> Tuple[List[dict], dict]:
    """Items of the iteration; with a plan snapshot, also the planned ones that moved to another iteration."""
    items = scope(snap, iteration, iteration_field, include_parents)
    info = {"planSnapshot": None, "movedOut": 0}
    if not (plan and iteration):
        return items, info
    planned = {(i.get("repo"), i["number"]) for i in scope(plan, iteration, iteration_field, include_parents)}
    have = {(i.get("repo"), i["number"]) for i in items}
    moved = [i for i in scope(snap, None, iteration_field, include_parents)
             if (i.get("repo"), i["number"]) in planned - have]
    info.update(planSnapshot=plan.get("takenAt"), movedOut=len(moved))
    return items + moved, info


def _local_date(stamp: str, tz: str) -> str:
    hours, minutes = int(tz[:3]), int(tz[0] + tz[4:6])
    zone = _dt.timezone(_dt.timedelta(hours=hours, minutes=minutes))
    return _dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(zone).date().isoformat()


def done_dates(items: List[dict], sd: dict, status_field: str, tz: str,
               done_status: str = "完了") -> Tuple[Dict[int, str], str, List[str]]:
    """Completion day per issue number. Source: the file's `completed` (checked against the Project:
    format, inside `days`, Status / state really done, nothing done left out) or else closedAt."""
    days, errors = sd.get("days") or [], []
    bad_days = [d for d in days if not DATE_RX.match(str(d))]
    if bad_days or days != sorted(days):
        errors.append(f"days は YYYY-MM-DD の昇順にしてください: {bad_days[:3] or days[:3]}")
    is_done = {i["number"]: i["fields"].get(status_field) == done_status or i.get("state") == "CLOSED" for i in items}
    completed = sd.get("completed")
    if not completed:
        dates = {i["number"]: _local_date(i["closedAt"], tz) for i in items if i.get("closedAt")}
        return dates, f"Project の closedAt（{tz} の日付）", errors
    ref = {i.get("key"): i for i in items if i.get("key")}
    ref.update({f"#{i['number']}": i for i in items})
    dates: Dict[int, str] = {}
    for k, d in completed.items():
        if k not in ref:
            errors.append(f"sprint-days の完了日に対象外の項目があります: {k}")
        elif not DATE_RX.match(str(d)) or d not in days:
            errors.append(f"{k}: 完了日 {d!r} は days の中の YYYY-MM-DD ではありません")
        elif not is_done[ref[k]["number"]]:
            errors.append(f"{k}: Project では完了していない（Status / state）のに完了日があります")
        else:
            dates[ref[k]["number"]] = d
    missing = [i.get("key") or f"#{i['number']}" for i in items if is_done[i["number"]] and i["number"] not in dates]
    if missing:
        errors.append(f"Project で完了済みなのに完了日がない: {missing[:5]}")
    return dates, "sprint-days の completed（模擬。Project の Status / state と照合済み）", errors
