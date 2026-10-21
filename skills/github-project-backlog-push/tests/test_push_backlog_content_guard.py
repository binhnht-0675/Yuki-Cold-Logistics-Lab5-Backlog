"""push-backlog.py stops with exit 3 and zero gh calls when any text would leak (fake gh, fictional data)."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "..", "_shared", "tests"))
from content_guard_samples import SAMPLES, SECRET_TEXT  # noqa: E402
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "push-backlog.py")
EXAMPLE = os.path.join(SKILL, "assets", "example-backlog.json")
LAST_KEY = "E01-I02-S02"  # the last item written: a finding there must still stop the very first write


class PushBacklogContentGuardTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        with open(EXAMPLE, encoding="utf-8") as fh:
            self.items = json.load(fh)

    def backlog_with(self, mutate):
        items = json.loads(json.dumps(self.items))
        mutate({i["key"]: i for i in items})
        path = self.gh.path("bad-backlog.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False)
        return path

    def run_cmd(self, command, backlog, *extra):
        return self.gh.run(SCRIPT, [command, "--backlog", backlog, "--repo", REPO, "--project", "9",
                                    "--state-dir", self.state] + list(extra))

    def assert_blocked(self, backlog, category_label):
        for command, extra in (("plan", []), ("apply", ["--apply"]), ("update-body", ["--apply"])):
            with self.subTest(command=command):
                r = self.run_cmd(command, backlog, *extra)
                self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
                self.assertIn(category_label, r.stdout)
                self.assertNotIn(SECRET_TEXT, r.stdout + r.stderr)
                self.assertEqual(self.gh.calls(), [], "guard must stop before any gh call")
        self.assertEqual(self.gh.load()["issues"], [])

    def test_each_category_in_last_item_blocks_whole_run(self):
        labels = {"vi": "1 ベトナム語", "ctrl": "2 制御文字", "path": "3 内部パス", "secret": "4 秘密情報",
                  "email": "5 メール", "term": "6 公開しない固有の用語", "internal": "7 社内"}
        for cat, text in SAMPLES.items():
            with self.subTest(cat=cat):
                bad = self.backlog_with(lambda m, t=text: m[LAST_KEY]["bodyJa"].update({"備考": t}))
                self.assert_blocked(bad, labels[cat])
                r = self.run_cmd("plan", bad)
                self.assertIn(f"{LAST_KEY} body", r.stdout)
                self.assertIn("§備考", r.stdout)

    def test_title_and_label_are_checked_too(self):
        bad = self.backlog_with(lambda m: (m["E01"].update({"titleJa": "LAB" + "-3 の続き"}),
                                           m["E01-I01"]["labels"].append("層:s\u1eeda")))
        r = self.run_cmd("plan", bad)
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("E01 title", r.stdout)
        self.assertIn("E01-I01 label", r.stdout)

    def test_permalink_to_allowed_repo_passes_but_other_repo_blocks(self):
        args = ["--ref-style", "permalink", "--ref", "v1", "--specs-root", "docs/specs"]
        r = self.run_cmd("plan", EXAMPLE, *args)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("内容検査: OK", r.stdout)
        # only https://github.com/<owner>/<repo> is exempt: an internal path after it is still blocked
        r = self.run_cmd("plan", EXAMPLE, "--ref-style", "permalink", "--ref", "v1", "--specs-root", "plans" + "/specs")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("3 内部パス", r.stdout)
        r = self.gh.run(SCRIPT, ["plan", "--backlog", EXAMPLE, "--repo", "other-org/private-repo",
                                 "--state-dir", self.gh.path("no-field-map")] + args)  # field-map is example-org's
        self.assertEqual(r.returncode, 0, r.stdout)  # the configured repo is the allowed one
        bad = self.backlog_with(lambda m: m[LAST_KEY]["bodyJa"].update(
            {"備考": "https://git" + "hub.com/other-org/private-repo/blob/main/a.md"}))
        r = self.run_cmd("plan", bad, *args)
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("github-other-repo", r.stdout)

    def test_guard_checks_all_items_whatever_only_level_says(self):
        bad = self.backlog_with(lambda m: m[LAST_KEY]["bodyJa"].update({"備考": SAMPLES["path"]}))  # a task
        r = self.run_cmd("apply", bad, "--apply", "--only-level", "epic")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertEqual(self.gh.calls(), [])

    def test_close_label_is_checked(self):
        r = self.gh.run(SCRIPT, ["close-and-mark", "--repo", REPO, "--state-dir", self.state, "--keys", LAST_KEY,
                                 "--close-label", "LAB" + "-5 で廃止", "--apply"])
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertEqual(self.gh.calls(), [])

    def test_dump_bodies_writes_one_file_per_item(self):
        out = self.gh.path("bodies")
        r = self.run_cmd("plan", EXAMPLE, "--dump-bodies", out)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(len(os.listdir(out)), len(self.items))
        with open(os.path.join(out, f"{LAST_KEY}.md"), encoding="utf-8") as fh:
            self.assertIn(f"<!-- backlog-key: {LAST_KEY} -->", fh.read())


if __name__ == "__main__":
    unittest.main()
