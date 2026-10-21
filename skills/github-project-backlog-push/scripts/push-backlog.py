#!/usr/bin/env python3
"""github-project-backlog-push: backlog.json -> issues + sub-issues + Project items.

Commands: plan (default, offline) | apply | rebuild-key-map | update-body |
close-and-mark | fetch-field-map. Nothing is written unless --apply is given.
Every string to be sent is checked by the content guard before the first write (plan / apply /
update-body / close-and-mark).
`apply` checks the field-map (fields, options, Project) before the first write (exit 2).
Issues with a backlog key opened by another account while the gh account is not the repository owner:
exit 2 before any write (probably run under a second account; see key_map.py).
Exit codes: 0 ok, 1 error, 2 usage/validation, 3 content guard blocked, 10 --max-writes reached
(apply / update-body / close-and-mark, dry-run included), 75 rate limit stop.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared"))
sys.path.insert(0, HERE)

from backlog_maintenance_commands import cmd_close, cmd_rebuild, cmd_update_body, content_entries  # noqa: E402
from backlog_model import load_backlog, validate  # noqa: E402
from backlog_plan_apply_commands import cmd_apply, cmd_plan  # noqa: E402
from content_guard import guard  # noqa: E402
from gh_runner import (EXIT_RATE_LIMIT_STOP, GhError, RateLimitStop, add_runner_args,  # noqa: E402
                       add_write_window_args, runner_from_args)
from key_map import OtherAccountError  # noqa: E402
from project_fields import fetch_field_map, save_field_map  # noqa: E402
COMMANDS = ["plan", "apply", "rebuild-key-map", "update-body", "close-and-mark", "fetch-field-map"]


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", nargs="?", default="plan", choices=COMMANDS)
    p.add_argument("--backlog", help="backlog.json のパス")
    p.add_argument("--repo", help="owner/name（issue を作るリポジトリ）")
    p.add_argument("--owner", help="Project の owner（既定: --repo の owner）")
    p.add_argument("--project", type=int, help="Project 番号")
    p.add_argument("--state-dir", default="state")
    p.add_argument("--ref-style", choices=["permalink", "text"], default="text")
    p.add_argument("--ref", help="permalink の tag / commit")
    p.add_argument("--specs-root", default="", help="リポジトリ内の設計書ルート")
    p.add_argument("--edition", default="", help="text 形式で併記する版表示")
    p.add_argument("--role-field", default="担当（仮）")
    p.add_argument("--status-field", default="Status")
    p.add_argument("--initial-status", default="未着手")
    p.add_argument("--only-level", help="epic,story,task のうち対象 level（カンマ区切り）")
    p.add_argument("--max-writes", type=int, help="1 回の実行での書き込み上限（バッチ）")
    p.add_argument("--keys", help="close-and-mark / update-body の対象キー（カンマ区切り）")
    p.add_argument("--force-body", action="store_true", help="update-body で依存以外の差分（手編集）も上書きする")
    p.add_argument("--close-label", default="廃止")
    p.add_argument("--include-closed", action="store_true",
                   help="close-and-mark: 既にクローズ済みの issue も not planned + 廃止ラベルに変える（既定は変えない）")
    p.add_argument("--show-body", help="plan で本文を表示するキー")
    p.add_argument("--dump-bodies", help="plan で全 issue の本文を <DIR>/<キー>.md に書き出す（追加の検査用）")
    p.add_argument("--verbose", action="store_true", help="dry-run の各書き込みを表示")
    p.add_argument("--apply", action="store_true", help="実際に GitHub へ書き込む")
    add_runner_args(p)
    add_write_window_args(p)
    return p.parse_args(argv)


def paths(ns):
    return {n: os.path.join(ns.state_dir, f) for n, f in
            (("kmap", "key-map.json"), ("fmap", "field-map.json"), ("log", "push-log.csv"))}


def main(argv=None):
    ns = parse_args(argv if argv is not None else sys.argv[1:])
    ns.owner = ns.owner or (ns.repo.split("/")[0] if ns.repo else None)
    P = paths(ns)
    items = []
    if ns.command in ("plan", "apply", "update-body"):
        if not ns.backlog:
            print("ERROR --backlog が必要です")
            return 2
        items = load_backlog(ns.backlog)
        errors = validate(items)
        if errors:
            print("\n".join("ERROR " + e for e in errors[:50]))
            return 2
    if ns.command in ("plan", "apply", "update-body", "close-and-mark"):
        blocked = guard(content_entries(ns, items), ns.repo or "OWNER/REPO")
        if blocked:
            return blocked
    if ns.command == "plan":
        return cmd_plan(ns, items, P)
    if not ns.repo and ns.command != "fetch-field-map":
        print("ERROR --repo が必要です")
        return 2
    try:
        runner = runner_from_args(ns)  # a broken write-window file stops here (exit 1)
        if ns.command == "fetch-field-map":
            save_field_map(P["fmap"], fetch_field_map(runner, ns.owner, ns.project))
            print(f"field-map を保存: {P['fmap']}")
            return 0
        if ns.command == "apply":
            return cmd_apply(ns, items, runner, P)
        if ns.command == "rebuild-key-map":
            return cmd_rebuild(ns, runner, P)
        if ns.command == "update-body":
            return cmd_update_body(ns, items, runner, P)
        return cmd_close(ns, runner, P)
    except OtherAccountError as e:  # raised while listing the issues, before any write
        print(f"ERROR {e}")
        return 2
    except RateLimitStop as e:
        print(f"STOPPED レート制限が続いたため停止: {e}. 時間をおいて同じコマンドを再実行（GitHub の現状から続き）。")
        return EXIT_RATE_LIMIT_STOP
    except (GhError, RuntimeError, ValueError, KeyError) as e:
        print(f"ERROR {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
