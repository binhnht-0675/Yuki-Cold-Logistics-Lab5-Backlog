"""Phase 07 review (22/10): splitting #404 / #300 changes their titles in the backlog. update-body must send the new
title in the same PATCH as the body (one write per issue), under the same rules: a title-only difference is applied
like a reference renumbering, a title change together with a hand-edited body still needs --force-body, and
--keys limits which issues are touched."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "..", "_shared", "tests"))
sys.path.insert(0, os.path.join(SKILL, "..", "_shared"))
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "push-backlog.py")
EXAMPLE = os.path.join(SKILL, "assets", "example-backlog.json")


class UpdateBodyTitleTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        with open(EXAMPLE, encoding="utf-8") as fh:
            self.data = json.load(fh)
        self.backlog = self.gh.path("backlog.json")
        self.save()
        r = self.run_cmd("apply", "--project", "9", "--pace", "0", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.run_cmd("update-body", "--apply").returncode, 0)  # settle the key references first

    def items(self):
        return self.data["items"] if isinstance(self.data, dict) else self.data

    def save(self):
        with open(self.backlog, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False)

    def run_cmd(self, *args):
        return self.gh.run(SCRIPT, list(args) + ["--backlog", self.backlog, "--repo", REPO, "--state-dir", self.state])

    def issue(self, key):
        return next(i for i in self.gh.load()["issues"] if f"<!-- backlog-key: {key} -->" in i["body"])

    def retitle(self, key, title):
        next(i for i in self.items() if i["key"] == key)["titleJa"] = title
        self.save()

    def test_title_only_change_is_written_with_one_patch(self):
        self.retitle("E01-I01", "新しい題名")
        n = len(self.gh.writes())
        r = self.run_cmd("update-body", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("WARN", r.stdout)
        self.assertEqual(self.issue("E01-I01")["title"], "新しい題名")
        self.assertEqual(len(self.gh.writes()) - n, 1, "title goes in the same PATCH; nothing else changes")
        self.assertIn("題名", r.stdout)
        n = len(self.gh.writes())
        self.run_cmd("update-body", "--apply")
        self.assertEqual(len(self.gh.writes()), n, "second run writes nothing")

    def test_dry_run_reports_title_change_and_writes_nothing(self):
        self.retitle("E01-I01", "新しい題名")
        n = len(self.gh.writes())
        r = self.run_cmd("update-body")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[dry-run]", r.stdout)
        self.assertIn("題名", r.stdout)
        self.assertEqual(len(self.gh.writes()), n)

    def test_keys_limit_title_updates(self):
        self.retitle("E01-I01", "題名 A")
        self.retitle("E01-I02", "題名 B")
        self.run_cmd("update-body", "--apply", "--keys", "E01-I02")
        self.assertNotEqual(self.issue("E01-I01")["title"], "題名 A")
        self.assertEqual(self.issue("E01-I02")["title"], "題名 B")

    def test_title_with_hand_edited_body_needs_force(self):
        item = next(i for i in self.items() if i["key"] == "E01-I01")
        item["titleJa"] = "題名 C"
        item["bodyJa"]["概要"] = item["bodyJa"]["概要"] + " 追記。"
        self.save()
        r = self.run_cmd("update-body", "--apply", "--keys", "E01-I01")
        self.assertIn("WARN", r.stdout)
        self.assertNotEqual(self.issue("E01-I01")["title"], "題名 C", "skipped as a whole, title included")
        r = self.run_cmd("update-body", "--apply", "--keys", "E01-I01", "--force-body")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.issue("E01-I01")["title"], "題名 C")
        self.assertIn("追記。", self.issue("E01-I01")["body"])


if __name__ == "__main__":
    unittest.main()
