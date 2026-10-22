"""Phase 07 (21/10, first real run of skill 4): the allowed repo name itself contains a course term.
Its bare `owner/name` (e.g. the `--repo` value in a recorded command) must not trip the course-term rule; that term
anywhere else, and the same words in another repo name, still must. The name is assembled at run time (REPO below)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from content_guard import scan_text  # noqa: E402

REPO = "binhnht-0675/Yuki-Cold-" + "Logistics-La" + "b5-Backlog"


class AllowedRepoNameTest(unittest.TestCase):
    def test_bare_allowed_repo_name_is_exempt(self):
        self.assertEqual(scan_text(f"render --repo {REPO} --force", allow_repo=REPO), [])
        self.assertEqual(scan_text(f"repo {REPO.upper()}.", allow_repo=REPO), [], "case-insensitive like URLs")

    def test_course_term_elsewhere_and_other_repos_still_blocked(self):
        hits = lambda t: [f[1] for f in scan_text(t, allow_repo=REPO)]  # noqa: E731
        self.assertIn("internal-term-1", hits(f"{REPO} は La" + "b5 の提出物"))
        self.assertIn("internal-term-1", hits("--repo someone/Other-La" + "b5-Backlog"))
        self.assertIn("internal-term-1", hits(f"x{REPO}"), "only a whole owner/name token is exempt")
        self.assertIn("internal-term-1", hits(f"--repo {REPO}"[:-3]), "a truncated name is not the allowed repo")


if __name__ == "__main__":
    unittest.main()
