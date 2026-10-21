"""Idempotent push executor. dry=True counts/prints every write without calling gh.

Per item (epic -> story -> task): create issue (if key absent) -> link to parent as
sub-issue -> add to Project -> fill initial fields that are still empty.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable, Dict, List, Optional

from backlog_model import BodyContext, ordered, render_body
from gh_runner import EXIT_RATE_LIMIT_STOP, GhError, RateLimitStop
from key_map import save_key_map
from project_fields import add_item, set_item_field

LABEL_COLORS = {"種別": "5319e7", "層": "0e8a16", "制約": "d93f0b"}


def existing_labels(runner, repo: str) -> List[str]:
    """Every label of the repo (paginated; a repo can hold more than 100 labels)."""
    names, page = [], 1
    while True:
        chunk = runner.api_json(f"repos/{repo}/labels?per_page=100&page={page}") or []
        names += [x["name"] for x in chunk]
        if len(chunk) < 100:
            return names
        page += 1


class BatchLimit(Exception):
    """--max-writes reached; re-run the same command to continue."""


class PushExecutor:
    def __init__(self, runner, ctx: BodyContext, kmap: Dict[str, dict], fmap: Optional[dict],
                 values: Dict[str, dict], log, dry: bool, max_writes: Optional[int] = None,
                 key_map_path: Optional[str] = None, initial: Optional[Dict[str, Callable]] = None,
                 printer: Callable[[str], None] = print):
        self.runner, self.ctx, self.kmap, self.fmap, self.values = runner, ctx, kmap, fmap, values
        self.log, self.dry, self.max_writes, self.key_map_path = log, dry, max_writes, key_map_path
        self.initial = initial or {}
        self.counts: Counter = Counter()
        self.print = printer
        self.current: Optional[str] = None
        self._seq = 0
        self._op = ""  # op id of the write in flight (write-ahead row), closed by _done

    # -- write gate: pending row -> gh write -> done row (by the step) / failed row ----------
    def _write(self, kind: str, key: Optional[str], desc: str, fn: Callable):
        if self.max_writes is not None and sum(self.counts.values()) >= self.max_writes:
            raise BatchLimit(key or "")
        self.counts[kind] += 1
        if self.dry:
            self.print(f"[dry-run] {kind:13} {key or '-':14} {desc}")
            return None
        number = (self.kmap.get(key) or {}).get("number") if key else ""
        self._op = self.log.begin(key, number, kind, "", desc)
        try:
            return fn()
        except GhError as e:  # record the failed write with its exit code, then stop
            code = EXIT_RATE_LIMIT_STOP if isinstance(e, RateLimitStop) else e.code
            self.log.write(key, number, kind, "", desc, exit_code=code, op=self._op)
            self._save()
            raise

    def _done(self, key, number, field: str, new) -> None:
        self.log.write(key, number, field, "", new, op=self._op)

    def _save(self) -> None:
        if not self.dry and self.key_map_path:
            save_key_map(self.key_map_path, self.ctx.repo, self.kmap)

    # -- steps ------------------------------------------------------------
    def ensure_labels(self, needed: List[str], existing: List[str]) -> None:
        have = {n.casefold() for n in existing}  # GitHub label names are case-insensitive
        for name in needed:
            if name.casefold() in have:
                continue
            color = LABEL_COLORS.get(name.split(":")[0], "ededed")
            self._write("label-create", None, name, lambda n=name, c=color: self.runner.api_json(
                f"repos/{self.ctx.repo}/labels", "POST", {"name": n, "color": c}, write=True))
            if not self.dry:
                self._done("", "", "label", name)

    def create_issue(self, item: dict) -> None:
        key = item["key"]
        self.ctx.numbers = {k: e["number"] for k, e in self.kmap.items() if e.get("number")}
        body = {"title": item["titleJa"], "body": render_body(item, self.ctx), "labels": item.get("labels") or []}
        res = self._write("issue-create", key, item["titleJa"], lambda: self.runner.api_json(
            f"repos/{self.ctx.repo}/issues", "POST", body, write=True))
        self._seq += 1
        if self.dry:
            self.kmap[key] = {"number": None, "dryRef": f"new{self._seq}", "projectItemId": None, "parentNumber": None}
            return
        self.kmap[key] = {"number": res["number"], "id": res["id"], "nodeId": res["node_id"], "state": "OPEN",
                          "parentNumber": None, "labels": sorted(body["labels"]), "projectItemId": None}
        self._done(key, res["number"], "issue", f"#{res['number']}")
        self._save()

    def link_parent(self, item: dict) -> None:
        key, pkey = item["key"], item.get("parentKey")
        if not pkey:
            return
        child, parent = self.kmap[key], self.kmap.get(pkey)
        if parent is None:
            raise RuntimeError(f"{key}: 親 {pkey} が未作成です（先に親の level を実行）")
        if child.get("parentNumber") and child["parentNumber"] == parent.get("number"):
            return
        if child.get("parentNumber"):
            self.print(f"WARN {key}: 既に別の親 #{child['parentNumber']} の sub-issue です（変更しません）")
            return
        pnum = parent.get("number") or parent.get("dryRef")
        self._write("sub-issue", key, f"親 #{pnum}", lambda: self.runner.api_json(
            f"repos/{self.ctx.repo}/issues/{parent['number']}/sub_issues", "POST",
            {"sub_issue_id": child["id"]}, write=True))
        if not self.dry:
            child["parentNumber"] = parent["number"]
            self._done(key, child["number"], "parent", f"#{parent['number']}")
            self._save()

    def add_to_project(self, item: dict) -> None:
        entry = self.kmap[item["key"]]
        if entry.get("projectItemId"):
            return
        item_id = self._write("project-add", item["key"], "Project に追加",
                              lambda: add_item(self.runner, self.fmap["projectId"], entry["nodeId"]))
        if not self.dry:
            entry["projectItemId"] = item_id
            self._done(item["key"], entry["number"], "project-item", item_id)
            self._save()

    def fill_fields(self, item: dict) -> None:
        entry = self.kmap[item["key"]]
        current = self.values.get(entry.get("projectItemId") or "", {})
        for field, getter in self.initial.items():
            value = getter(item)
            if value in (None, "") or current.get(field) not in (None, ""):
                continue
            self._write("field-set", item["key"], f"{field} = {value}", lambda f=field, v=value: set_item_field(
                self.runner, self.fmap, entry["projectItemId"], f, v))
            if not self.dry:
                self._done(item["key"], entry["number"], field, value)

    def run(self, items: List[dict]) -> None:
        for item in ordered(items):
            self.current = item["key"]
            if item["key"] not in self.kmap:
                self.create_issue(item)
            self.link_parent(item)
            self.add_to_project(item)
            self.fill_fields(item)
        self.current = None
