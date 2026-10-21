"""Review 20/10: the 450 writes / rolling 60 minutes cap must hold across runs and across skill 1 / skill 2.

Each "run" is a fresh runner built by the skill's own CLI parser (same as a new process); gh is stubbed,
time is fake. CLI-level cases run the real script against the fake gh in a temp dir.
"""
import importlib.util
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.dirname(HERE)
SKILLS = os.path.dirname(SHARED)
sys.path.insert(0, SHARED)
sys.path.insert(0, HERE)
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402
from gh_runner import runner_from_args  # noqa: E402

PUSH = os.path.join(SKILLS, "github-project-backlog-push", "scripts", "push-backlog.py")
WRITE = os.path.join(SKILLS, "github-project-field-writer", "scripts", "write-fields.py")
BACKLOG = os.path.join(SKILLS, "github-project-backlog-push", "assets", "example-backlog.json")
BIG_WAIT = 60  # anything longer than the pace is the hourly gate


def load_cli(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PUSH_CLI = load_cli("push_backlog_cli", PUSH)
WRITE_CLI = load_cli("write_fields_cli", WRITE)


class WindowAcrossRunsTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        self.now = [1_800_000_000.0]
        self.sent, self.waits, self.notes = [0], [], []

    def sleep(self, s):
        if s >= BIG_WAIT:
            self.waits.append((self.sent[0], s))
        self.now[0] += s

    def run_of(self, cli, command):
        ns = cli.parse_args([command, "--apply", "--pace", "0", "--state-dir", self.state])
        r = runner_from_args(ns)
        r.sleep, r.clock, r.wall, r.notify = self.sleep, (lambda: self.now[0]), (lambda: self.now[0]), self.notes.append

        def fake_exec(args, stdin):
            self.sent[0] += 1
            return 0, "{}", ""
        r._exec = fake_exec
        return r

    def write(self, r, n):
        for _ in range(n):
            r.api_json(f"repos/{REPO}/issues", "POST", {"title": "t"}, write=True)
            self.now[0] += 1

    def test_a_second_run_waits_once_the_shared_window_is_full(self):
        self.write(self.run_of(PUSH_CLI, "apply"), 440)  # run 1 (e.g. --only-level epic,story)
        self.assertEqual(self.waits, [])
        self.sent[0] = 0
        self.write(self.run_of(PUSH_CLI, "apply"), 20)  # run 2: a new process, same state dir
        self.assertEqual(len(self.waits), 1, "run 2 must wait: 440 + 10 writes already in the last 60 minutes")
        before, wait = self.waits[0]
        self.assertEqual(before, 10, "the 11th write of run 2 is the 451st in the window")
        self.assertAlmostEqual(wait, 3600 - 450, delta=1)
        self.assertTrue(any("450 件" in n for n in self.notes), self.notes)

    def test_b_writes_older_than_60_minutes_are_dropped(self):
        self.write(self.run_of(PUSH_CLI, "apply"), 449)
        self.now[0] += 3600
        self.write(self.run_of(PUSH_CLI, "apply"), 20)
        self.assertEqual(self.waits, [])
        with open(os.path.join(self.state, "write-window.json"), encoding="utf-8") as fh:
            saved = json.load(fh)
        self.assertEqual(saved["version"], 1)
        self.assertEqual(len(saved["writes"]), 20, "entries older than 60 minutes must be pruned from the file")

    def test_d_skill_1_and_skill_2_share_one_window(self):
        r1, r2 = self.run_of(PUSH_CLI, "apply"), self.run_of(WRITE_CLI, "apply")
        self.assertEqual(r1.window.path, r2.window.path)
        self.write(r1, 445)
        self.sent[0] = 0
        self.write(r2, 10)
        self.assertEqual([w[0] for w in self.waits], [5], "skill 2 must count the writes of skill 1")


class WindowConcurrentRunsTest(unittest.TestCase):
    """Team review 20/10 (round 5): two runs at the same moment must not both take the last slot."""

    def test_e_a_run_cannot_slip_in_between_another_runs_count_and_save(self):
        """A has just counted 0 of cap 1. If nothing holds A's count and save together, B writes right
        now and A then writes too (2 writes). If A holds the lock, B could only wait for it, so B runs
        after A and finds the window full. Decided by a non-blocking probe of the lock, not by timing."""
        from gh_runner import GhRunner
        from write_window_store import FileWindow, fcntl
        if fcntl is None:
            self.skipTest("no fcntl: no lock on this platform")
        state = FakeGitHub().path("state")
        os.makedirs(state)
        path, sent, after_a = os.path.join(state, "write-window.json"), [], []

        class Full(Exception):
            pass

        def runner(name, window):
            r = GhRunner(pace=0, max_per_hour=1, window=window, wall=lambda: 1_800_000_000.0, notify=lambda _m: None)
            r.sleep = lambda _s: (_ for _ in ()).throw(Full())  # the window is full: stop instead of waiting
            r._exec = lambda args, stdin: (sent.append(name), (0, "{}", ""))[1]
            return r

        def write(r):
            try:
                r.api_json(f"repos/{REPO}/issues", "POST", {"title": "t"}, write=True)
            except Full:
                pass

        b, win_a = runner("B", FileWindow(path)), FileWindow(path)
        read_a, b_started = win_a._read, []

        def read_then_let_b_run():
            times = read_a()
            if not b_started:
                b_started.append(True)
                with open(path + ".lock", "a") as probe:
                    try:
                        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        after_a.append(b)  # A holds the lock while counting: B would block until A saved
                    else:
                        fcntl.flock(probe, fcntl.LOCK_UN)
                        write(b)  # A counted outside the lock: B gets in between
            return times
        win_a._read = read_then_let_b_run
        write(runner("A", win_a))
        for r in after_a:
            write(r)
        self.assertEqual(len(sent), 1, f"cap 1 but written by {sent}")
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)["writes"]), 1)


class WindowCliTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        self.window = os.path.join(self.state, "write-window.json")

    def push(self, *extra):
        return self.gh.run(PUSH, ["apply", "--backlog", BACKLOG, "--repo", REPO, "--project", "9", "--pace", "0",
                                  "--state-dir", self.state] + list(extra))

    def test_c_broken_window_file_stops_before_any_write(self):
        for broken in ("{not json", json.dumps({"version": 99, "writes": []}), json.dumps({"version": 1, "writes": ["x"]})):
            with open(self.window, "w", encoding="utf-8") as fh:
                fh.write(broken)
            r = self.push("--apply")
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("write-window.json", r.stdout)
            self.assertNotIn("Traceback", r.stderr)
            self.assertEqual(self.gh.writes(), [], "nothing may be written with an unreadable window")
            r = self.gh.run(WRITE, ["apply", "--apply", "--change-set", self.gh.path("cs.json"), "--repo", REPO,
                                    "--project", "9", "--state-dir", self.state])  # skill 2 stops the same way
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("write-window.json", r.stdout)
            self.assertEqual(self.gh.calls(), [])
        r = self.push("--apply", "--ignore-broken-write-window")  # explicit opt-in to start from 0
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.window, encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)["writes"]), len(self.gh.writes()))

    def test_dry_run_and_plan_do_not_touch_the_window_file(self):
        r = self.push()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.gh.run(PUSH, ["plan", "--backlog", BACKLOG, "--repo", REPO, "--state-dir", self.state])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(self.window))
        r = self.push("--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.window, encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)["writes"]), len(self.gh.writes()), "every write is recorded")


if __name__ == "__main__":
    unittest.main()
