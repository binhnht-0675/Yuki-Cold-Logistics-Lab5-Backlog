"""Negative tests (review of 2026-10-20, round 2): M1 error rows stop apply before the first write,
M2 every reverted value is conditional on GitHub still holding this run's value, M3 revert handles every
label of an issue, M4 the estimate gate follows the content of the change-set, not source.kind."""
import json
import unittest

from test_write_fields import LIVE, FieldWriterBase

S01 = "貸出テーブルを追加"  # E01-I01-S01 in the sample backlog


class GuardBase(FieldWriterBase):
    def cs_file(self, name, changes, kind="manual", **source):
        path = self.gh.path(name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"schema": "change-set/1", "source": dict({"kind": kind}, **source), "changes": changes}, fh,
                      ensure_ascii=False)
        return path

    def edit_cs(self, fn):
        with open(self.cs, encoding="utf-8") as fh:
            cs = json.load(fh)
        fn(cs)
        with open(self.cs, "w", encoding="utf-8") as fh:
            json.dump(cs, fh, ensure_ascii=False)

    def apply(self, cs, *extra):
        return self.wf("apply", "--change-set", cs, "--apply", *LIVE, *extra)

    def blocked(self, cs, *must_contain):
        n0 = len(self.gh.writes())
        r = self.apply(cs)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(len(self.gh.writes()), n0, "no write may happen")
        for text in must_contain:
            self.assertIn(text, r.stdout)
        return r

    def revert(self, log):
        r = self.wf("revert-from-log", "--from-log", log, "--change-set", self.gh.path("rv.json"), "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def labels_of(self, title):
        return next(i["labels"] for i in self.gh.load()["issues"] if i["title"] == title)


class ErrorRowStopsApplyTest(GuardBase):  # M1
    def test_unknown_key_stops_whole_apply(self):
        self.build()
        self.edit_cs(lambda cs: cs["changes"].append({"key": "NOPE-1", "fields": {"Status": "完了"}}))
        self.blocked(self.cs, "Project にない", "書き込みません")

    def test_leaf_missing_from_project_writes_no_parent(self):
        self.build()
        st = self.gh.load()
        num = next(i["number"] for i in st["issues"] if i["title"] == S01)
        st["project"]["items"] = [it for it in st["project"]["items"] if it["issueNumber"] != num]
        self.gh.save(st)
        self.blocked(self.cs, "E01-I01-S01")


class RevertIfCurrentTest(GuardBase):  # M2, M3
    def test_certain_write_is_not_reverted_over_a_later_run(self):
        log = self.gh.path("run-1.csv")
        r = self.apply(self.cs_file("cs-1.json", [{"key": "E01-I01-S01", "fields": {"Status": "完了"}}]), "--log", log)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.apply(self.cs_file("cs-2.json", [{"key": "E01-I01-S01", "fields": {"Status": "進行中"}}]),
                       "--log", self.gh.path("run-2.csv"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.revert(log)
        self.assertEqual(self.values()[S01]["Status"], "進行中", "the later run's value must survive")
        self.assertIn("この実行の値ではないので戻さない", r.stdout)

    def test_revert_handles_every_label_of_an_issue(self):
        title = "貸出登録 API"
        r = self.apply(self.cs_file("cs-0.json", [{"key": "E01-I01-S02", "addLabels": ["確認X", "確認Y"]}]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log = self.gh.path("run-l.csv")
        r = self.apply(self.cs_file("cs-l.json", [{"key": "E01-I01-S02", "addLabels": ["追加A", "追加B"],
                                                   "removeLabels": ["確認X", "確認Y"]}]), "--log", log)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.revert(log)
        labels = self.labels_of(title)
        self.assertNotIn("追加A", labels)
        self.assertNotIn("追加B", labels, "every added label is removed")
        self.assertIn("確認X", labels)
        self.assertIn("確認Y", labels, "every removed label is added back")


class EstimateGateByContentTest(GuardBase):  # M4
    def unreviewed_as(self, kind):
        self.build(reviewed=False)

        def tamper(cs):
            cs["source"]["kind"] = kind
            cs.pop("blockingErrors", None)
        self.edit_cs(tamper)

    def test_kind_sprint_plan_does_not_skip_review(self):
        self.unreviewed_as("sprint-plan")
        self.blocked(self.cs, "--reviewed-by")

    def test_kind_manual_does_not_skip_review(self):
        self.unreviewed_as("manual")
        self.blocked(self.cs, "--reviewed-by")

    def test_manual_path_without_estimate_marks_writes_with_a_warning(self):
        """Review 20/10 team 1 item 1 (kept on purpose): stripping every estimate mark and setting kind=manual
        writes SWP without the review gate. apply says so, the #run log row keeps kind=manual, and
        parent = sum of children is still checked on the Project."""
        self.unreviewed_as("manual")

        def strip(cs):
            cs["source"] = {"kind": "manual"}
            for c in cs["changes"]:
                c.pop("derived", None)
                c.pop("children", None)
        self.edit_cs(strip)
        r = self.apply(self.cs)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("代表 issue のレビュー記録を検査せずに", r.stdout)
        with open(self.log_of(r.stdout), encoding="utf-8") as fh:
            run_rows = [line for line in fh if ",#run," in line]
        self.assertTrue(run_rows and all("kind=manual" in line for line in run_rows), run_rows)

    def test_hand_made_revert_kind_cannot_write_swp(self):
        self.blocked(self.cs_file("cs-rv.json", [{"key": "E01-I01-S01", "fields": {"SWP": 5}}], kind="revert"),
                     "revert-from-log")

    def test_manual_leaf_swp_without_parents_is_blocked(self):
        self.blocked(self.cs_file("cs-m.json", [{"key": "E01-I01-S01", "fields": {"SWP": 5}}]), "子の合計")

    def test_manual_swp_keeping_parent_sum_is_allowed(self):
        self.build()
        self.assertEqual(self.apply(self.cs).returncode, 0)
        cs = self.cs_file("cs-fix.json", [{"key": "E01-I01-S01", "fields": {"SWP": 6}},
                                          {"key": "E01-I01", "fields": {"SWP": 12}},
                                          {"key": "E01", "fields": {"SWP": 22}}])
        r = self.apply(cs)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.values()["図書の貸出（架空サンプル）"]["SWP"], 22)


class RevertKeepsExistingChangeSetTest(GuardBase):  # parity 2026-10-20 T2-1
    def test_revert_from_log_does_not_overwrite_an_existing_change_set(self):
        self.build()
        log = self.log_of(self.apply(self.cs).stdout)
        with open(self.cs, "rb") as fh:
            original = fh.read()
        n0 = len(self.gh.writes())
        r = self.wf("revert-from-log", "--from-log", log, "--change-set", self.cs, "--apply", *LIVE)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("--force", r.stdout)
        self.assertEqual(len(self.gh.writes()), n0, "no write may happen")
        with open(self.cs, "rb") as fh:
            self.assertEqual(fh.read(), original, "the original change-set must survive")
        r = self.wf("revert-from-log", "--from-log", log, "--change-set", self.cs, "--force", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
