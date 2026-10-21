#!/usr/bin/env python3
"""github-project-field-writer: write Project fields from a reviewed change-set.

Commands: build-from-estimate-swp | build-from-sprint-plan | diff (default) | apply | revert-from-log.
Nothing is written to GitHub unless `apply` / `revert-from-log` get --apply.
apply / revert-from-log refuse (exit 2, zero writes) while the change-set has blocking errors: a backlog
leaf without SWP, a missing parent, parent != sum of children, an unreviewed estimate-made change-set
(decided from its content, not source.kind), or a Status / iteration value that is not in field-map.
After reading the Project, apply also refuses (exit 2, zero writes) on any error row (a key that is not on
the Project) and on parent != sum of children on the Project after the write. Each run gets its own log.
diff / apply / revert-from-log run the content guard on comments, added labels and text values first.
revert-from-log writes the revert change-set to --change-set; an existing file is replaced only when it is a
revert built from the same log (a re-run), otherwise exit 2 unless --force.
Exit: 0 ok, 1 error, 2 usage/validation, 3 content guard blocked, 75 rate-limit stop (re-run later;
already-equal values are skipped).
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared"))
sys.path.insert(0, HERE)

from change_set_apply import (change_set_entries, comment_marks, comment_note, execute, plan_ops,  # noqa: E402
                              render_diff, summary)
from change_set_builders import validate_change_set  # noqa: E402
from change_set_checks import blocking_errors, writes_estimate  # noqa: E402
from change_set_live_comments import check_comment_ops  # noqa: E402
from change_set_project_checks import stop_reasons  # noqa: E402
from change_set_revert import revert_change_set  # noqa: E402
from content_guard import guard  # noqa: E402
from field_write_run_log import all_log_rows, default_log_path, write_rows, write_run_meta  # noqa: E402
from gh_runner import (EXIT_RATE_LIMIT_STOP, GhError, RateLimitStop, add_runner_args,  # noqa: E402
                       add_write_window_args, runner_from_args)
from key_map import load_key_map  # noqa: E402
from project_fields import load_field_map  # noqa: E402
from project_snapshot import load_snapshot, read_snapshot  # noqa: E402
from write_fields_build_command import cmd_build, load_json, save_change_set  # noqa: E402
from write_log import WriteLog, read_log  # noqa: E402

SKILL = "github-project-field-writer"
COMMANDS = ["build-from-estimate-swp", "build-from-sprint-plan", "diff", "apply", "revert-from-log"]


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", nargs="?", default="diff", choices=COMMANDS)
    p.add_argument("--change-set", help="build の出力先 / diff・apply の入力")
    p.add_argument("--html", help="estimate-swp の HTML レポート")
    p.add_argument("--hour-rule", help='{"k": 時間/SWP, "f": 係数, "round": 0.5}')
    p.add_argument("--backlog", help="親子関係（parentKey）を持つバックログ JSON")
    p.add_argument("--plan", help="build-from-sprint-plan の入力 JSON")
    p.add_argument("--from-log", help="revert-from-log の対象ログ CSV")
    p.add_argument("--repo")
    p.add_argument("--owner")
    p.add_argument("--project", type=int)
    p.add_argument("--state-dir", default="state")
    p.add_argument("--snapshot", help="diff を GitHub に接続せずに行う場合のスナップショット")
    p.add_argument("--diff-out", help="差分表（Markdown）の保存先")
    p.add_argument("--swp-field", default="SWP")
    p.add_argument("--hours-field", default="見積時間(h)")
    p.add_argument("--status-field", default="Status")
    p.add_argument("--iteration-field", default="スプリント")
    p.add_argument("--apply", action="store_true", help="実際に GitHub へ書き込む")
    p.add_argument("--log", help="この実行のログ CSV（既定: <state-dir>/write-logs/<change-set 名>-<内容の sha8>.csv）")
    p.add_argument("--reviewed-by", help="build-from-estimate-swp: 代表 issue をレビューした人（change-set とログに記録）")
    p.add_argument("--reviewed-at", help="build-from-estimate-swp: レビューした日（YYYY-MM-DD）")
    p.add_argument("--force", action="store_true", help="revert-from-log: 既存の --change-set を上書きする")
    add_runner_args(p)
    add_write_window_args(p)
    return p.parse_args(argv)


def current_snapshot(ns, runner, kmap_path, offline_ok):
    if offline_ok and ns.snapshot:
        return load_snapshot(ns.snapshot)
    if not (ns.owner and ns.project and ns.repo):
        raise ValueError("--repo / --owner / --project（または diff では --snapshot）が必要です")
    return read_snapshot(runner, ns.owner, ns.project, load_key_map(kmap_path), ns.repo)


def replaceable_revert(path, from_log) -> bool:
    """revert-from-log may write `path` only if it is new or an earlier revert built from the same log (re-run)."""
    if not os.path.exists(path):
        return True
    try:
        src = load_json(path).get("source") or {}
    except (OSError, ValueError, AttributeError):
        return False
    return src.get("kind") == "revert" and src.get("fromLog") == os.path.basename(from_log)


def cmd_diff_apply(ns, cs, fmap, runner, kmap_path):
    errors = validate_change_set(cs, fmap)
    if errors:
        print("\n".join("ERROR " + e for e in errors[:50]))
        return 2
    estimate_fields = (ns.swp_field, ns.hours_field)
    revert = ns.command == "revert-from-log"  # the change-set was just built from the log in this process
    blocking = blocking_errors(cs, estimate_fields, revert)
    if blocking:
        tag = "WARN [apply 停止]" if ns.command == "diff" else "ERROR"
        print("\n".join(f"{tag} {e}" for e in blocking[:50]))
        if ns.command != "diff":
            print(f"書き込みません（{len(blocking)} 件）。change-set を作り直してから再実行してください。")
            return 2
    if (cs.get("source") or {}).get("kind") == "manual" and writes_estimate(cs, estimate_fields):
        print("WARN source.kind = manual（見積もり由来の印なし）: 代表 issue のレビュー記録を検査せずに SWP / 見積時間を"
              "書きます。ログの #run 行に kind=manual を残します。親 = 子の合計は書き込み前に Project 上で検査します")
    blocked = guard(change_set_entries(cs), ns.repo)  # whole change-set, before reading or writing
    if blocked:
        return blocked
    offline = ns.command == "diff" and bool(ns.snapshot)
    snap = current_snapshot(ns, runner, kmap_path, offline_ok=offline)
    log_path = ns.log or default_log_path(ns.state_dir, ns.change_set, cs)
    ops = plan_ops(cs, snap, *comment_marks(write_rows(all_log_rows(ns.state_dir, log_path))))
    if not offline:  # comments are not in the snapshot: read them (only where a comment op needs it)
        check_comment_ops(runner, ns.repo, ops)
    stop, notes = stop_reasons(ops, snap, estimate_fields, revert)
    table = render_diff(ops)
    if ns.diff_out:
        with open(ns.diff_out, "w", encoding="utf-8") as fh:
            fh.write(table + "\n")
        print(f"差分表: {ns.diff_out}")
    else:
        print(table)
    print(f"集計: {summary(ops)}（基準: {snap.get('takenAt')}）")
    for line in [comment_note(ops)] + ["WARN " + n for n in notes]:
        if line:
            print(line)
    if stop:
        tag = "WARN [apply 停止]" if ns.command == "diff" else "ERROR"
        print("\n".join(f"{tag} {e}" for e in stop[:50]))
        if ns.command != "diff":
            print(f"書き込みません（{len(stop)} 件。最初の書き込みの前に全行を検査）。key-map / Project / change-set を直して再実行。")
            return 2
    if ns.command == "diff" or not ns.apply:
        if ns.command != "diff":
            print("dry-run のため GitHub は変更していません。実行するには --apply を付けてください。")
        return 0
    log = WriteLog(log_path, SKILL, ns.command)
    if any(not o["same"] and not o.get("error") for o in ops):
        write_run_meta(log, ns.change_set, cs)
    done = execute(runner, ops, fmap, ns.repo, log)
    print(f"書き込み: {done} 件（ログ: {log_path}）")
    return 0


def main(argv=None):
    ns = parse_args(argv if argv is not None else sys.argv[1:])
    ns.owner = ns.owner or (ns.repo.split("/")[0] if ns.repo else None)
    kmap_path = os.path.join(ns.state_dir, "key-map.json")
    fmap_path = os.path.join(ns.state_dir, "field-map.json")
    if not ns.change_set:
        print("ERROR --change-set が必要です")
        return 2
    if ns.command.startswith("build-"):
        return cmd_build(ns, kmap_path)
    fmap = load_field_map(fmap_path)
    try:
        runner = runner_from_args(ns)  # a broken write-window file stops here (exit 1)
        if ns.command == "revert-from-log":
            if not ns.from_log:
                print("ERROR --from-log が必要です")
                return 2
            if not ns.force and not replaceable_revert(ns.change_set, ns.from_log):
                print(f"ERROR --change-set が既にあり、このログから作った戻し用ではありません: {ns.change_set}"
                      "（元の change-set を守るため上書きしない。別の名前にするか、上書きするなら --force）")
                return 2
            cs, warns = revert_change_set(list(read_log(ns.from_log)), fmap, SKILL)
            cs["source"]["fromLog"] = os.path.basename(ns.from_log)
            for w in warns:
                print("WARN " + w)
            save_change_set(ns.change_set, cs)
        else:
            cs = load_json(ns.change_set)
        return cmd_diff_apply(ns, cs, fmap, runner, kmap_path)
    except RateLimitStop as e:
        print(f"STOPPED レート制限が続いたため停止: {e}. 時間をおいて同じコマンドを再実行（同値はスキップ）。")
        return EXIT_RATE_LIMIT_STOP
    except (GhError, ValueError, KeyError) as e:
        print(f"ERROR {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
