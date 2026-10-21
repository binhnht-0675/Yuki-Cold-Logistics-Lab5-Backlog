"""update-body / close-and-mark: --max-writes, failed log rows with exit code, closed issues left alone."""
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
KEYS = ("E01-I02-S01", "E01-I02-S02")


class MaintenanceSafetyTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        r = self.gh.run(SCRIPT, ["apply", "--backlog", EXAMPLE, "--repo", REPO, "--project", "9",
                                 "--state-dir", self.state, "--apply"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def issue(self, key):
        return next(i for i in self.gh.load()["issues"] if f"backlog-key: {key} " in i["body"])

    def close(self, *extra):
        return self.gh.run(SCRIPT, ["close-and-mark", "--repo", REPO, "--state-dir", self.state,
                                    "--keys", ",".join(KEYS), "--apply"] + list(extra))

    def log_rows(self):
        with open(os.path.join(self.state, "push-log.csv"), encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def test_close_and_mark_leaves_an_already_closed_issue_alone(self):
        st = self.gh.load()
        done = next(i for i in st["issues"] if f"backlog-key: {KEYS[0]} " in i["body"])
        done["state"] = "CLOSED"  # e.g. closed as completed after the sprint
        self.gh.save(st)
        n = len(self.gh.writes())
        r = self.close()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"WARN {KEYS[0]}", r.stdout)
        self.assertNotIn("廃止", self.issue(KEYS[0])["labels"])
        self.assertEqual(len(self.gh.writes()), n + 2, "only the open issue gets label + close")
        self.assertFalse(any(f"/{done['number']}" in " ".join(c["args"]) for c in self.gh.writes()[n:]))
        r = self.close("--include-closed")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("廃止", self.issue(KEYS[0])["labels"])

    def test_close_and_mark_respects_max_writes_and_resumes_without_repeats(self):
        n = len(self.gh.writes())
        codes = []
        for _ in range(8):
            codes.append(self.close("--max-writes", "1").returncode)
            if codes[-1] == 0:
                break
        self.assertEqual(codes[0], 10)
        self.assertEqual(codes[-1], 0)
        self.assertEqual(len(self.gh.writes()), n + 4, "2 keys x (label + close), nothing repeated")
        for k in KEYS:
            self.assertEqual(self.issue(k)["state"], "CLOSED")
            self.assertIn("廃止", self.issue(k)["labels"])

    def test_update_body_respects_max_writes(self):
        st = self.gh.load()
        for i in st["issues"]:
            if any(f"backlog-key: {k} " in i["body"] for k in KEYS):
                i["body"] += "\n手で追記"
        self.gh.save(st)
        n = len(self.gh.writes())
        r = self.gh.run(SCRIPT, ["update-body", "--backlog", EXAMPLE, "--repo", REPO, "--state-dir", self.state,
                                 "--keys", ",".join(KEYS), "--force-body", "--apply", "--max-writes", "1"])
        self.assertEqual(r.returncode, 10, r.stdout + r.stderr)
        self.assertEqual(len(self.gh.writes()), n + 1)

    def test_close_and_mark_rate_limit_stop_logs_failed_row_75(self):
        self.gh.inject_failure(f"issues/{self.issue(KEYS[0])['number']}/labels", 99, LIMIT_MSG)
        r = self.close()
        self.assertEqual(r.returncode, 75, r.stdout + r.stderr)
        rows = [x for x in self.log_rows() if x["command"] == "close-and-mark"]
        self.assertEqual([(x["status"], x["exit_code"]) for x in rows], [("pending", ""), ("failed", "75")])

    def test_update_body_error_logs_failed_row_with_exit_code(self):
        num = self.issue(KEYS[0])["number"]
        st = self.gh.load()
        next(i for i in st["issues"] if i["number"] == num)["body"] += "\n手で追記"
        self.gh.save(st)
        self.gh.inject_failure(f"issues/{num} --method PATCH", 1, "HTTP 422: Validation Failed", code=1)
        r = self.gh.run(SCRIPT, ["update-body", "--backlog", EXAMPLE, "--repo", REPO, "--state-dir", self.state,
                                 "--keys", KEYS[0], "--force-body", "--apply"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        rows = [x for x in self.log_rows() if x["command"] == "update-body"]
        self.assertEqual([(x["status"], x["exit_code"]) for x in rows], [("pending", ""), ("failed", "1")])


if __name__ == "__main__":
    unittest.main()
