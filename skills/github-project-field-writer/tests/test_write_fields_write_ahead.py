"""Write-ahead log: a crash between a GitHub write and its log row must still be revertible,
and comments are deleted by revert-from-log (by logged id, else found by sha8 on GitHub)."""
import csv
import json
import unittest

from test_write_fields import LIVE, FieldWriterBase

S01 = "貸出テーブルを追加"  # E01-I01-S01 in the sample backlog


class WriteAheadTest(FieldWriterBase):
    def cs_file(self, name, changes):
        path = self.gh.path(name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"schema": "change-set/1", "source": {"kind": "manual"}, "changes": changes}, fh,
                      ensure_ascii=False)
        return path

    def apply(self, cs, log):
        return self.wf("apply", "--change-set", cs, "--apply", *LIVE, "--log", log)

    def revert(self, log):
        r = self.wf("revert-from-log", "--from-log", log, "--change-set", self.gh.path("rv.json"), "--apply", *LIVE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def rows(self, log):
        with open(log, encoding="utf-8") as fh:
            return [r for r in csv.DictReader(fh) if not r["field"].startswith("#")]

    def comments(self):
        return self.gh.load().get("comments", [])

    def crash_comment_run(self):
        cs = self.cs_file("cs-c.json", [{"key": "E01-I02-S01", "comment": "（模擬）確認メモ"}])
        log = self.gh.path("run-c.csv")
        self.gh.inject_crash("/comments --method POST")
        r = self.apply(cs, log)
        self.assertNotEqual(r.returncode, 0, "the skill process must have been killed")
        self.assertEqual(len(self.comments()), 1, "the comment reached GitHub before the crash")
        return cs, log

    def test_crash_after_field_write_is_reverted(self):
        cs = self.cs_file("cs-f.json", [{"key": "E01-I01-S01", "fields": {"Status": "完了"}},
                                        {"key": "E01-I01-S03", "fields": {"Status": "進行中"}}])
        log = self.gh.path("run-f.csv")
        self.gh.inject_crash("updateProjectV2ItemFieldValue")
        r = self.apply(cs, log)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.values()[S01]["Status"], "完了", "the write reached GitHub")
        self.assertEqual([x["status"] for x in self.rows(log)], ["pending"], "only the write-ahead row is left")
        self.revert(log)
        self.assertEqual(self.values()[S01]["Status"], "未着手", "revert restores the value before the crash")

    def test_uncertain_write_does_not_overwrite_a_later_run(self):
        log = self.gh.path("run-u.csv")
        self.gh.inject_crash("updateProjectV2ItemFieldValue")
        self.apply(self.cs_file("cs-u.json", [{"key": "E01-I01-S01", "fields": {"Status": "完了"}}]), log)
        self.apply(self.cs_file("cs-later.json", [{"key": "E01-I01-S01", "fields": {"Status": "進行中"}}]),
                   self.gh.path("l.csv"))
        r = self.revert(log)
        self.assertEqual(self.values()[S01]["Status"], "進行中", "GitHub no longer holds this run's value: keep it")
        self.assertIn("この実行の値ではないので戻さない", r.stdout)

    def test_crash_after_comment_post_is_reverted(self):
        _, log = self.crash_comment_run()
        self.revert(log)
        self.assertEqual(self.comments(), [], "the comment found by its sha8 is deleted")

    def test_rerun_after_crash_does_not_post_comment_twice(self):
        cs, log = self.crash_comment_run()
        r = self.apply(cs, log)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.comments()), 1, "a pending comment already on GitHub is not posted again")

    def test_crash_before_comment_post_reverts_only_what_reached_github(self):
        cs = self.cs_file("cs-b.json", [{"key": "E01-I01-S01", "fields": {"Status": "完了"}},
                                        {"key": "E01-I02-S01", "comment": "（模擬）未投稿"}])
        log = self.gh.path("run-b.csv")
        self.apply(self.cs_file("cs-0.json", [{"key": "E01-I01-S01", "fields": {"Status": "進行中"}}]),
                   self.gh.path("r0.csv"))
        self.gh.inject_crash("/comments --method POST", when="before")
        self.assertNotEqual(self.apply(cs, log).returncode, 0)
        self.assertEqual(self.comments(), [])
        self.assertEqual([x["status"] for x in self.rows(log)], ["pending", "done", "pending"])
        n0 = len(self.gh.writes())
        r = self.revert(log)
        self.assertEqual(self.values()[S01]["Status"], "進行中", "the field write of the run is undone")
        self.assertEqual(len(self.gh.writes()) - n0, 1, "the never-posted comment needs no write")
        self.assertIn("| E01-I02-S01 | 7 | comment- |", r.stdout)

    def test_comment_revert_deletes_by_logged_id_once(self):
        log = self.gh.path("run-ok.csv")
        r = self.apply(self.cs_file("cs-ok.json", [{"key": "E01-I02-S01", "comment": "（模擬）確認メモ"}]), log)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cid = self.comments()[0]["id"]
        done = [x for x in self.rows(log) if x["status"] == "done"]
        self.assertEqual([x["ref"] for x in done], [str(cid)], "the done row keeps the comment id")
        self.revert(log)
        self.assertEqual(self.comments(), [])
        deletes = [c for c in self.gh.writes() if "DELETE" in c["args"]]
        self.assertEqual([c["args"][1] for c in deletes], [f"repos/example-org/sample-repo/issues/comments/{cid}"])
        self.revert(log)
        self.assertEqual(len([c for c in self.gh.writes() if "DELETE" in c["args"]]), 1, "already deleted: skip")

    def test_comment_deleted_by_revert_is_posted_again_by_the_next_apply(self):
        """Review 20/10 team 1 item 6: the live comments decide, not the old done row in the log."""
        log, cs = self.gh.path("run-re.csv"), self.cs_file("cs-re.json", [{"key": "E01-I02-S01", "comment": "（模擬）再投稿"}])
        self.assertEqual(self.apply(cs, log).returncode, 0)
        self.revert(log)
        self.assertEqual(self.comments(), [])
        r = self.apply(cs, log)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([c["body"] for c in self.comments()], ["（模擬）再投稿"], "the comment is back on the issue")
        r = self.apply(cs, log)
        self.assertEqual(len(self.comments()), 1, "still on GitHub: not posted twice")
        self.assertIn("'変更': 0", r.stdout)

    def test_two_identical_comments_without_id_need_hand_delete(self):
        _, log = self.crash_comment_run()
        st = self.gh.load()
        st["comments"].append(dict(st["comments"][0], id=999))
        self.gh.save(st)
        r = self.revert(log)
        self.assertIn("手で削除", r.stdout)
        self.assertEqual(len(self.comments()), 2, "nothing is deleted when the target is ambiguous")

    def test_legacy_log_without_status_columns_still_reverts(self):
        log = self.gh.path("legacy.csv")
        cs = self.cs_file("cs-l.json", [{"key": "E01-I01-S01", "fields": {"Status": "完了"}},
                                        {"key": "E01-I02-S01", "comment": "（模擬）旧形式"}])
        self.assertEqual(self.apply(cs, log).returncode, 0)
        with open(log, encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        legacy = [rows[0][:9]] + [r[:9] for r in rows[1:] if r[9] != "pending"]  # format before 20/10
        with open(log, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(legacy)
        self.revert(log)
        self.assertEqual(self.values()[S01]["Status"], "未着手")
        self.assertEqual(self.comments(), [], "no id in an old log: found on GitHub by sha8 and deleted")


if __name__ == "__main__":
    unittest.main()
