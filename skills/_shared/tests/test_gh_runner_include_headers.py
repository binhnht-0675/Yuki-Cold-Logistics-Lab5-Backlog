"""Review 20/10 (team 1, item 3): the rate-limit wait reads the RESPONSE headers (`gh api --include`).

Real gh prints the headers on stdout only with --include; the error message on stderr carries no header.
The fake gh does the same, so these tests fail when the runner does not pass --include.
"""
import json
import os
import shlex
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from fake_gh_harness import FAKE_GH, FakeGitHub  # noqa: E402
from gh_include_response import split_include  # noqa: E402
from gh_runner import GhRunner  # noqa: E402

SECONDARY = "gh: You have exceeded a secondary rate limit. (HTTP 403)"
PRIMARY = "gh: API rate limit exceeded for user ID 1. (HTTP 403)"


class IncludeHeadersTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        os.environ["FAKE_GH_STATE"], os.environ["FAKE_GH_LOG"] = self.gh.state_path, self.gh.log_path
        self.sleeps, self.now = [], [0.0]

        def sleep(s):
            self.sleeps.append(s)
            self.now[0] += s
        self.runner = GhRunner(gh=f"{shlex.quote(sys.executable)} {shlex.quote(FAKE_GH)}", pace=0, retry_wait=60,
                               max_retries=3, sleep=sleep, clock=lambda: self.now[0], wall=lambda: 1000.0 + self.now[0],
                               notify=lambda s: None)

    def inject(self, match, stderr, headers, times=1):
        st = self.gh.load()
        st["fail"].append({"match": match, "times": times, "stderr": stderr, "code": 1, "headers": headers,
                           "stdout": json.dumps({"message": "rate limit"})})
        self.gh.save(st)

    def create(self):
        return self.runner.api_json("repos/example-org/sample-repo/issues", "POST", {"title": "t", "body": "b"},
                                    write=True)

    def test_retry_after_response_header_sets_the_wait(self):
        self.inject("issues --method POST", SECONDARY, {"Retry-After": "7"}, times=2)
        self.assertEqual(self.create()["number"], 1)
        self.assertEqual(self.sleeps, [7.0, 14.0], "retry-after from the headers, doubled on the repeat")

    def test_ratelimit_reset_response_header_waits_until_reset(self):
        self.inject("issues --method POST", PRIMARY, {"X-Ratelimit-Remaining": "0", "X-Ratelimit-Reset": "1300"})
        self.assertEqual(self.create()["number"], 1)
        self.assertEqual(self.sleeps, [301.0], "until x-ratelimit-reset (wall clock 1000) + 1 s")

    def test_without_headers_the_wait_is_60s_doubling(self):
        self.inject("issues --method POST", SECONDARY, {}, times=2)
        self.create()
        self.assertEqual(self.sleeps, [60, 120])

    def test_every_call_asks_for_headers_and_bodies_still_parse(self):
        self.assertEqual(self.create()["number"], 1)
        self.assertIn("repository", self.runner.graphql("query { repository(owner:$o) { x } }"))
        cid = self.runner.api_json("repos/example-org/sample-repo/issues/1/comments", "POST", {"body": "c"}, write=True)["id"]
        self.assertIsNone(self.runner.api_json(f"repos/example-org/sample-repo/issues/comments/{cid}", "DELETE", write=True),
                          "HTTP 204: headers only, no body")
        self.assertTrue(all("--include" in c["args"] for c in self.gh.calls()), self.gh.calls())

    def test_split_include(self):
        out = "HTTP/2.0 200 OK\r\nRetry-After: 3\r\nContent-Type: application/json\r\n\r\n{\"a\": \"x\\r\\n\\r\\ny\"}"
        headers, body = split_include(out)
        self.assertIn("Retry-After: 3", headers)
        self.assertEqual(json.loads(body), {"a": "x\r\n\r\ny"})
        self.assertEqual(split_include("HTTP/2.0 204 No Content\r\nX-A: 1\r\n\r\n"), ("HTTP/2.0 204 No Content\r\nX-A: 1", ""))
        self.assertEqual(split_include('{"plain": 1}'), ("", '{"plain": 1}'), "no status line: all body")
        self.assertEqual(split_include(""), ("", ""))


if __name__ == "__main__":
    unittest.main()
