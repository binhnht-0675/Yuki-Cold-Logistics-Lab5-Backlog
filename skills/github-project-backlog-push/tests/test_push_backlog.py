"""Offline tests for push-backlog.py against the fake gh (fictional data only)."""
import csv
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "..", "_shared", "tests"))
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "push-backlog.py")
EXAMPLE = os.path.join(SKILL, "assets", "example-backlog.json")
LIMIT_MSG = "HTTP 403: You have exceeded a secondary rate limit. Please wait a few minutes."


class PushBacklogTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)

    def push(self, *extra, page_size=None):
        if page_size:
            self.gh.save(dict(self.gh.load(), page_size=page_size))
        return self.gh.run(SCRIPT, ["apply", "--backlog", EXAMPLE, "--repo", REPO, "--project", "9",
                                    "--state-dir", self.state] + list(extra))

    def issues(self):
        return self.gh.load()["issues"]

    def test_plan_is_offline_and_counts(self):
        r = self.gh.run(SCRIPT, ["plan", "--backlog", EXAMPLE, "--repo", REPO, "--state-dir", self.state])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("作成予定 issue: 8（epic 1 / story 2 / task 5）", r.stdout)
        self.assertIn("sub-issue: 7", r.stdout)
        self.assertIn("project-add: 8", r.stdout)
        self.assertEqual(self.gh.calls(), [])

    def test_apply_without_flag_writes_nothing(self):
        r = self.push()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("dry-run", r.stdout)
        self.assertGreater(len(self.gh.calls()), 0)
        self.assertEqual(self.gh.writes(), [])

    def test_apply_creates_tree_in_order_and_is_idempotent(self):
        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        iss = self.issues()
        self.assertEqual(len(iss), 8)
        levels = [i["title"] for i in iss]
        self.assertEqual(levels[0], "図書の貸出（架空サンプル）")  # epic first
        self.assertEqual(set(levels[1:3]), {"貸出登録画面", "返却処理"})  # then stories
        by_title = {i["title"]: i for i in iss}
        self.assertEqual(by_title["貸出登録 API"]["parent"], by_title["貸出登録画面"]["number"])
        self.assertEqual(by_title["返却処理"]["parent"], by_title["図書の貸出（架空サンプル）"]["number"])
        items = self.gh.load()["project"]["items"]
        self.assertEqual(len(items), 8)
        self.assertTrue(all(it["values"].get("Status") == "未着手" for it in items))
        roles = {it["issueNumber"]: it["values"].get("担当（仮）") for it in items}
        self.assertEqual(roles[by_title["返却の結合テスト"]["number"]], "QA-1")
        self.assertIn("<!-- backlog-key: E01-I02-S02 -->", by_title["返却の結合テスト"]["body"])
        self.assertEqual(sorted(self.gh.load()["labels"]), sorted({"種別:エピック", "種別:ストーリー", "種別:タスク",
                                                                  "層:DB", "層:API", "層:UI", "層:テスト"}))
        with open(os.path.join(self.state, "push-log.csv"), encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(sum(r["field"] == "issue" for r in rows), 8)
        self.assertTrue(all(r["exit_code"] == ("" if r["status"] == "pending" else "0") for r in rows))
        before = len(self.gh.writes())
        r2 = self.push("--apply", page_size=3)  # paginated re-read
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(len(self.gh.writes()), before, "second run must not write")
        self.assertEqual(len(self.issues()), 8)

    def test_secondary_rate_limit_retries_then_succeeds(self):
        self.gh.inject_failure("repos/example-org/sample-repo/issues --method POST", 2, LIMIT_MSG)
        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.issues()), 8)

    def test_rate_limit_stop_then_resume_without_duplicates(self):
        self.gh.inject_failure("sub_issues", 99, LIMIT_MSG)
        r = self.push("--apply")
        self.assertEqual(r.returncode, 75, r.stdout + r.stderr)
        self.assertIn("STOPPED", r.stdout)
        with open(os.path.join(self.state, "push-log.csv"), encoding="utf-8") as fh:
            self.assertTrue(any(row["exit_code"] == "75" for row in csv.DictReader(fh)))
        st = self.gh.load()
        st["fail"] = []
        self.gh.save(st)
        r2 = self.push("--apply")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertEqual(len(self.issues()), 8)
        self.assertEqual(sum(1 for i in self.issues() if i["parent"]), 7)

    def test_max_writes_batches_resume(self):
        r = self.push("--apply", "--max-writes", "5")
        self.assertEqual(r.returncode, 10, r.stdout + r.stderr)
        for _ in range(20):
            r = self.push("--apply", "--max-writes", "5")
            if r.returncode == 0:
                break
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len(self.issues()), 8)
        self.assertEqual(len(self.gh.load()["project"]["items"]), 8)

    def test_initial_fields_are_set_only_when_empty(self):
        self.push("--apply")
        st = self.gh.load()
        item = st["project"]["items"][0]
        item["values"]["Status"] = "進行中"  # changed by a person
        item["values"].pop("担当（仮）")  # cleared by a person
        self.gh.save(st)
        before = len(self.gh.writes())
        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.gh.writes()), before + 1)  # only the empty role is filled again
        values = self.gh.load()["project"]["items"][0]["values"]
        self.assertEqual(values["Status"], "進行中")
        self.assertIn("担当（仮）", values)

    def test_rebuild_key_map_detects_duplicate_key(self):
        self.push("--apply")
        st = self.gh.load()
        dup = dict(st["issues"][0], number=99, id=1099, nodeId="I_99")
        st["issues"].append(dup)
        self.gh.save(st)
        r = self.gh.run(SCRIPT, ["rebuild-key-map", "--repo", REPO, "--state-dir", self.state])
        self.assertEqual(r.returncode, 1)
        self.assertIn("複数", r.stdout)

    def test_update_body_resolves_dependencies_then_noop(self):
        self.push("--apply")
        args = ["update-body", "--backlog", EXAMPLE, "--repo", REPO, "--state-dir", self.state]
        n_before = len(self.gh.writes())
        r = self.gh.run(SCRIPT, args)
        self.assertIn("[dry-run]", r.stdout)
        self.assertEqual(len(self.gh.writes()), n_before, "update-body without --apply must not write")
        self.gh.run(SCRIPT, args + ["--apply"])
        self.assertGreater(len(self.gh.writes()), n_before)
        ui = next(i for i in self.issues() if i["title"] == "貸出登録画面の実装")
        ret = next(i for i in self.issues() if i["title"] == "返却 API")  # created after the UI task
        self.assertIn(f"#{ret['number']}（E01-I02-S01）", ui["body"])
        n_after = len(self.gh.writes())
        self.gh.run(SCRIPT, args + ["--apply"])
        self.assertEqual(len(self.gh.writes()), n_after)

    def test_update_body_keeps_manual_edits_unless_forced(self):
        self.push("--apply")
        st = self.gh.load()
        issue = next(i for i in st["issues"] if i["title"] == "返却 API")
        issue["body"] = issue["body"].replace("\n", "\r\n")  # same text saved from the web UI
        self.gh.save(st)
        args = ["update-body", "--backlog", EXAMPLE, "--repo", REPO, "--state-dir", self.state, "--apply",
                "--keys", "E01-I02-S01"]
        n = len(self.gh.writes())
        self.gh.run(SCRIPT, args)
        self.assertEqual(len(self.gh.writes()), n, "CRLF-only difference must not rewrite")
        st = self.gh.load()
        next(i for i in st["issues"] if i["title"] == "返却 API")["body"] += "\n手で追記"
        self.gh.save(st)
        r = self.gh.run(SCRIPT, args)
        self.assertIn("--force-body", r.stdout)
        self.assertEqual(len(self.gh.writes()), n)
        self.gh.run(SCRIPT, args + ["--force-body"])
        self.assertEqual(len(self.gh.writes()), n + 1)

    def test_close_and_mark(self):
        self.push("--apply")
        base = ["close-and-mark", "--repo", REPO, "--state-dir", self.state, "--keys", "E01-I02-S02"]
        n = len(self.gh.writes())
        self.gh.run(SCRIPT, base)
        self.assertEqual(len(self.gh.writes()), n)
        self.gh.run(SCRIPT, base + ["--apply"])
        issue = next(i for i in self.issues() if i["title"] == "返却の結合テスト")
        self.assertEqual(issue["state"], "CLOSED")
        self.assertIn("廃止", issue["labels"])

    def test_text_ref_style_has_no_links(self):
        r = self.gh.run(SCRIPT, ["plan", "--backlog", EXAMPLE, "--state-dir", self.state, "--ref-style", "text",
                                 "--edition", "2030-01-01 提出版", "--show-body", "E01-I01-S02"])
        self.assertIn("`lending/API.md` — §3 POST /loans（2030-01-01 提出版）", r.stdout)
        self.assertNotIn("https://", r.stdout)

    def test_invalid_backlog_rejected(self):
        bad = self.gh.path("bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            json.dump([{"key": "X1", "level": "task", "parentKey": "NOPE", "titleJa": "t", "bodyJa": {}}], fh)
        r = self.gh.run(SCRIPT, ["plan", "--backlog", bad, "--state-dir", self.state])
        self.assertEqual(r.returncode, 2)
        self.assertIn("親 NOPE がない", r.stdout)


if __name__ == "__main__":
    unittest.main()
