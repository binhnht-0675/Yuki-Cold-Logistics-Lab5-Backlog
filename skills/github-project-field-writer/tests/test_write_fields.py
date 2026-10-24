"""Offline tests for write-fields.py (fake gh, fictional estimate-swp fixture)."""
import csv
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SKILLS = os.path.dirname(SKILL)
sys.path.insert(0, os.path.join(SKILLS, "_shared", "tests"))
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "write-fields.py")
PUSH = os.path.join(SKILLS, "github-project-backlog-push", "scripts", "push-backlog.py")
SNAPSHOT = os.path.join(SKILLS, "github-project-progress-report", "scripts", "progress-report.py")
BACKLOG = os.path.join(SKILLS, "github-project-backlog-push", "assets", "example-backlog.json")
FIX = os.path.join(SKILLS, "_shared", "tests", "fixtures")
HTML = os.path.join(FIX, "example-estimate-swp-original.html")
SPRINT = os.path.join(SKILL, "assets", "example-sprint-plan.json")
LIVE = ["--repo", REPO, "--project", "9"]
REVIEWED = ["--reviewed-by", "reviewer-a", "--reviewed-at", "2030-01-03"]


class FieldWriterBase(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        r = self.gh.run(PUSH, ["apply", "--apply", "--backlog", BACKLOG, "--state-dir", self.state] + LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.rule = self.gh.path("hour-rule.json")
        with open(self.rule, "w", encoding="utf-8") as fh:
            json.dump({"k": 1.5, "f": 1.0, "round": 0.5}, fh)
        self.cs = self.gh.path("cs.json")

    def wf(self, *args):
        return self.gh.run(SCRIPT, list(args) + ["--state-dir", self.state])

    def build(self, html=HTML, reviewed=True):
        r = self.wf("build-from-estimate-swp", "--html", html, "--backlog", BACKLOG, "--hour-rule", self.rule,
                    "--repo", REPO, "--change-set", self.cs, *(REVIEWED if reviewed else []))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.cs, encoding="utf-8") as fh:
            return {c["key"]: c for c in json.load(fh)["changes"]}, r.stdout

    def values(self):
        st = self.gh.load()
        num_key = {i["number"]: i for i in st["issues"]}
        return {num_key[it["issueNumber"]]["title"]: it["values"] for it in st["project"]["items"]}

    def log_of(self, stdout):
        """Path of the per-run log printed by apply（ログ: …）."""
        return stdout.rsplit("（ログ: ", 1)[1].split("）", 1)[0]


class WriteFieldsTest(FieldWriterBase):

    def test_build_leaf_and_parent_sums(self):
        ch, out = self.build()
        self.assertNotIn("WARN", out)
        self.assertEqual(ch["E01-I01-S01"]["fields"], {"SWP": 5, "見積時間(h)": 7.5})
        self.assertEqual(ch["E01-I02-S01"]["fields"], {"SWP": 8, "見積時間(h)": 12})
        self.assertEqual(ch["E01-I01"]["fields"], {"SWP": 11, "見積時間(h)": 16.5})
        self.assertEqual(ch["E01"]["fields"], {"SWP": 21, "見積時間(h)": 31.5})
        self.assertEqual(ch["E01"]["derived"], "sum-of-children")

    def test_fixed_hours_override_the_formula_for_listed_leaves(self):
        with open(self.rule, "w", encoding="utf-8") as fh:
            json.dump({"k": 1.5, "f": 1.0, "round": 0.5, "fixedHours": {"E01-I01-S01": 2}}, fh)
        ch, out = self.build()
        self.assertNotIn("WARN", out)
        self.assertEqual(ch["E01-I01-S01"]["fields"], {"SWP": 5, "見積時間(h)": 2})
        self.assertEqual(ch["E01-I01"]["fields"], {"SWP": 11, "見積時間(h)": 11})
        self.assertEqual(ch["E01"]["fields"], {"SWP": 21, "見積時間(h)": 26})

    def test_fixed_hours_for_a_key_that_is_not_a_leaf_blocks(self):
        with open(self.rule, "w", encoding="utf-8") as fh:
            json.dump({"k": 1.5, "f": 1.0, "fixedHours": {"E01-I01": 2, "E99-I01-S01": 2}}, fh)
        self.build()
        with open(self.cs, encoding="utf-8") as fh:
            errors = json.load(fh)["blockingErrors"]
        self.assertTrue(any("E01-I01" in e and "fixedHours" in e for e in errors), errors)
        self.assertTrue(any("E99-I01-S01" in e and "fixedHours" in e for e in errors), errors)

    def test_diff_offline_apply_idempotent_and_revert(self):
        self.build()
        snap = self.gh.path("snap.json")
        self.gh.run(SNAPSHOT, ["snapshot", "--owner", "example-org", "--project", "9", "--repo", REPO,
                               "--key-map", os.path.join(self.state, "key-map.json"), "--snapshot", snap])
        n0 = len(self.gh.writes())
        r = self.wf("diff", "--change-set", self.cs, "--snapshot", snap)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("'変更': 16", r.stdout)
        self.assertIn("| E01 | 1 | SWP | （空） | 21 | 変更 |", r.stdout)
        r = self.wf("apply", "--change-set", self.cs, *LIVE)
        self.assertIn("dry-run", r.stdout)
        self.assertEqual(len(self.gh.writes()), n0)
        r = self.wf("apply", "--change-set", self.cs, "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        first_apply = r.stdout
        v = self.values()
        self.assertEqual(v["図書の貸出（架空サンプル）"]["SWP"], 21)
        self.assertEqual(v["返却 API"]["見積時間(h)"], 12)
        n1 = len(self.gh.writes())
        self.assertEqual(n1 - n0, 16)
        r = self.wf("apply", "--change-set", self.cs, "--apply", *LIVE)
        self.assertIn("'変更': 0", r.stdout)
        self.assertEqual(len(self.gh.writes()), n1)
        log = self.log_of(first_apply)
        with open(log, encoding="utf-8") as fh:
            rows = [row for row in csv.DictReader(fh) if not row["field"].startswith("#")]
        self.assertEqual(sum(row["status"] == "done" for row in rows), 16)
        self.assertEqual(sum(row["status"] == "pending" for row in rows), 16, "every write is announced first")
        rv = self.gh.path("revert.json")
        r = self.wf("revert-from-log", "--from-log", log, "--change-set", rv, "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(all("SWP" not in x and "見積時間(h)" not in x for x in self.values().values()))

    def test_sprint_plan_status_close_label_comment(self):
        r = self.wf("build-from-sprint-plan", "--plan", SPRINT, "--change-set", self.cs)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.wf("apply", "--change-set", self.cs, "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = self.gh.load()
        by_title = {i["title"]: i for i in st["issues"]}
        self.assertEqual(by_title["貸出テーブルを追加"]["state"], "CLOSED")
        self.assertIn("持ち越し", by_title["貸出登録画面の実装"]["labels"])
        self.assertEqual(self.values()["返却 API"]["Status"], "ブロック中")
        self.assertEqual(self.values()["貸出登録画面の実装"]["スプリント"], "スプリント 2")
        self.assertEqual(len(st["comments"]), 1)
        self.wf("apply", "--change-set", self.cs, "--apply", *LIVE)
        self.assertEqual(len(self.gh.load()["comments"]), 1, "comment must not be posted twice")

    def test_missing_child_skips_parent_and_mismatch_warns(self):
        with open(HTML, encoding="utf-8") as fh:
            html = fh.read()
        html = html.replace('"issueRef":"example-org/sample-repo#8"', '"issueRef":"other/repo#8"')
        html = html.replace('"finalSWP":11', '"finalSWP":12')
        alt = self.gh.path("alt.html")
        with open(alt, "w", encoding="utf-8") as fh:
            fh.write(html)
        ch, out = self.build(alt)
        self.assertIn("対象外の issueRef: other/repo#8", out)
        self.assertIn("E01-I02: 子の値がそろわない", out)
        self.assertIn("E01-I01: 親の合計 11.0 がレポートの 12 と一致しません", out)
        self.assertNotIn("E01-I02", ch)
        self.assertNotIn("E01", ch)

    def test_unknown_field_rejected(self):
        with open(self.cs, "w", encoding="utf-8") as fh:
            json.dump({"schema": "change-set/1", "changes": [{"key": "E01", "fields": {"存在しない": 1}}]}, fh)
        r = self.wf("apply", "--change-set", self.cs, "--apply", *LIVE)
        self.assertEqual(r.returncode, 2)
        self.assertIn("Project にないフィールド", r.stdout)

    def test_rate_limit_stop_logs_and_resumes(self):
        self.build()
        self.gh.inject_failure("updateProjectV2ItemFieldValue", 50, "GraphQL: was submitted too quickly")
        r = self.wf("apply", "--change-set", self.cs, "--apply", *LIVE, "--log", self.gh.path("run.csv"))
        self.assertEqual(r.returncode, 75, r.stdout + r.stderr)
        with open(self.gh.path("run.csv"), encoding="utf-8") as fh:
            rows = [row for row in csv.DictReader(fh) if not row["field"].startswith("#")]
        self.assertEqual([(row["status"], row["exit_code"]) for row in rows], [("pending", ""), ("failed", "75")])
        self.assertEqual(rows[0]["op"], rows[1]["op"])
        st = self.gh.load()
        st["fail"] = []
        self.gh.save(st)
        r = self.wf("apply", "--change-set", self.cs, "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.values()["図書の貸出（架空サンプル）"]["SWP"], 21)


if __name__ == "__main__":
    unittest.main()
