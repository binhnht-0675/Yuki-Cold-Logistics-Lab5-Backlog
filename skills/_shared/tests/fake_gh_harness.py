"""Test harness: build a fictional fake-GitHub state and run a skill script against fake-gh."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from typing import List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE_GH = os.path.join(HERE, "fake-gh.py")
REPO = "example-org/sample-repo"
ROLES = ["BE-1", "BE-2", "FE-1", "FE-2", "QA-1", "QA-2", "Infra-1", "PM", "BrSE"]


def default_fields() -> dict:
    return {
        "Status": {"id": "F_STATUS", "type": "single_select",
                   "options": {n: "o%d" % i for i, n in enumerate(["未着手", "進行中", "完了", "ブロック中"])}},
        "スプリント": {"id": "F_ITER", "type": "iteration",
                   "iterations": {"スプリント 1": "it1", "スプリント 2": "it2", "スプリント 3": "it3"}},
        "SWP": {"id": "F_SWP", "type": "number"},
        "見積時間(h)": {"id": "F_HOURS", "type": "number"},
        "担当（仮）": {"id": "F_ROLE", "type": "single_select", "options": {r: "r%d" % i for i, r in enumerate(ROLES)}},
    }


class FakeGitHub:
    def __init__(self, page_size: int = 100):
        self.dir = tempfile.mkdtemp(prefix="fake-gh-")
        self.state_path = os.path.join(self.dir, "state.json")
        self.log_path = os.path.join(self.dir, "calls.jsonl")
        self.save({"repo": REPO, "issues": [], "labels": [], "page_size": page_size, "fail": [],
                   "project": {"id": "PVT_fake", "title": "サンプル", "fields": default_fields(), "items": []}})
        open(self.log_path, "w").close()

    def path(self, name: str) -> str:
        return os.path.join(self.dir, name)

    def load(self) -> dict:
        with open(self.state_path, encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, st: dict) -> None:
        with open(self.state_path, "w", encoding="utf-8") as fh:
            json.dump(st, fh, ensure_ascii=False)

    def calls(self) -> List[dict]:
        with open(self.log_path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def writes(self) -> List[dict]:
        return [c for c in self.calls() if c["write"]]

    def inject_failure(self, match: str, times: int, stderr: str, code: int = 1) -> None:
        st = self.load()
        st["fail"].append({"match": match, "times": times, "stderr": stderr, "code": code})
        self.save(st)

    def inject_crash(self, match: str, when: str = "after", times: int = 1) -> None:
        """Kill the skill process right after (or before) the matching gh call reaches the fake GitHub."""
        st = self.load()
        st.setdefault("die", []).append({"match": match, "times": times, "when": when})
        self.save(st)

    def field_map(self) -> dict:
        st = self.load()
        return {"owner": "example-org", "number": 9, "projectId": st["project"]["id"],
                "fields": st["project"]["fields"]}

    def write_field_map(self) -> str:
        p = self.path("field-map.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(self.field_map(), fh, ensure_ascii=False)
        return p

    def run(self, script: str, args: List[str], extra_env: Optional[dict] = None) -> subprocess.CompletedProcess:
        env = dict(os.environ, FAKE_GH_STATE=self.state_path, FAKE_GH_LOG=self.log_path)
        env.update(extra_env or {})
        cmd = [sys.executable, script] + args + ["--gh", f"{shlex.quote(sys.executable)} {shlex.quote(FAKE_GH)}",
                                                 "--pace", "0", "--retry-wait", "0"]
        return subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
