"""write-fields.py stops with exit 3 before reading or writing when a comment / label would leak."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SKILLS = os.path.dirname(SKILL)
sys.path.insert(0, os.path.join(SKILLS, "_shared", "tests"))
from content_guard_samples import SAMPLES, SECRET_TEXT  # noqa: E402
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "write-fields.py")
LIVE = ["--repo", REPO, "--project", "9"]


class WriteFieldsContentGuardTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        self.cs = self.gh.path("cs.json")

    def write_cs(self, last_change):
        changes = [{"key": "E01-I01-S01", "fields": {"Status": "進行中"}, "comment": "着手しました。"},
                   dict({"key": "E01-I02-S02", "fields": {"Status": "完了"}}, **last_change)]
        with open(self.cs, "w", encoding="utf-8") as fh:
            json.dump({"schema": "change-set/1", "source": {"kind": "manual"}, "changes": changes}, fh,
                      ensure_ascii=False)

    def run_wf(self, *args):
        return self.gh.run(SCRIPT, list(args) + ["--change-set", self.cs, "--state-dir", self.state])

    def test_each_category_in_comment_blocks_diff_and_apply(self):
        for cat, text in SAMPLES.items():
            with self.subTest(cat=cat):
                self.write_cs({"comment": text})
                for args in (["diff", "--snapshot", self.gh.path("none.json")], ["apply", "--apply", *LIVE]):
                    r = self.run_wf(*args)
                    self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
                    self.assertIn("E01-I02-S02 comment", r.stdout)
                    self.assertNotIn(SECRET_TEXT, r.stdout + r.stderr)
                self.assertEqual(self.gh.calls(), [], "no gh call (read or write) before the guard passes")

    def test_added_label_is_checked(self):
        self.write_cs({"addLabels": ["持ち越し", "LAB" + "-5"]})
        r = self.run_wf("apply", "--apply", *LIVE)
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("E01-I02-S02 label+", r.stdout)
        self.assertEqual(self.gh.calls(), [])

    def test_clean_change_set_passes_guard(self):
        self.write_cs({"comment": "（模擬）顧客の確認待ち。https://github.com/%s/issues/1" % REPO})
        r = self.run_wf("apply", *LIVE)  # dry-run: reads only
        self.assertIn("内容検査: OK", r.stdout)
        self.assertNotEqual(r.returncode, 3, r.stdout)
        self.assertEqual([c for c in self.gh.calls() if c["write"]], [])


if __name__ == "__main__":
    unittest.main()
