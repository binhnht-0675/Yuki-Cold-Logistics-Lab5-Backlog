#!/usr/bin/env python3
"""github-project-progress-report (read-only): Project -> snapshot JSON -> JA tables.

Commands: snapshot (reads GitHub, writes snapshot JSON) | tables (offline, snapshot -> Markdown / JSON).
Exit: 0 ok, 1 GitHub error, 2 usage / check failed (snapshot count or key-map mismatch: no file written;
sprint-days not matching the Project), 4 tables written but a parent != sum of its children,
5 (only with --strict) tables written but a counted issue's Status and open / closed state disagree.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared"))
sys.path.insert(0, HERE)

from gh_runner import GhError, add_runner_args, runner_from_args  # noqa: E402
from key_map import load_key_map  # noqa: E402
from progress_checks import (done_dates, parent_sum_check, snapshot_errors, sprint_scope,  # noqa: E402
                             status_state_mismatches)
from progress_markdown import to_markdown  # noqa: E402
from progress_tables import burndown_rows, epic_rows, role_rows, status_rows  # noqa: E402
from project_snapshot import load_snapshot, read_snapshot, save_snapshot  # noqa: E402

EXIT_PARENT_MISMATCH = 4
EXIT_STATUS_STATE_MISMATCH = 5


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["snapshot", "tables"])
    p.add_argument("--owner")
    p.add_argument("--project", type=int)
    p.add_argument("--repo", help="owner/name。このリポジトリの issue だけを数える（大文字小文字は区別しない）。"
                                  "Project に複数リポジトリがあるときは必須")
    p.add_argument("--key-map", default="state/key-map.json")
    p.add_argument("--expect-items", type=int, help="snapshot: 期待するアイテム数（違えば exit 2、ファイルを書かない）")
    p.add_argument("--snapshot", help="tables の入力 / snapshot の出力先")
    p.add_argument("--plan-snapshot", help="tables: 計画時点のスナップショット（--iteration の対象を計画どおりに固定）")
    p.add_argument("--iteration", help="対象イテレーション名（例: スプリント 1）")
    p.add_argument("--include-parents", action="store_true", help="親（epic / story）も数える（既定は末端のみ）")
    p.add_argument("--sprint-days", help="バーンダウンの入力 JSON（days 必須、completed は任意）")
    p.add_argument("--tz", default="+09:00", help="closedAt を日付にするときの時差（既定 +09:00）")
    p.add_argument("--strict", action="store_true",
                   help="tables: Status と open / closed が合わない issue があれば表を出したうえで exit 5")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--out", help="出力ファイル（既定: 標準出力）")
    p.add_argument("--status-field", default="Status")
    p.add_argument("--swp-field", default="SWP")
    p.add_argument("--hours-field", default="見積時間(h)")
    p.add_argument("--role-field", default="担当（仮）")
    p.add_argument("--iteration-field", default="スプリント")
    add_runner_args(p)
    return p.parse_args(argv)


def build(ns, snap):
    plan = load_snapshot(ns.plan_snapshot) if ns.plan_snapshot else None
    items, info = sprint_scope(snap, plan, ns.iteration, ns.iteration_field, ns.include_parents)
    result = {
        "source": dict(info, takenAt=snap.get("takenAt"), project=snap.get("project"), title=snap.get("title"),
                       repo=snap.get("repo"), iteration=ns.iteration, leafOnly=not ns.include_parents,
                       items=len(items)),
        "status": status_rows(items, ns.status_field, ns.swp_field),
        "epics": epic_rows(snap, items, ns.status_field, ns.swp_field, ns.hours_field),
        "roles": role_rows(items, ns.role_field, ns.swp_field, ns.hours_field),
        "missingSwp": sum(1 for i in items if i["fields"].get(ns.swp_field) is None),
        "parentCheck": parent_sum_check(snap["items"], [ns.swp_field, ns.hours_field]),
        "statusStateMismatch": status_state_mismatches(items, ns.status_field),
    }
    if ns.sprint_days:
        with open(ns.sprint_days, encoding="utf-8") as fh:
            sd = json.load(fh)
        dates, source, errors = done_dates(items, sd, ns.status_field, ns.tz)
        if errors:
            raise ValueError("sprint-days が Project と合いません:\n  " + "\n  ".join(errors[:20]))
        result["burndown"] = burndown_rows(items, sd["days"], dates, ns.swp_field)
        result["burndownDateSource"] = source
    return result


def emit(ns, text):
    if ns.out:
        os.makedirs(os.path.dirname(os.path.abspath(ns.out)), exist_ok=True)
        with open(ns.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"出力: {ns.out}")
    else:
        sys.stdout.write(text)


def cmd_snapshot(ns):
    if not (ns.owner and ns.project):
        print("ERROR --owner と --project が必要です")
        return 2
    kmap = load_key_map(ns.key_map)
    try:
        snap = read_snapshot(runner_from_args(ns), ns.owner, ns.project, kmap, ns.repo)
    except (GhError, ValueError) as e:
        print(f"ERROR {e}")
        return 1
    if snap.get("excludedOtherRepo"):
        print(f"WARN 他のリポジトリの issue {snap['excludedOtherRepo']} 件を除外しました（--repo {ns.repo}）")
    errors = snapshot_errors(snap, kmap, ns.expect_items)
    if errors:
        print("\n".join("ERROR " + e for e in errors))
        print("スナップショットは保存しません（正式な数字に使えないため）。")
        return 2
    save_snapshot(ns.snapshot, snap)
    print(f"スナップショット: {len(snap['items'])} 件 → {ns.snapshot}")
    return 0


def main(argv=None):
    ns = parse_args(argv if argv is not None else sys.argv[1:])
    if not ns.snapshot:
        print("ERROR --snapshot が必要です")
        return 2
    if not re.match(r"^[+-]\d{2}:\d{2}$", ns.tz):
        print("ERROR --tz は +09:00 の形で指定してください")
        return 2
    if ns.command == "snapshot":
        return cmd_snapshot(ns)
    try:
        result = build(ns, load_snapshot(ns.snapshot))
    except ValueError as e:
        print(f"ERROR {e}")
        return 2
    emit(ns, json.dumps(result, ensure_ascii=False, indent=1) + "\n" if ns.format == "json" else to_markdown(result))
    if result["parentCheck"]["mismatches"]:
        print(f"ERROR 親 = 子の合計が一致しない行が {len(result['parentCheck']['mismatches'])} 件（表は出力済み）",
              file=sys.stderr if not ns.out else sys.stdout)
        return EXIT_PARENT_MISMATCH
    if result["statusStateMismatch"]:
        print(f"WARN Status と issue の状態（open / closed）が合わない issue が {len(result['statusStateMismatch'])} 件"
              "（表の「注意」を参照）", file=sys.stderr if not ns.out else sys.stdout)
        if ns.strict:
            return EXIT_STATUS_STATE_MISMATCH
    return 0


if __name__ == "__main__":
    sys.exit(main())
