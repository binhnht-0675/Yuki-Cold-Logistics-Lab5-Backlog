"""Review 20/10 round 2 (M-2, L1, I-1): NFKC view, format characters, new terms / names / secrets,
GitHub URLs that point elsewhere, home-directory paths. Fictional strings only, assembled at run time;
every non-Japanese special character is written as an escape."""
import os
import sys
import unicodedata
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import content_guard as cg  # noqa: E402

ALLOWED = "binhnht-0675/Yuki-Cold-Logistics-" + "Lab" + "5-Backlog"
GH = "https://git" + "hub.com/"
OTHER = "other-org/" + "private-repo"


def fw(text):
    """Full-width form of the ASCII letters / digits / symbols in text."""
    return "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in text)


def cats(text, allow=ALLOWED):
    return {f[0] for f in cg.scan_text(text, allow)}


class NormalizationTest(unittest.TestCase):
    def test_full_width_forms_are_caught(self):
        cases = {"path": [fw("plans" + "/a.md"), fw("/Us" + "ers/") + "someone", fw("~/") + "x"],
                 "term": [fw("LAB" + "-5"), "LAB" + fw("5")], "email": ["taro" + fw("@") + "corp-sample.co.jp"],
                 "internal": [fw("sun-" + "asterisk")], "secret": [fw("gh" + "p_" + "A" * 30)]}
        for cat, texts in cases.items():
            for t in texts:
                with self.subTest(cat=cat, text=repr(t)):
                    self.assertIn(cat, cats(t))

    def test_every_format_character_is_blocked(self):
        missing = [hex(c) for c in range(0x110000)
                   if unicodedata.category(chr(c)) == "Cf" and not cg.CTRL_RX.match(chr(c))]
        self.assertEqual(missing, [])
        for ch in ["\u00ad", "\u034f", "\u2061", "\ufe0f", "\U000e0041", "\u3164", "\u200b"]:
            with self.subTest(ch=hex(ord(ch))):
                self.assertIn("ctrl", cats("ok" + ch + "ok"))

    def test_invisible_chars_cannot_hide_a_rule(self):
        cases = {"path": "pla\u00adns/a", "internal": "sun-\u00ad" + "asterisk", "term": "LAB\u034f5"}
        for cat, t in cases.items():
            with self.subTest(cat=cat):
                self.assertEqual(cats(t), {"ctrl", cat})

    def test_position_is_a_column_of_the_original_line(self):
        found = {f[0]: f for f in cg.scan_text("x\n見\u00ad plans" + "/a", None)}
        self.assertEqual((found["ctrl"][2], found["ctrl"][3]), (2, 2))
        self.assertEqual((found["path"][2], found["path"][3]), (2, 4))
        (f,) = cg.scan_text(fw("ab") + "\u3000" + fw("plans" + "/") + "x")
        self.assertEqual((f[0], f[3]), ("path", 4))

    def test_vietnamese_nfd_with_breve_only(self):
        self.assertEqual(cats(unicodedata.normalize("NFD", "n\u0103m")), {"vi"})
        self.assertEqual(cats("a\u034f\u0306"), {"ctrl", "vi"})  # a joiner between letter and mark


class NewRulesTest(unittest.TestCase):
    def test_terms_names_and_secrets(self):
        cases = {
            "term": ["講" + "座の資料"],
            "internal": ["Su" + "n* の社内", "su" + "n asterisk", "SU" + "N_ASTERISK", "サン" + "アスタリスク",
                         "\uff7b\uff9d" + "\uff71\uff7d\uff80\uff98\uff7d\uff78"],
            "secret": ["sb" + "p_" + "a" * 40, "pass" + "word: hunter2x", "PASS" + "WORD = x", "pass" + "wd=abc"],
        }
        for cat, texts in cases.items():
            for t in texts:
                with self.subTest(cat=cat, text=repr(t)):
                    self.assertIn(cat, cats(t))

    def test_home_directories(self):
        for t in ["~" + "/Claude/Projects/x", "C:" + "\\Us" + "ers\\someone\\x", "c:/us" + "ers/someone", "/priv" + "ate/tmp/x"]:
            with self.subTest(text=t):
                self.assertIn("path", cats(t))

    def test_github_urls_to_other_repos(self):
        api = "https://api.git" + "hub.com/repos/"
        for t in [api + OTHER, "http://git" + "hub.com:443/" + OTHER, GH + ALLOWED + "/../../" + OTHER,
                  GH + ALLOWED + "/blob/main/%2e%2e/%2e%2e/" + OTHER, GH + "users/other-org/projects/3",
                  "https://x@git" + "hub.com/" + OTHER]:
            with self.subTest(text=t):
                self.assertIn("internal", cats(t))

    def test_allowed_forms_stay_clean(self):
        api = "https://api.git" + "hub.com/repos/"
        for t in [api + ALLOWED.upper() + "/issues", "git" + "hub.com:443/" + ALLOWED + "/issues/3",
                  GH + "users/" + ALLOWED.split("/")[0].upper() + "/projects/3", GH + ALLOWED + "/issues/12 ../x",
                  "パスワード\uff08別途連絡\uff09", "Sunday の朝", "10\uff5e20 件"]:
            with self.subTest(text=t):
                self.assertEqual(cg.scan_text(t, ALLOWED), [])

    def test_percent_encoded_tail_of_allowed_url_is_scanned_decoded(self):
        """Review 21/10 phase 07 (team 2): the tail was decoded only for the `..` check, so an encoded path slipped."""
        for t in [GH + ALLOWED + "/blob/main%2fplan" + "s%2fhidden", GH + ALLOWED + "/blob/main%252fplan" + "s%252fx",
                  GH + ALLOWED + "/tree/x?p=%7e%2f" + "Claude"]:
            with self.subTest(text=t):
                self.assertIn("path", cats(t))
        self.assertEqual(cg.scan_text(GH + ALLOWED + "/issues?q=is%3Aopen%20label%3Abug", ALLOWED), [])

    def test_allow_repo_list(self):
        url = GH + "example-org/sample-repo/issues/1"
        self.assertEqual(cg.scan_text(url, [ALLOWED, "example-org/sample-repo"]), [])
        self.assertEqual(cats(url, [ALLOWED]), {"internal"})


class TestFilesHygieneTest(unittest.TestCase):
    def test_test_files_hold_no_raw_invisible_characters(self):
        for name in sorted(os.listdir(HERE)):
            if name.endswith(".py"):
                with open(os.path.join(HERE, name), encoding="utf-8") as fh:
                    bad = [hex(ord(c)) for c in fh.read() if cg.CTRL_RX.match(c) and c not in "\n\t"]
                with self.subTest(name=name):
                    self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
