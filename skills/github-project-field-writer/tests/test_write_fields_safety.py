"""Negative tests: apply must stop before the first write; revert must undo exactly one run."""
import json
import os
import unittest

from test_write_fields import BACKLOG, HTML, LIVE, SPRINT, FieldWriterBase  # noqa: F401


class ApplyGateTest(FieldWriterBase):
    def alt_html(self, *pairs):
        with open(HTML, encoding="utf-8") as fh:
            html = fh.read()
        for old, new in pairs:
            self.assertIn(old, html)
            html = html.replace(old, new)
        path = self.gh.path("alt.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        return path

    def apply_blocked(self, *must_contain):
        n0 = len(self.gh.writes())
        r = self.wf("apply", "--change-set", self.cs, "--apply", *LIVE)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(len(self.gh.writes()), n0, "no write may happen")
        for text in must_contain:
            self.assertIn(text, r.stdout)
        return r

    def test_missing_leaf_blocks_apply(self):
        self.build(self.alt_html(('"issueRef":"example-org/sample-repo#8"', '"issueRef":"other/repo#8"')),
                   reviewed=False)
        self.apply_blocked("SWP がない")

    def test_report_parent_mismatch_blocks_apply(self):
        self.build(self.alt_html(('"finalSWP":11', '"finalSWP":12')), reviewed=False)
        self.apply_blocked("一致しません")

    def test_hand_edited_leaf_breaks_parent_sum_and_blocks_apply(self):
        self.build(reviewed=False)
        with open(self.cs, encoding="utf-8") as fh:
            cs = json.load(fh)
        cs.pop("blockingErrors", None)
        for c in cs["changes"]:
            if c["key"] == "E01-I01-S01":
                c["fields"]["SWP"] = 99
        with open(self.cs, "w", encoding="utf-8") as fh:
            json.dump(cs, fh, ensure_ascii=False)
        self.apply_blocked("子の合計")

    def test_unreviewed_report_blocks_apply_and_review_is_logged(self):
        self.build(reviewed=False)
        self.apply_blocked("--reviewed-by")
        self.build()
        r = self.wf("apply", "--change-set", self.cs, "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.cs, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["source"]["review"]["reviewedBy"], "reviewer-a")
        with open(self.log_of(r.stdout), encoding="utf-8") as fh:
            self.assertIn("reviewedBy=reviewer-a", fh.read())

    def test_pending_calibration_blocks_apply(self):
        self.build(self.alt_html(('"calibrationStatus":"accepted"', '"calibrationStatus":"pending"')),
                   reviewed=False)
        self.apply_blocked("calibrationStatus")

    def test_unknown_status_option_stops_before_first_write(self):
        plan = self.gh.path("bad-plan.json")
        with open(plan, "w", encoding="utf-8") as fh:
            json.dump({"items": [{"key": "E01-I01-S01", "status": "完了"},
                                 {"key": "E01-I01-S02", "status": "存在しない状態"},
                                 {"key": "E01-I01-S03", "iteration": "スプリント 9"}]}, fh, ensure_ascii=False)
        r = self.wf("build-from-sprint-plan", "--plan", plan, "--change-set", self.cs)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.apply_blocked("選択肢にない値", "イテレーションにない値")


class RevertPerRunTest(FieldWriterBase):
    def write_cs(self, name, changes):
        path = self.gh.path(name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"schema": "change-set/1", "source": {"kind": "manual"}, "changes": changes}, fh,
                      ensure_ascii=False)
        return path

    def apply(self, cs):
        r = self.wf("apply", "--change-set", cs, "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return self.log_of(r.stdout)

    def test_revert_sprint_run_keeps_earlier_swp_run(self):
        self.build()  # SWP comes from a reviewed estimate run (a leaf alone would break parent = sum)
        swp_log = self.apply(self.cs)
        sprint_cs = self.gh.path("cs-sprint.json")
        r = self.wf("build-from-sprint-plan", "--plan", SPRINT, "--change-set", sprint_cs)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        sprint_log = self.apply(sprint_cs)
        self.assertNotEqual(swp_log, sprint_log)
        r = self.wf("revert-from-log", "--from-log", sprint_log, "--change-set", self.gh.path("rv.json"),
                    "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        v = self.values()
        self.assertEqual(v["貸出テーブルを追加"]["SWP"], 5, "SWP of the earlier run must survive")
        self.assertEqual(v["貸出テーブルを追加"]["Status"], "未着手", "Status goes back to its value before the run")
        st = {i["title"]: i for i in self.gh.load()["issues"]}
        self.assertEqual(st["貸出テーブルを追加"]["state"], "OPEN", "close is undone")
        self.assertNotIn("持ち越し", st["貸出登録画面の実装"]["labels"], "added label is removed")
        self.assertEqual(self.gh.load()["comments"], [], "the posted comment is deleted by its id")

    def test_revert_re_adds_removed_label(self):
        self.apply(self.write_cs("cs-add.json", [{"key": "E01-I01-S02", "addLabels": ["確認用"]}]))
        log = self.apply(self.write_cs("cs-rm.json", [{"key": "E01-I01-S02", "removeLabels": ["確認用"]}]))
        self.assertFalse(any("確認用" in i["labels"] for i in self.gh.load()["issues"]))
        r = self.wf("revert-from-log", "--from-log", log, "--change-set", self.gh.path("rv.json"), "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any("確認用" in i["labels"] for i in self.gh.load()["issues"]))

    def test_diff_says_comment_can_be_deleted_by_revert(self):
        r = self.wf("build-from-sprint-plan", "--plan", SPRINT, "--change-set", self.cs)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.wf("diff", "--change-set", self.cs, *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("revert-from-log で削除できます", r.stdout)


if __name__ == "__main__":
    unittest.main()
