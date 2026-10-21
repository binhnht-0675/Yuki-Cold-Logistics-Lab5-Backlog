"""Offline tests for progress-report.py (fake gh + fictional sample snapshot)."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SKILLS = os.path.dirname(SKILL)
sys.path.insert(0, os.path.join(SKILLS, "_shared", "tests"))
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "progress-report.py")
PUSH = os.path.join(SKILLS, "github-project-backlog-push", "scripts", "push-backlog.py")
EXAMPLE_BACKLOG = os.path.join(SKILLS, "github-project-backlog-push", "assets", "example-backlog.json")
SNAP = os.path.join(SKILL, "assets", "example-snapshot.json")
DAYS = os.path.join(SKILL, "assets", "example-sprint-days.json")


class SnapshotFromFakeProjectTest(unittest.TestCase):
    def test_snapshot_reads_project_without_writes(self):
        gh = FakeGitHub(page_size=3)
        state = gh.path("state")
        os.makedirs(state)
        with open(os.path.join(state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(gh.field_map(), fh, ensure_ascii=False)
        r = gh.run(PUSH, ["apply", "--apply", "--backlog", EXAMPLE_BACKLOG, "--repo", REPO, "--project", "9",
                          "--state-dir", state])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = gh.load()
        for it in st["project"]["items"]:
            it["values"]["SWP"] = 3
        gh.save(st)
        n_writes = len(gh.writes())
        out = gh.path("snap.json")
        r = gh.run(SCRIPT, ["snapshot", "--owner", "example-org", "--project", "9", "--repo", REPO,
                            "--key-map", os.path.join(state, "key-map.json"), "--snapshot", out])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(gh.writes()), n_writes, "snapshot must be read-only")
        with open(out, encoding="utf-8") as fh:
            snap = json.load(fh)
        self.assertEqual(len(snap["items"]), 8)
        keys = {i["key"] for i in snap["items"]}
        self.assertIn("E01-I02-S02", keys)
        self.assertTrue(all("body" not in i for i in snap["items"]))
        task = next(i for i in snap["items"] if i["key"] == "E01-I01-S02")
        story = next(i for i in snap["items"] if i["key"] == "E01-I01")
        self.assertEqual(task["parentNumber"], story["number"])
        self.assertEqual(task["fields"]["担当（仮）"], "BE-2")


class TablesTest(unittest.TestCase):
    def run_tables(self, *extra):
        gh = FakeGitHub()
        return gh.run(SCRIPT, ["tables", "--snapshot", SNAP] + list(extra))

    def test_status_table_counts_leaves_only(self):
        r = self.run_tables("--format", "json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = json.loads(r.stdout)
        st = {s["status"]: s for s in res["status"]}
        self.assertEqual(res["source"]["items"], 5)  # 5 tasks, parents excluded
        self.assertEqual(st["完了"]["count"], 2)
        self.assertEqual(st["完了"]["swp"], 8)
        self.assertEqual(st["完了"]["note"], "クローズ済み 2")
        self.assertEqual(st["ブロック中"]["count"], 1)
        self.assertEqual(sum(s["swp"] for s in res["status"]), 21)
        self.assertEqual(res["epics"][0]["swp"], 21)
        self.assertEqual(res["epics"][0]["doneSwp"], 8)

    def test_markdown_has_japanese_tables(self):
        r = self.run_tables("--iteration", "スプリント 1", "--sprint-days", DAYS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("| ステータス | issue 数 | SWP 合計 | 備考 |", r.stdout)
        self.assertIn("| **合計** | 4 | 18 |  |", r.stdout)  # S03 is in sprint 2
        self.assertIn("### バーンダウン（模擬）", r.stdout)
        self.assertIn("| 2030-01-10 | 0 | 10 | 0 |", r.stdout)

    def test_burndown_numbers(self):
        r = self.run_tables("--iteration", "スプリント 1", "--sprint-days", DAYS, "--format", "json")
        bd = json.loads(r.stdout)["burndown"]
        self.assertEqual(len(bd), 10)
        self.assertEqual(bd[0]["ideal"], 16.2)
        self.assertEqual(bd[2]["remaining"], 13)   # E01-I01-S01 (5) done on day 3
        self.assertEqual(bd[-1]["remaining"], 10)  # 8 done of 18

    def test_unknown_completed_key_is_rejected(self):
        gh = FakeGitHub()
        bad = gh.path("days.json")
        with open(bad, "w", encoding="utf-8") as fh:
            json.dump({"days": ["2030-01-01"], "completed": {"E99": "2030-01-01"}}, fh)
        r = gh.run(SCRIPT, ["tables", "--snapshot", SNAP, "--sprint-days", bad])
        self.assertEqual(r.returncode, 2)
        self.assertIn("E99", r.stdout)


if __name__ == "__main__":
    unittest.main()
