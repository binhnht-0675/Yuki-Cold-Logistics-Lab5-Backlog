"""`plan` (offline) and `apply` of push-backlog.py. Both check the field-map before the first write."""
from __future__ import annotations

import os

from backlog_field_map_preflight import (field_map_errors, live_field_errors, live_project_errors, print_all,
                                         project_title_warnings)
from backlog_maintenance_commands import SKILL, context, dump_bodies, missing_parents, selected
from backlog_model import needed_labels, render_body
from backlog_push_executor import BatchLimit, PushExecutor, existing_labels
from backlog_run_estimate import estimate_seconds, format_duration
from key_map import build_key_map, list_repo_issues, load_key_map
from project_fields import fetch_field_map, load_field_map
from project_snapshot import read_item_fields, read_snapshot
from write_log import WriteLog

CONTENT_CREATING = ("issue-create", "sub-issue", "label-create")


def initial_fields(ns):
    return {ns.role_field: lambda i: i.get("assigneeRole"), ns.status_field: lambda i: ns.initial_status}


def print_estimate(ns, counts) -> None:
    total = sum(counts.values())
    creating = sum(counts[k] for k in CONTENT_CREATING)
    cap = ns.max_writes_per_hour
    print(f"書き込み合計（見込み・ラベルは最大値）: {total}（うち内容作成 issue・sub-issue・ラベル {creating}）")
    print(f"所要時間の目安: {format_duration(estimate_seconds(total, ns.pace, cap))}"
          f"（1 件 / {ns.pace:g}s、" + (f"上限 {cap} 件 / 60 分に達したら待機" if cap else "時間あたりの上限なし")
          + "。GitHub のレート制限による待ちは含まない）")


def stop_on_missing_parents(ns, items, kmap) -> int:
    """--only-level story / task before the parent level exists: stop before any write (exit 2)."""
    missing = missing_parents(selected(ns, items), kmap)
    if not missing:
        return 0
    print_all(missing[:50], "ERROR ")
    print(f"親が未作成の項目 {len(missing)} 件。親の level を先に実行してください（epic → story → task）。書き込み 0 件。")
    return 2


def cmd_plan(ns, items, P):
    kmap = load_key_map(P["kmap"])
    if stop_on_missing_parents(ns, items, kmap):
        return 2
    fmap = load_field_map(P["fmap"]) if os.path.exists(P["fmap"]) else None
    if fmap:
        errors = field_map_errors(fmap, ns, items, need_project=False)
        if errors:
            print_all(errors, "ERROR ")
            return 2
        print_all(project_title_warnings(fmap, ns.repo or "OWNER/REPO"))
    ex = PushExecutor(None, context(ns, kmap), dict(kmap), fmap, {}, None, dry=True,
                      initial=initial_fields(ns), printer=print if ns.verbose else (lambda s: None))
    ex.ensure_labels(needed_labels(items), [])
    ex.run(selected(ns, items))
    by_level = {lv: sum(1 for i in selected(ns, items) if i["level"] == lv) for lv in ("epic", "story", "task")}
    new = [i for i in selected(ns, items) if i["key"] not in kmap]
    print(f"backlog: epic {by_level['epic']} / story {by_level['story']} / task {by_level['task']}"
          f"（対象 {sum(by_level.values())} 件、key-map 既存 {len(kmap)} 件）")
    print(f"作成予定 issue: {len(new)}（epic {sum(i['level'] == 'epic' for i in new)} / "
          f"story {sum(i['level'] == 'story' for i in new)} / task {sum(i['level'] == 'task' for i in new)}）")
    for kind in ("sub-issue", "project-add", "field-set", "label-create"):
        print(f"{kind}: {ex.counts[kind]}")
    print_estimate(ns, ex.counts)
    print("field-map: " + ("確認済み" if fmap else "なし（選択肢の検証は省略）"))
    if ns.dump_bodies and dump_bodies(ns, items):
        return 2
    if ns.show_body:
        item = next(i for i in items if i["key"] == ns.show_body)
        print("----- 本文プレビュー -----\n" + render_body(item, context(ns, kmap)))
    return 0


def cmd_apply(ns, items, runner, P):
    if not os.path.exists(P["fmap"]):
        print(f"ERROR {P['fmap']} がありません。先に fetch-field-map を実行してください")
        return 2
    fmap = load_field_map(P["fmap"])
    errors = field_map_errors(fmap, ns, items, need_project=True)  # before any gh call
    if errors:
        print_all(errors, "ERROR ")
        return 2
    print_all(project_title_warnings(fmap, ns.repo))
    kmap = build_key_map(list_repo_issues(runner, ns.repo), fmap["projectId"])
    if stop_on_missing_parents(ns, items, kmap):  # reads only so far
        return 2
    snap = read_snapshot(runner, ns.owner, ns.project, kmap, ns.repo)
    errors = live_project_errors(fmap, snap)  # reads only so far
    if not errors:  # one more read: field names / option ids on the Project as it is now
        live = fetch_field_map(runner, ns.owner, ns.project)
        errors = live_field_errors(fmap, live, (ns.role_field, ns.status_field))
    if errors:
        print_all(errors, "ERROR ")
        return 2
    values = {i["itemId"]: i["fields"] for i in snap["items"]}
    unlisted = [e["projectItemId"] for e in kmap.values() if e.get("projectItemId") and e["projectItemId"] not in values]
    values.update(read_item_fields(runner, unlisted))  # the Project's item list can lag behind recent adds
    log = WriteLog(P["log"], SKILL, "apply")
    ex = PushExecutor(runner, context(ns, kmap), kmap, fmap, values, log, dry=not ns.apply,
                      max_writes=ns.max_writes, key_map_path=P["kmap"], initial=initial_fields(ns))
    try:
        ex.ensure_labels(needed_labels(items), existing_labels(runner, ns.repo))
        ex.run(selected(ns, items))
    except BatchLimit:
        print(f"BATCH_LIMIT {ns.max_writes} 件で停止（次: {ex.current}）。同じコマンドを再実行すると続きから。")
        return 10
    finally:
        print("書き込み" + ("" if ns.apply else "（dry-run）") + f": {dict(ex.counts)}")
    if not ns.apply:
        print("dry-run のため GitHub は変更していません。実行するには --apply を付けてください。")
    return 0
