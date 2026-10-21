"""Trial push 20/10 (E09, real GitHub): right after `apply`, the Project's item list showed 1 of 15 items
while every issue already had its item. A re-run then planned to set Status / 担当（仮） again on the 14
unlisted items - on a later re-run that would reset a Status a person had changed (e.g. 完了 -> 未着手).
Fields of items missing from the list must be read by id, never assumed empty."""
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


class ProjectItemListLagTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)

    def push(self, *extra):
        return self.gh.run(SCRIPT, ["apply", "--backlog", EXAMPLE, "--repo", REPO, "--project", "9", "--pace", "0",
                                    "--state-dir", self.state] + list(extra))

    def test_rerun_does_not_touch_fields_of_items_missing_from_the_project_list(self):
        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = self.gh.load()
        items = st["project"]["items"]
        self.assertGreater(len(items), 2)
        items[-1]["values"]["Status"] = "完了"  # a person moved this one on meanwhile
        st["unlisted_items"] = [it["id"] for it in items[1:]]  # the list shows only the first item yet
        self.gh.save(st)
        before = len(self.gh.writes())

        r = self.push()  # dry-run
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("field-set", r.stdout, "fields already set must not be planned again")

        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.gh.writes()[before:], [], "a re-run must write nothing")
        self.assertEqual(self.gh.load()["project"]["items"][-1]["values"]["Status"], "完了")

    def test_auto_added_sub_issue_is_taken_as_added(self):
        """Full push 20/10: the Project workflow "Auto-add sub-issues to project" added #54 right after it
        became a sub-issue, so the skill's own add was refused ("Content already exists") and the run stopped."""
        st = self.gh.load()
        st["auto_add_sub_issues"] = True
        self.gh.save(st)
        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = self.gh.load()
        per_issue = [it["issueNumber"] for it in st["project"]["items"]]
        self.assertEqual(sorted(per_issue), sorted(i["number"] for i in st["issues"]), "each issue once in the Project")
        self.assertTrue(all(it["values"].get("Status") == "未着手" for it in st["project"]["items"]))
        before = len(self.gh.writes())
        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.gh.writes()[before:], [], "a re-run must write nothing")

    def test_unlisted_item_that_cannot_be_read_by_id_stops_before_any_write(self):
        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = self.gh.load()
        lost = st["project"]["items"][-1]["id"]
        st["unlisted_items"], st["unreadable_items"] = [lost], [lost]
        self.gh.save(st)
        before = len(self.gh.writes())
        r = self.push("--apply")
        self.assertNotEqual(r.returncode, 0, "an item that cannot be read must not be taken as empty")
        self.assertIn("id で読めません", r.stdout + r.stderr)
        self.assertEqual(self.gh.writes()[before:], [], "nothing may be written")


if __name__ == "__main__":
    unittest.main()
