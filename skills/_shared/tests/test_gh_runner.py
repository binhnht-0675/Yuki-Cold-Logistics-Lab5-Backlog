"""Unit tests for the shared gh runner (pacing, retry, stop) and key map."""
import json
import os
import shlex
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from fake_gh_harness import FAKE_GH, FakeGitHub  # noqa: E402
from gh_runner import GhError, GhRunner, RateLimitStop, add_runner_args  # noqa: E402
from key_map import build_key_map, marker, parse_key  # noqa: E402
from write_log import WriteLog, read_log  # noqa: E402

LIMIT = "HTTP 403: You have exceeded a secondary rate limit"


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        os.environ["FAKE_GH_STATE"], os.environ["FAKE_GH_LOG"] = self.gh.state_path, self.gh.log_path
        self.sleeps = []
        self.now = [0.0]
        self.runner = GhRunner(gh=f"{shlex.quote(sys.executable)} {shlex.quote(FAKE_GH)}", pace=2.5,
                               retry_wait=60, max_retries=3, sleep=self.sleeps.append, clock=lambda: self.now[0])

    def create(self):
        return self.runner.api_json("repos/example-org/sample-repo/issues", "POST",
                                    {"title": "t", "body": marker("K1")}, write=True)

    def test_retry_backoff_then_success(self):
        self.gh.inject_failure("issues --method POST", 2, LIMIT)
        res = self.create()
        self.assertEqual(res["number"], 1)
        self.assertEqual(self.sleeps[-2:], [60, 120])

    def test_retry_after_header_is_respected(self):
        self.gh.inject_failure("issues --method POST", 1, "HTTP 429 Too Many Requests\nretry-after: 7")
        self.create()
        self.assertIn(7.0, self.sleeps)

    def test_primary_graphql_rate_limit_is_retried(self):
        msg = "gh: API rate limit exceeded for user ID 1. (RATE_LIMITED)"  # no "HTTP 403" in this form
        self.gh.inject_failure("issues --method POST", 1, msg)
        self.assertEqual(self.create()["number"], 1)
        self.assertEqual(self.sleeps[-1:], [60])

    def test_stop_after_max_retries(self):
        self.gh.inject_failure("issues --method POST", 10, LIMIT)
        with self.assertRaises(RateLimitStop):
            self.create()
        self.assertEqual(len([s for s in self.sleeps if s >= 60]), 3)

    def test_other_error_is_not_retried(self):
        self.gh.inject_failure("issues --method POST", 1, "HTTP 404: Not Found")
        with self.assertRaises(GhError) as ctx:
            self.create()
        self.assertNotIsInstance(ctx.exception, RateLimitStop)
        self.assertEqual(self.sleeps, [])

    def test_writes_are_paced_reads_are_not(self):
        self.create()
        self.create()  # clock did not move -> must wait the full pace
        self.assertEqual(self.sleeps, [2.5])
        self.runner.api_json("repos/example-org/sample-repo/labels")
        self.assertEqual(self.sleeps, [2.5])


class KeyMapTest(unittest.TestCase):
    def test_parse_and_duplicate(self):
        self.assertEqual(parse_key("x\n<!--  backlog-key: E01-I02  -->\n"), "E01-I02")
        self.assertIsNone(parse_key("no marker"))
        issues = [{"number": 1, "body": marker("A")}, {"number": 2, "body": marker("A")}]
        with self.assertRaises(ValueError):
            build_key_map(issues)

    def test_log_has_no_newlines(self):
        gh = FakeGitHub()
        log = WriteLog(gh.path("log.csv"), "s", "c")
        log.write("K", 1, "f", "a\nb", "new")
        rows = list(read_log(gh.path("log.csv")))
        self.assertEqual(rows[0]["old"], "a b")
        self.assertEqual(rows[0]["exit_code"], "0")


class RunnerHardeningTest(unittest.TestCase):
    """Review 20/10: timeout, bounded retry of transient errors, rate limit inside HTTP 200, hourly cap."""

    def setUp(self):
        self.gh = FakeGitHub()
        os.environ["FAKE_GH_STATE"], os.environ["FAKE_GH_LOG"] = self.gh.state_path, self.gh.log_path
        self.sleeps, self.now, self.notes = [], [0.0], []

        def sleep(s):
            self.sleeps.append(s)
            self.now[0] += s
        self.sleep = sleep

    def runner(self, **kw):
        opts = dict(pace=0, retry_wait=60, max_retries=3, sleep=self.sleep, clock=lambda: self.now[0],
                    wall=lambda: 1000.0 + self.now[0], notify=self.notes.append)
        opts.update(kw)
        return GhRunner(gh=f"{shlex.quote(sys.executable)} {shlex.quote(FAKE_GH)}", **opts)

    def inject(self, match, times, stderr="", code=1, **extra):
        st = self.gh.load()
        st["fail"].append(dict({"match": match, "times": times, "stderr": stderr, "code": code}, **extra))
        self.gh.save(st)

    def create(self, r):
        return r.api_json("repos/example-org/sample-repo/issues", "POST", {"title": "t", "body": marker("K1")},
                          write=True)

    def labels(self, r):
        return r.api_json("repos/example-org/sample-repo/labels")

    def test_cli_defaults(self):
        import argparse
        p = argparse.ArgumentParser()
        add_runner_args(p)
        ns = p.parse_args([])
        self.assertEqual((ns.timeout, ns.max_writes_per_hour, ns.retry_wait), (120.0, 450, 60.0))

    def test_hung_read_times_out_and_is_retried(self):
        self.inject("labels", 1, sleep=5)
        self.assertEqual(self.labels(self.runner(timeout=0.5)), [])
        self.assertEqual(len(self.gh.calls()), 2)

    def test_hung_write_times_out_and_stops_without_retry(self):
        self.inject("issues --method POST", 1, sleep=5)
        with self.assertRaises(GhError) as ctx:
            self.create(self.runner(timeout=0.5))
        self.assertNotIsInstance(ctx.exception, RateLimitStop)
        self.assertIn("timeout", str(ctx.exception).lower())
        self.assertEqual(len(self.gh.calls()), 1, "a write whose effect is unknown must not be re-sent")

    def test_5xx_read_is_retried_with_a_bound(self):
        self.inject("labels", 1, "HTTP 502: Bad Gateway (https://api.github.com/)")
        self.assertEqual(self.labels(self.runner()), [])
        self.inject("labels", 99, "gh: Server Error (HTTP 503)")
        with self.assertRaises(GhError) as ctx:
            self.labels(self.runner())
        self.assertNotIsInstance(ctx.exception, RateLimitStop)
        self.assertEqual(len(self.gh.calls()), 2 + 4)  # 1 + max_retries(3) attempts

    def test_5xx_write_is_not_resent_but_connect_error_is(self):
        self.inject("issues --method POST", 1, "HTTP 502: Bad Gateway")
        with self.assertRaises(GhError):
            self.create(self.runner())
        self.assertEqual(len(self.gh.calls()), 1)
        self.inject("issues --method POST", 1, "dial tcp: lookup api.github.com: no such host")
        self.assertEqual(self.create(self.runner())["number"], 1)  # nothing was sent: safe to retry
        self.assertEqual(len(self.gh.load()["issues"]), 1)

    def test_graphql_rate_limit_in_http_200_waits_and_retries(self):
        body = json.dumps({"data": None, "errors": [{"type": "RATE_LIMITED", "message": "API rate limit exceeded"}]})
        self.inject("repository(owner", 2, stdout=body, code=0)
        data = self.runner().graphql("query { repository(owner:$o) { x } }")
        self.assertIn("repository", data)
        self.assertEqual(self.sleeps, [60, 120])

    def test_graphql_rate_limit_exhausted_stops(self):
        body = json.dumps({"errors": [{"message": "You have exceeded a secondary rate limit"}]})
        self.inject("repository(owner", 99, stdout=body, code=0)
        with self.assertRaises(RateLimitStop):
            self.runner().graphql("query { repository(owner:$o) { x } }")
        self.assertEqual(self.sleeps, [60, 120, 240])

    def test_secondary_limit_message_in_rest_200_body(self):
        body = json.dumps({"message": "You have exceeded a secondary rate limit.", "documentation_url": "x"})
        self.inject("issues --method POST", 1, stdout=body, code=0)
        self.assertEqual(self.create(self.runner())["number"], 1)
        self.assertEqual(self.sleeps, [60])

    def test_ratelimit_reset_header_is_used(self):
        self.inject("issues --method POST", 1, "HTTP 403: API rate limit exceeded\n"
                  "x-ratelimit-remaining: 0\nx-ratelimit-reset: 1300")
        self.create(self.runner())
        self.assertEqual(self.sleeps, [301])  # until reset (wall clock 1000) + 1 s

    def test_hourly_write_cap_waits_for_the_rolling_window(self):
        r = self.runner(max_per_hour=3)
        for _ in range(3):
            self.create(r)
            self.now[0] += 10
        self.assertEqual(self.sleeps, [])
        self.create(r)
        self.assertEqual(self.sleeps, [3600 - 30])
        self.assertTrue(any("3 件" in n for n in self.notes), self.notes)
        self.assertEqual(len(self.gh.load()["issues"]), 4)


if __name__ == "__main__":
    unittest.main()
