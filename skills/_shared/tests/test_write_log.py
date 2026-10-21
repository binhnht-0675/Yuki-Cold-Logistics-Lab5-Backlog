"""write_log: write-ahead rows, legacy (9-column) logs, and a crash of skill 1 between write and log."""
import csv
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402
from write_log import COLUMNS, LEGACY_COLUMNS, WriteLog, outcome_rows, read_log, unresolved  # noqa: E402

PUSH = os.path.join(SKILLS, "github-project-backlog-push", "scripts", "push-backlog.py")
BACKLOG = os.path.join(SKILLS, "github-project-backlog-push", "assets", "example-backlog.json")


class WriteLogTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.path = self.gh.path("log.csv")

    def test_pending_row_is_on_disk_before_the_write_and_closed_by_its_op(self):
        log = WriteLog(self.path, "s", "apply")
        op = log.begin("K1", 3, "comment", "", "abcd1234")
        rows = list(read_log(self.path))
        self.assertEqual([(r["status"], r["exit_code"]) for r in rows], [("pending", "")])
        self.assertEqual(unresolved(rows), rows)
        log.write("K1", 3, "comment", "", "abcd1234", op=op, ref=501)
        log.begin("K2", 4, "SWP", "", "5")  # the process "dies" here
        rows = list(read_log(self.path))
        self.assertEqual([r["key"] for r in unresolved(rows)], ["K2"])
        self.assertEqual([(r["key"], r["status"], r["ref"]) for r in outcome_rows(rows)],
                         [("K1", "done", "501"), ("K2", "pending", "")])

    def test_failed_write_closes_its_pending_row(self):
        log = WriteLog(self.path, "s", "apply")
        op = log.begin("K", 1, "SWP", "", "5")
        log.write("K", 1, "SWP", "", "5", exit_code=75, op=op)
        rows = list(read_log(self.path))
        self.assertEqual(unresolved(rows), [])
        self.assertEqual([r["status"] for r in outcome_rows(rows)], ["failed"])

    def legacy_log(self):
        with open(self.path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(LEGACY_COLUMNS)
            w.writerow(["t", "s", "apply", "K", "1", "SWP", "", "5", "0"])
            w.writerow(["t", "s", "apply", "K", "1", "Status", "", "x", "75"])

    def test_legacy_log_is_read_without_rewrite(self):
        self.legacy_log()
        rows = list(read_log(self.path))
        self.assertEqual([(r["status"], r["op"], r["ref"]) for r in rows], [("done", "", ""), ("failed", "", "")])
        self.assertEqual(unresolved(rows), [])
        with open(self.path, encoding="utf-8") as fh:
            self.assertEqual(fh.readline().strip(), ",".join(LEGACY_COLUMNS), "reading never changes the file")

    def test_appending_to_legacy_log_upgrades_header_and_keeps_rows(self):
        self.legacy_log()
        WriteLog(self.path, "s", "apply").write("K", 1, "SWP", "5", "6")
        with open(self.path, newline="", encoding="utf-8") as fh:
            raw = list(csv.reader(fh))
        self.assertEqual(raw[0], COLUMNS)
        self.assertTrue(all(len(r) == len(COLUMNS) for r in raw))
        self.assertEqual([r["status"] for r in read_log(self.path)], ["done", "failed", "done"])

    def test_formula_like_cells_are_quoted_and_read_back_unchanged(self):
        """L-7: a title such as =HYPERLINK(...) must not run as a formula when the CSV is opened."""
        values = ["=HYPERLINK(\"x\")", "+1", "-2", "@SUM(A1)", "'=x", "''", "'a", "plain", ""]
        log = WriteLog(self.path, "s", "apply")
        for v in values:
            log.write("K", 1, "title", v, v)
        with open(self.path, newline="", encoding="utf-8") as fh:
            raw = list(csv.DictReader(fh))
        self.assertTrue(all(r["new"][:1] not in tuple("=+-@") for r in raw), [r["new"] for r in raw])
        self.assertEqual([r["new"] for r in read_log(self.path)], values)
        self.assertEqual([r["old"] for r in read_log(self.path)], values)


class BacklogPushCrashTest(unittest.TestCase):
    """Skill 1: killed right after an issue was created -> the pending row says so; a re-run makes no duplicate."""

    def test_crash_after_issue_create_leaves_pending_row_and_rerun_is_clean(self):
        gh = FakeGitHub()
        state = gh.path("state")
        os.makedirs(state)
        with open(os.path.join(state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(gh.field_map(), fh, ensure_ascii=False)
        args = ["apply", "--apply", "--backlog", BACKLOG, "--state-dir", state, "--repo", REPO, "--project", "9"]
        gh.inject_crash(f"repos/{REPO}/issues --method POST")
        self.assertNotEqual(gh.run(PUSH, args).returncode, 0)
        log = os.path.join(state, "push-log.csv")
        left = unresolved(list(read_log(log)))
        self.assertEqual([(r["key"], r["field"]) for r in left], [("E01", "issue-create")])
        r = gh.run(PUSH, args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(gh.load()["issues"]), 8, "the issue made before the crash is found by its key")


if __name__ == "__main__":
    unittest.main()
