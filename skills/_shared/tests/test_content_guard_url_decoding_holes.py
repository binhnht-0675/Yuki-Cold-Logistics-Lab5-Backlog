"""Review 22/10 (teams 1 and 2): three holes in how the tail of an allowed GitHub URL is decoded.
1 a percent-decoded tail was not checked for GitHub URLs to other repos;
2 the `..` check cut the decoded tail at `#` / `?`, so an encoded `%23` / `%3f` hid a traversal;
3 decoding stopped after 4 layers, so a path encoded 5 times slipped.
Fictional strings only, assembled at run time."""
import os
import sys
import unittest
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import content_guard as cg  # noqa: E402

ALLOWED = "binhnht-0675/Yuki-Cold-Logistics-" + "Lab" + "5-Backlog"
GH = "https://git" + "hub.com/"
BASE = GH + ALLOWED


def enc(text, layers):
    for _ in range(layers):
        text = urllib.parse.quote(text, safe="")
    return text


def rules(text):
    return {(f[0], f[1]) for f in cg.scan_text(text, ALLOWED)}


class DecodedTailOtherRepoTest(unittest.TestCase):
    def test_decoded_tail_naming_another_repo_is_blocked(self):
        for t in [BASE + "/issues?next=https%3A%2F%2Fgit" + "hub.com%2Fevil%2Fx",
                  BASE + "/issues?next=git" + "hub.com%2Fevil%2Fx",
                  BASE + "/issues?next=" + enc(GH + "evil/x", 3)]:
            with self.subTest(text=t):
                self.assertIn(("internal", "github-other-repo"), rules(t))

    def test_decoded_tail_naming_an_allowed_repo_stays_clean(self):
        allow = [ALLOWED, "example-org/sample-repo"]
        t = BASE + "/issues?next=" + enc(GH + "example-org/sample-repo/issues/3", 2)
        self.assertEqual(cg.scan_text(t, allow), [])
        # the name of the allowed repo stays literal in the encoded form, so only the term rule may fire on it
        t = BASE + "/issues?next=" + enc(BASE + "/issues/3", 2)
        self.assertNotIn(("internal", "github-other-repo"), rules(t))


class EncodedQueryMarkTraversalTest(unittest.TestCase):
    def test_encoded_hash_or_question_mark_cannot_hide_a_traversal(self):
        for mark in ["%23", "%3f", "%3F", "%2523", "%253f"]:
            t = BASE + "/blob/main" + mark + "/../../../evil/x"
            with self.subTest(mark=mark):
                self.assertIn(("internal", "github-other-repo"), rules(t))

    def test_backslash_counts_as_a_path_separator(self):
        for t in [BASE + "/blob/main/..\\..\\..\\evil/x", BASE + "/blob/main/..%5c..%5c..%5cevil/x"]:
            with self.subTest(text=t):
                self.assertIn(("internal", "github-other-repo"), rules(t))

    def test_dots_after_a_literal_query_mark_stay_clean(self):
        self.assertEqual(cg.scan_text(BASE + "/issues/12?from=/../x", ALLOWED), [])


class DeepEncodingTest(unittest.TestCase):
    def test_path_encoded_5_and_8_times_is_caught(self):
        for layers in (5, 8):
            t = BASE + "/blob/main" + enc("/plan" + "s/hidden", layers)
            with self.subTest(layers=layers):
                self.assertIn(("path", "plans-dir"), rules(t))

    def test_encoding_deeper_than_the_bound_is_a_finding(self):
        t = BASE + "/blob/main" + enc("/x", 20)
        self.assertIn(("internal", "deep-percent-encoding"), rules(t))

    def test_normal_allowed_url_with_space_and_colon_stays_clean(self):
        for t in [BASE + "/issues?q=is%3Aopen%20label%3Abug", BASE + "/blob/main/docs/a%20b.md#L3"]:
            with self.subTest(text=t):
                self.assertEqual(cg.scan_text(t, ALLOWED), [])


if __name__ == "__main__":
    unittest.main()
