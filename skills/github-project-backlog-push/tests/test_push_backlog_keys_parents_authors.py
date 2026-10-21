"""Review 20/10 round 2 for push-backlog.py (fake gh, fictional data):
L2 key characters, L-5 --dump-bodies stays inside its folder, L4 --only-level without parents,
M-1 a backlog-key marker in an issue opened by another account."""
import contextlib
import io
import json
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "..", "_shared", "tests"))
sys.path.insert(0, os.path.join(SKILL, "..", "_shared"))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "push-backlog.py")
EXAMPLE = os.path.join(SKILL, "assets", "example-backlog.json")


class KeysParentsAuthorsTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        with open(EXAMPLE, encoding="utf-8") as fh:
            self.items = json.load(fh)

    def run_cmd(self, command, *extra, backlog=EXAMPLE):
        return self.gh.run(SCRIPT, [command, "--backlog", backlog, "--repo", REPO, "--project", "9",
                                    "--state-dir", self.state] + list(extra))

    def backlog_renaming(self, old, new):
        text = json.dumps(self.items, ensure_ascii=False).replace(f'"{old}"', json.dumps(new))
        path = self.gh.path("renamed.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_key_with_characters_the_marker_cannot_hold_stops_before_any_call(self):
        for bad in ["E01-I02-S02 x", "E01-I02-S02/../x", "E01-I02-S02か", "../evil"]:
            backlog = self.backlog_renaming("E01-I02-S02", bad)
            for command in ("plan", "apply"):
                with self.subTest(key=bad, command=command):
                    r = self.run_cmd(command, "--apply", backlog=backlog) if command == "apply" \
                        else self.run_cmd(command, backlog=backlog)
                    self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                    self.assertIn("key に使えない文字", r.stdout)
        self.assertEqual(self.gh.calls(), [])

    def test_dump_bodies_never_writes_outside_its_folder(self):
        from backlog_maintenance_commands import dump_bodies
        out = self.gh.path("dump")
        ns = types.SimpleNamespace(dump_bodies=out, repo=REPO, ref_style="text", ref=None, specs_root="", edition="")
        item = dict(self.items[0], key="../escaped")
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(dump_bodies(ns, [item]), 2)
            self.assertFalse(os.path.exists(os.path.join(self.gh.dir, "escaped.md")))
            self.assertEqual(dump_bodies(ns, self.items[:1]), 0)
        self.assertIn("書き出しません", printed.getvalue())
        self.assertTrue(os.path.exists(os.path.join(out, "E01.md")))

    def test_only_level_task_before_its_parents_writes_nothing(self):
        r = self.run_cmd("apply", "--apply", "--only-level", "task")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("親 E01-I01 が GitHub にまだありません", r.stdout)
        self.assertEqual((self.gh.writes(), self.gh.load()["issues"]), ([], []))
        r = self.run_cmd("plan", "--only-level", "task")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_only_level_story_without_epic_fails(self):  # moved from test_push_backlog.py (was: exit 1 after a write)
        r = self.run_cmd("apply", "--apply", "--only-level", "story")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("未作成", r.stdout)
        self.assertEqual(self.gh.writes(), [])

    def test_levels_in_order_still_work(self):
        for level in ("epic", "story", "task"):
            r = self.run_cmd("apply", "--apply", "--only-level", level)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.gh.load()["issues"]), 8)

    def outsider_issue(self, key, number=50):
        st = self.gh.load()
        st["issues"].append({"number": number, "id": 1000 + number, "nodeId": f"I_{number}", "title": "x",
                             "body": f"<!-- backlog-key: {key} -->", "state": "OPEN", "labels": [],
                             "parent": None, "author": "outsider"})
        st["next_number"] = number + 1
        self.gh.save(st)

    def test_marker_in_an_issue_by_another_account_is_ignored(self):
        self.outsider_issue("E01-I01")  # placed before the story level runs
        r = self.run_cmd("apply", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("WARN #50: キー E01-I01", r.stdout)
        issues = self.gh.load()["issues"]
        mine = [i for i in issues if "backlog-key: E01-I01 " in i["body"] and i.get("author") != "outsider"]
        self.assertEqual(len(mine), 1, "the skill makes its own issue for the key")
        outsider = next(i for i in issues if i["number"] == 50)
        self.assertIsNone(outsider["parent"])
        self.assertNotIn(50, [it["issueNumber"] for it in self.gh.load()["project"]["items"]])
        self.assertTrue(all(i.get("parent") != 50 for i in issues), "no task is linked under the outsider issue")

    def test_duplicate_marker_by_another_account_does_not_block(self):
        self.assertEqual(self.run_cmd("apply", "--apply").returncode, 0)
        self.outsider_issue("E01", number=60)
        r = self.gh.run(SCRIPT, ["rebuild-key-map", "--repo", REPO, "--state-dir", self.state])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("WARN #60", r.stdout)
        with open(os.path.join(self.state, "key-map.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["keys"]["E01"]["number"], 1)

    def test_run_under_another_account_than_the_owner_stops_before_any_write(self):
        """Review 20/10 team 1 item 4: viewer != author AND viewer != repo owner -> exit 2, zero writes."""
        self.assertEqual(self.run_cmd("apply", "--apply").returncode, 0)  # the owner (example-org) opened them
        st = self.gh.load()
        for i in st["issues"]:
            i["author"] = "example-org"
        st["viewer"] = "helper-account"
        self.gh.save(st)
        writes, issues = len(self.gh.writes()), len(st["issues"])
        for command in ("apply", "rebuild-key-map"):
            with self.subTest(command=command):
                r = self.run_cmd(command, "--apply") if command == "apply" else \
                    self.gh.run(SCRIPT, [command, "--repo", REPO, "--state-dir", self.state])
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("別のアカウントで実行しています", r.stdout)
        self.assertEqual((len(self.gh.writes()), len(self.gh.load()["issues"])), (writes, issues), "no write at all")


if __name__ == "__main__":
    unittest.main()
