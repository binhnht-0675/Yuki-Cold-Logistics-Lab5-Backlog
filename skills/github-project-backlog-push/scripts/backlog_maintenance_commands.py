"""Shared CLI helpers and the maintenance commands of push-backlog.py (rebuild-key-map, update-body, close-and-mark).

update-body / close-and-mark write through MaintenanceWrites, the same gate as `apply`: --max-writes (exit 10,
counted in dry-run too), a pending row before each write, a done row after it, a failed row with the exit code
(75 for a rate-limit stop) when gh fails. close-and-mark leaves an already closed issue alone unless
--include-closed is given (its close reason and labels stay as they are)."""
from __future__ import annotations

import hashlib
import os

from backlog_model import BodyContext, render_body
from backlog_push_executor import BatchLimit
from gh_runner import EXIT_RATE_LIMIT_STOP, GhError, RateLimitStop
from key_map import build_key_map, list_repo_issues, save_key_map
from project_fields import load_field_map
from write_log import WriteLog

SKILL = "github-project-backlog-push"


def context(ns, kmap) -> BodyContext:
    return BodyContext(repo=ns.repo or "OWNER/REPO", ref_style=ns.ref_style, ref=ns.ref,
                       specs_root=ns.specs_root, edition=ns.edition,
                       numbers={k: e["number"] for k, e in kmap.items() if e.get("number")})


def content_entries(ns, items):
    """Every string the commands can send to GitHub (all items, whatever --only-level says)."""
    ctx = context(ns, {})  # issue numbers in 依存 cannot add findings; render without them
    for i in items:
        k = i.get("key")
        yield k, "title", i.get("titleJa") or ""
        yield k, "body", render_body(i, ctx)
        yield from ((k, "label", lab) for lab in i.get("labels") or [])
        yield k, "担当（仮）", i.get("assigneeRole") or ""
    yield "-", "Status 初期値", ns.initial_status
    yield "-", "close-label", ns.close_label


def dump_bodies(ns, items) -> int:
    """Write each rendered body to <dir>/<key>.md for an extra offline scan (overlap with sources).

    Every target must sit directly in <dir>; otherwise nothing is written and 2 is returned."""
    root = os.path.realpath(ns.dump_bodies)
    targets = [(i, os.path.join(ns.dump_bodies, f"{i['key']}.md")) for i in items]
    outside = [i["key"] for i, t in targets if os.path.dirname(os.path.realpath(t)) != root]
    if outside:
        print(f"ERROR --dump-bodies の外に出るキーがあるため書き出しません: {', '.join(map(repr, outside[:10]))}")
        return 2
    os.makedirs(ns.dump_bodies, exist_ok=True)
    ctx = context(ns, {})
    for i, target in targets:
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(f"# {i['titleJa']}\n\n" + render_body(i, ctx))
    print(f"本文を書き出し: {len(items)} 件 → {ns.dump_bodies}")
    return 0


def selected(ns, items):
    if not ns.only_level:
        return items
    levels = set(ns.only_level.split(","))
    return [i for i in items if i["level"] in levels]


def missing_parents(chosen, kmap):
    """Items whose parent is neither on GitHub (kmap) nor created earlier in this run."""
    keys = {i["key"] for i in chosen}
    return [f"{i['key']}: 親 {i['parentKey']} が GitHub にまだありません" for i in chosen
            if i.get("parentKey") and i["parentKey"] not in kmap and i["parentKey"] not in keys]


def cmd_rebuild(ns, runner, P):
    fmap = load_field_map(P["fmap"]) if os.path.exists(P["fmap"]) else None
    kmap = build_key_map(list_repo_issues(runner, ns.repo), fmap["projectId"] if fmap else None)
    save_key_map(P["kmap"], ns.repo, kmap)
    linked = sum(1 for e in kmap.values() if e.get("parentNumber"))
    in_proj = sum(1 for e in kmap.values() if e.get("projectItemId"))
    print(f"key-map: {len(kmap)} 件（sub-issue 接続 {linked}、Project 内 {in_proj}）→ {P['kmap']}")
    return 0


def _without_deps(body: str) -> str:
    """Body minus the 依存 section (the part update-body is meant to refresh)."""
    out, skip = [], False
    for line in body.split("\n"):
        if line.startswith("## ") or line.startswith("---"):
            skip = line.strip() == "## 依存"
        if not skip:
            out.append(line)
    return "\n".join(out)


class MaintenanceWrites:
    """--max-writes gate + write-ahead log (pending -> done / failed with exit code), like the apply executor."""

    def __init__(self, log, apply: bool, max_writes):
        self.log, self.apply, self.max_writes, self.count = log, apply, max_writes, 0

    def write(self, key, number, field, old, new, fn):
        if self.max_writes is not None and self.count >= self.max_writes:
            raise BatchLimit(key)
        self.count += 1
        if not self.apply:
            return None
        op = self.log.begin(key, number, field, old, new)
        try:
            fn()
        except GhError as e:
            code = EXIT_RATE_LIMIT_STOP if isinstance(e, RateLimitStop) else e.code
            self.log.write(key, number, field, old, new, exit_code=code, op=op)
            raise
        self.log.write(key, number, field, old, new, op=op)


def batch_stop(ns, key) -> int:
    print(f"BATCH_LIMIT {ns.max_writes} 件で停止（次: {key}）。同じコマンドを再実行すると続きから。")
    return 10


def cmd_update_body(ns, items, runner, P):
    issues = list_repo_issues(runner, ns.repo)
    kmap = build_key_map(issues)
    current = {i["number"]: (i.get("body") or "").replace("\r\n", "\n") for i in issues}  # UI edits use CRLF
    ctx, changed = context(ns, kmap), 0
    w = MaintenanceWrites(WriteLog(P["log"], SKILL, "update-body"), ns.apply, ns.max_writes)
    only = set(k for k in (ns.keys or "").split(",") if k)
    h = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]  # noqa: E731
    for item in selected(ns, items):
        entry = kmap.get(item["key"])
        if not entry or (only and item["key"] not in only):
            continue
        new = render_body(item, ctx)
        old = current[entry["number"]]
        if new == old:
            continue
        if _without_deps(new) != _without_deps(old) and not ns.force_body:
            print(f"WARN {item['key']} #{entry['number']}: 依存以外も異なる（手で編集された可能性）ため更新しません。"
                  "上書きするなら --force-body")
            continue
        try:
            w.write(item["key"], entry["number"], "body", h(old), h(new), lambda n=entry["number"], b=new:
                    runner.api_json(f"repos/{ns.repo}/issues/{n}", "PATCH", {"body": b}, write=True))
        except BatchLimit:
            return batch_stop(ns, item["key"])
        changed += 1
        print(("" if ns.apply else "[dry-run] ") + f"本文更新 {item['key']} #{entry['number']} {h(old)} → {h(new)}")
    print(f"本文更新: {changed} 件" + ("" if ns.apply else "（dry-run）"))
    return 0


def cmd_close(ns, runner, P):
    keys = [k for k in (ns.keys or "").split(",") if k]
    if not keys:
        print("ERROR --keys が必要です")
        return 2
    kmap = build_key_map(list_repo_issues(runner, ns.repo))
    w = MaintenanceWrites(WriteLog(P["log"], SKILL, "close-and-mark"), ns.apply, ns.max_writes)
    for k in keys:
        e = kmap.get(k)
        if not e:
            print(f"WARN {k}: issue が見つかりません")
            continue
        n = e["number"]
        if e.get("state") == "CLOSED" and not ns.include_closed:
            print(f"WARN {k} #{n}: 既にクローズ済みのため変更しません（クローズ理由・ラベルはそのまま。"
                  "not planned と廃止ラベルに変えるなら --include-closed）")
            continue
        print(("" if ns.apply else "[dry-run] ") + f"close + ラベル {ns.close_label}: {k} #{n}")
        has_label = ns.close_label.casefold() in {x.casefold() for x in e.get("labels") or []}
        try:
            if not has_label:  # a re-run after --max-writes / a stop does not add the label twice
                w.write(k, n, "labels+", "", ns.close_label, lambda: runner.api_json(
                    f"repos/{ns.repo}/issues/{n}/labels", "POST", {"labels": [ns.close_label]}, write=True))
            w.write(k, n, "state", e["state"], "CLOSED", lambda: runner.api_json(
                f"repos/{ns.repo}/issues/{n}", "PATCH", {"state": "closed", "state_reason": "not_planned"}, write=True))
        except BatchLimit:
            return batch_stop(ns, k)
    return 0
