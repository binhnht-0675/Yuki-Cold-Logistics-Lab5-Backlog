"""Negative tests: snapshot count / key checks, parent = sum of children, iteration scope, burndown dates."""
import json
import os
import unittest

from test_progress_report import EXAMPLE_BACKLOG, PUSH, SCRIPT, SNAP
from fake_gh_harness import REPO, FakeGitHub

DAYS = ["2030-01-%02d" % d for d in range(1, 11)]


class SnapshotChecksTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        r = self.gh.run(PUSH, ["apply", "--apply", "--backlog", EXAMPLE_BACKLOG, "--repo", REPO, "--project", "9",
                               "--state-dir", self.state])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.kmap = os.path.join(self.state, "key-map.json")
        self.out = self.gh.path("snap.json")

    def snapshot(self, *extra, kmap=None):
        return self.gh.run(SCRIPT, ["snapshot", "--owner", "example-org", "--project", "9", "--repo", REPO.upper(),
                                    "--key-map", kmap or self.kmap, "--snapshot", self.out] + list(extra))

    def test_expect_items_mismatch_is_an_error_and_writes_nothing(self):
        r = self.snapshot("--expect-items", "9")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("件数", r.stdout)
        self.assertFalse(os.path.exists(self.out))
        self.assertEqual(self.snapshot("--expect-items", "8").returncode, 0)

    def test_key_map_mismatch_is_an_error(self):
        with open(self.kmap, encoding="utf-8") as fh:
            km = json.load(fh)
        km["keys"].pop(next(iter(km["keys"])))
        short = self.gh.path("short-key-map.json")
        with open(short, "w", encoding="utf-8") as fh:
            json.dump(km, fh, ensure_ascii=False)
        r = self.snapshot(kmap=short)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("key-map", r.stdout)
        self.assertFalse(os.path.exists(self.out))


class TablesChecksTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        with open(SNAP, encoding="utf-8") as fh:
            self.snap = json.load(fh)

    def write(self, name, obj):
        path = self.gh.path(name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False)
        return path

    def tables(self, *extra, snap=SNAP):
        return self.gh.run(SCRIPT, ["tables", "--snapshot", snap] + list(extra))

    def item(self, snap, key):
        return next(i for i in snap["items"] if i["key"] == key)

    def test_parent_not_equal_sum_of_children_is_reported_with_exit_4(self):
        self.item(self.snap, "E01")["fields"]["SWP"] = 22
        r = self.tables(snap=self.write("bad.json", self.snap))
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("親 = 子の合計", r.stdout)
        self.assertIn("| E01 | SWP | 22 | 21 |", r.stdout)
        ok = self.tables()
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn("一致", ok.stdout)

    def test_status_and_state_disagreeing_is_warned_and_strict_fails(self):
        """Review 20/10 team 1 item 7: 完了 but open / closed but not 完了 -> 注意 line + list; --strict -> exit 5."""
        self.item(self.snap, "E01-I01-S03")["fields"]["Status"] = "完了"  # still OPEN
        self.item(self.snap, "E01-I01-S02")["fields"]["Status"] = "進行中"  # already CLOSED
        snap = self.write("drift.json", self.snap)
        r = self.tables(snap=snap)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("注意: Status と issue の状態（open / closed）が合わない issue が 2 件", r.stdout)
        self.assertIn("| E01-I01-S03 | 6 | 完了 | OPEN | Status 完了 だが未クローズ |", r.stdout)
        self.assertIn("| E01-I01-S02 | 5 | 進行中 | CLOSED | クローズ済みだが Status ≠ 完了 |", r.stdout)
        res = json.loads(self.tables("--format", "json", snap=snap).stdout)
        self.assertEqual([m["key"] for m in res["statusStateMismatch"]], ["E01-I01-S02", "E01-I01-S03"])
        strict = self.tables("--strict", snap=snap)
        self.assertEqual(strict.returncode, 5, strict.stdout + strict.stderr)
        self.assertIn("注意:", strict.stdout, "the tables are still written")
        clean = self.tables("--strict")
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        self.assertNotIn("注意:", clean.stdout)

    def test_plan_snapshot_keeps_moved_issue_in_the_sprint_total(self):
        plan = json.loads(json.dumps(self.snap))
        self.item(plan, "E01-I01-S03")["fields"]["スプリント"] = "スプリント 1"
        r = self.tables("--iteration", "スプリント 1", "--plan-snapshot", self.write("plan.json", plan))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("| **合計** | 5 | 21 |  |", r.stdout)
        self.assertIn("他のイテレーションへ移動 1 件", r.stdout)

    def test_iteration_filter_states_its_scope(self):
        r = self.tables("--iteration", "スプリント 1")
        self.assertIn("集計範囲", r.stdout)

    def test_burndown_dates_come_from_project_closed_at(self):
        r = self.tables("--iteration", "スプリント 1", "--sprint-days", self.write("d.json", {"days": DAYS}),
                        "--format", "json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = json.loads(r.stdout)
        self.assertEqual(res["burndown"][2]["remaining"], 13)
        self.assertEqual(res["burndown"][-1]["remaining"], 10)
        self.assertIn("closedAt", res["burndownDateSource"])

    def test_burndown_file_dates_are_checked_against_project(self):
        days = self.write("d.json", {"days": DAYS, "completed": {"E01-I01-S01": "2030-01-03",
                                                                 "E01-I01-S02": "2030-01-07",
                                                                 "E01-I02-S02": "2030-01-08"}})
        r = self.tables("--iteration", "スプリント 1", "--sprint-days", days)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("E01-I02-S02", r.stdout)
        bad = self.write("bad-days.json", {"days": DAYS, "completed": {"E01-I01-S01": "2030/01/03",
                                                                       "E01-I01-S02": "2030-01-07"}})
        r = self.tables("--iteration", "スプリント 1", "--sprint-days", bad)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("YYYY-MM-DD", r.stdout)


if __name__ == "__main__":
    unittest.main()
