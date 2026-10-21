"""push-backlog.py: field-map preflight inside `apply`, time estimate, Project title warning, label listing
(fake gh, fictional data). Review 20/10."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "..", "_shared", "tests"))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "push-backlog.py")
EXAMPLE = os.path.join(SKILL, "assets", "example-backlog.json")


class PreflightTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        self.write_fmap()

    def write_fmap(self, **change):
        fmap = dict(self.gh.field_map(), title="サンプル")
        fmap.update(change)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(fmap, fh, ensure_ascii=False)

    def run_cmd(self, command, *extra, backlog=EXAMPLE):
        return self.gh.run(SCRIPT, [command, "--backlog", backlog, "--repo", REPO, "--project", "9",
                                    "--state-dir", self.state] + list(extra))

    def backlog_with_role(self, role):
        with open(EXAMPLE, encoding="utf-8") as fh:
            items = json.load(fh)
        items[2]["assigneeRole"] = role
        path = self.gh.path("roles.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False)
        return path

    def assert_stopped_before_first_write(self, r, needle):
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn(needle, r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(self.gh.writes(), [])
        self.assertEqual(self.gh.load()["issues"], [])

    def test_apply_checks_field_map_before_the_first_write(self):
        cases = [
            ("status option", ["--initial-status", "着手前"], {}, None, "着手前"),
            ("role field", ["--role-field", "担当者"], {}, None, "担当者"),
            ("role option", [], {}, "BE-9", "BE-9"),
            ("other Project number", [], {"number": 8}, None, "field-map"),
            ("other Project id", [], {"projectId": "PVT_other"}, None, "PVT_other"),
        ]
        for name, extra, change, role, needle in cases:
            with self.subTest(case=name):
                self.setUp()
                self.write_fmap(**change)
                backlog = self.backlog_with_role(role) if role else EXAMPLE
                r = self.run_cmd("apply", "--apply", *extra, backlog=backlog)
                self.assert_stopped_before_first_write(r, needle)

    def test_apply_compares_field_names_and_option_ids_with_the_live_project(self):
        """Review 20/10 team 1 item 2: field-map is right for the projectId but the Project changed since."""
        def option_id_changed(f):
            f["Status"]["options"]["未着手"] = "o-new"

        def field_renamed(f):
            f["担当"] = f.pop("担当（仮）")
        cases = [("Status option id", option_id_changed, "Status: 選択肢"), ("role field name", field_renamed, "担当（仮）")]
        for name, change, needle in cases:
            with self.subTest(case=name):
                self.setUp()  # field-map written from the Project as it was
                st = self.gh.load()
                change(st["project"]["fields"])
                self.gh.save(st)
                r = self.run_cmd("apply", "--apply")
                self.assert_stopped_before_first_write(r, needle)
                self.assertIn("fetch-field-map", r.stdout)

    def test_apply_without_field_map_stops_cleanly(self):
        os.remove(os.path.join(self.state, "field-map.json"))
        r = self.run_cmd("apply", "--apply")
        self.assert_stopped_before_first_write(r, "fetch-field-map")

    def test_plan_checks_status_option_too(self):
        r = self.run_cmd("plan", "--initial-status", "着手前")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertEqual(self.gh.calls(), [])

    def test_plan_estimate_counts_the_hourly_cap(self):
        r = self.run_cmd("plan", "--max-writes-per-hour", "10")  # 46 writes: 4 full hours + 6 x 2.5 s
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("10 件 / 60 分", r.stdout)
        self.assertIn("約 4.0 時間", r.stdout)
        r = self.run_cmd("plan", "--max-writes-per-hour", "0")
        self.assertIn("時間あたりの上限なし", r.stdout)

    def test_estimate_function(self):
        from backlog_run_estimate import estimate_seconds
        self.assertEqual(estimate_seconds(2421, 2.5, 450), 5 * 3600 + 171 * 2.5)
        self.assertEqual(estimate_seconds(100, 2.5, 450), 250)
        self.assertEqual(estimate_seconds(1000, 10, 450), 10000)  # the pace alone is slower than the cap
        self.assertEqual(estimate_seconds(0, 2.5, 450), 0)

    def test_project_title_with_internal_term_warns(self):
        self.write_fmap(title="サンプル（" + "LAB" + "-5）")
        for command in ("plan", "apply"):
            with self.subTest(command=command):
                r = self.run_cmd(command)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("WARN Project 名", r.stdout)
                self.assertIn("6 公開しない固有の用語", r.stdout)
        self.write_fmap(title="サンプル")
        self.assertNotIn("WARN Project 名", self.run_cmd("plan").stdout)

    def test_existing_labels_are_read_past_page_one_and_compared_case_insensitively(self):
        st = self.gh.load()
        st["labels"] = ["x-%d" % n for n in range(105)] + ["種別:エピック", "層:db"]
        self.gh.save(st)
        r = self.run_cmd("apply", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        posted = [json.loads(c["stdin"])["name"] for c in self.gh.writes() if c["args"][1].endswith("/labels")]
        self.assertEqual(len(posted), 5, posted)
        self.assertNotIn("種別:エピック", posted)
        self.assertNotIn("層:DB", posted)


if __name__ == "__main__":
    unittest.main()
