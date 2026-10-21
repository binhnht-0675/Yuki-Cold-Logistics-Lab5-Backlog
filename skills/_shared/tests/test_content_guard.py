"""Unit tests for content_guard (fictional strings only; secrets, URLs and paths are assembled at run time
so that this file never trips the guard or the plan-side leak scanner; invisible characters are escapes)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import content_guard as cg  # noqa: E402
from content_guard_samples import SAMPLES, SECRET_TEXT  # noqa: E402

ALLOWED = "binhnht-0675/Yuki-Cold-Logistics-" + "Lab" + "5-Backlog"  # the public repo the skills write to
GH = "https://git" + "hub.com/"
OTHER = "other-org/" + "private-repo"


def cats(text, allow=None):
    return {f[0] for f in cg.scan_text(text, allow)}


class ContentGuardTest(unittest.TestCase):
    def test_each_category_sample_is_found(self):
        for cat, text in SAMPLES.items():
            with self.subTest(cat=cat):
                self.assertIn(cat, cats(text))

    def test_more_negative_variants(self):
        cases = {
            "secret": ["AK" + "IA" + "ABCDEFGHIJKLMNOP", "gh" + "p_" + "a" * 30, "sb" + "_secret_" + "x" * 12,
                       "ey" + "JhbGciOiJIUzI1NiJ9", "-----BEGIN" + " RSA PRIVATE KEY-----"],
            "path": ["/Us" + "ers/someone/x", "proto" + "type/src/app.ts", ".e" + "nv.local を読む", "nop" + "-bai/README"],
            "ctrl": ["行末\r", "見えない\u200b文字", "向き\u202e反転"],
            "term": ["講" + "師の確認", "課" + "題として提出", "lab" + "5 の範囲"],
            "internal": ["https://" + "docs.google" + ".com/document/d/x", "https://example.atlas" + "sian.net/browse/X-1",
                         GH + OTHER + "/blob/main/a.md"],
        }
        for cat, texts in cases.items():
            for t in texts:
                with self.subTest(cat=cat, text=repr(t)):
                    self.assertIn(cat, cats(t))

    def test_clean_japanese_and_allowed_forms_pass(self):
        ok = ["貸出を登録する API を作る。\n- [ ] 二重貸出は 409", "process.e" + "nv.API_URL を使う",
              ".e" + "nv.example を更新", "通知元 noreply" + "@" + "example.com", "利用者 user" + "@" + "example.com",
              "タブ\tと改行\nは可", "温度帯は −18℃ 以下 \u00d7 3 区分", GH + "me/pub/blob/v1/docs/specs/A.md#L3",
              "raw.githubuser" + "content.com/me/pub/v1/docs/a.md"]
        for t in ok:
            with self.subTest(text=t):
                self.assertEqual(cg.scan_text(t, "me/pub"), [])

    def test_allowed_repo_is_case_insensitive_but_exact(self):
        url = GH + "Me/Pub/blob/v1/docs/A.md"
        self.assertEqual(cats(url, "me/pub"), set())
        self.assertEqual(cats(url, "me/pub2"), {"internal"})

    def test_allowed_repo_url_exempts_only_owner_and_repo(self):
        """Only `https://github.com/<owner>/<repo>` is exempt; the path / query after it is still scanned."""
        base = GH + ALLOWED
        self.assertEqual(cg.scan_text(base.lower() + "/issues/12", ALLOWED), [])
        self.assertEqual(cg.scan_text(base + "/blob/main/docs/specs/A.md#L3", ALLOWED.upper()), [])
        cases = {
            "path": [base + "/blob/main/" + "plans" + "/a.md", base + "/blob/main/.e" + "nv", base + "/tree/main/proto" + "type/src"],
            "secret": [base + "/issues?token=" + "gh" + "p_" + "a" * 30],
            "email": [base + "/issues?q=taro.yamada" + "@" + "corp-sample.co.jp"],
            "term": [base + "/blob/main/" + "LAB" + "-5.md"],
        }
        for cat, urls in cases.items():
            for url in urls:
                with self.subTest(cat=cat, url=url):
                    self.assertIn(cat, cats(url, ALLOWED))
        self.assertIn("internal", cats(GH + OTHER + "/issues/1", ALLOWED))

    def test_allowed_repo_name_with_internal_term_passes(self):
        """The allowed repo's own name matches an internal-term pattern: exempt inside its URL only."""
        base = GH + ALLOWED
        self.assertEqual(cg.scan_text(base.upper() + "/issues/12 と " + base.lower(), ALLOWED), [])
        self.assertEqual(cg.scan_text("git" + "hub.com/" + ALLOWED + "/issues", ALLOWED), [])  # no scheme
        self.assertIn("term", cats(base + "/issues/12", "me/pub"))
        self.assertIn("term", cats("repo " + ALLOWED.split("/")[1], ALLOWED))  # bare name is not a URL

    def test_review_261020_holes_are_closed(self):
        cases = {
            "email": ["my" + "noreply" + "@" + "mail-sample.com", "a.no-reply.b" + "@" + "corp-sample.co.jp"],
            "secret": ["xo" + "xb-1234567890-abcdefghij", "AI" + "za" + "B" * 35],
            "internal": ["gist.git" + "hub.com/someone/abc123", "raw.githubuser" + "content.com/" + OTHER + "/main/a.md",
                         "git" + "hub.com/" + OTHER, "team.no" + "tion.site/page-1", "drive.goo" + "gle.com/file/d/x"],
            "ctrl": ["段落\u2028区切り"],
        }
        for cat, texts in cases.items():
            for t in texts:
                with self.subTest(cat=cat, text=repr(t)):
                    self.assertIn(cat, cats(t, "me/pub"))

    def test_location_section_and_one_finding_per_rule_per_line(self):
        body = "<!-- k -->\n\n## 概要\nplans" + "/a plans" + "/b\n## 備考\nok"
        (f,) = cg.scan_entries([("K1", "body", body)])
        self.assertEqual((f.key, f.field, f.category, f.line, f.col, f.section), ("K1", "body", "path", 4, 1, "概要"))

    def test_guard_masks_secrets_and_returns_exit_code(self):
        out = []
        rc = cg.guard([("K9", "comment", SAMPLES["secret"]), ("K9", "title", SAMPLES["email"])], "a/b", out.append)
        self.assertEqual(rc, cg.EXIT_CONTENT_BLOCKED)
        text = "\n".join(out)
        self.assertNotIn(SECRET_TEXT, text)
        self.assertNotIn("taro.yamada", text)
        self.assertIn("K9 comment 行1", text)
        self.assertIn("4 秘密情報のパターン 1", text)
        self.assertIn("書き込み 0 件", text)

    def test_report_closing_line_is_optional(self):
        findings = cg.scan_entries([("K1", "title", SAMPLES["path"])])
        default, custom = [], []
        cg.report(findings, default.append)
        cg.report(findings, custom.append, closing="HTML を書き出しませんでした。")
        self.assertEqual(default[-1], cg.STOP_LINE)
        self.assertEqual((custom[-1], custom[:-1]), ("HTML を書き出しませんでした。", default[:-1]))

    def test_guard_clean_returns_zero(self):
        out = []
        self.assertEqual(cg.guard([("K1", "title", "返却処理")], None, out.append), 0)
        self.assertIn("OK", out[0])


if __name__ == "__main__":
    unittest.main()
