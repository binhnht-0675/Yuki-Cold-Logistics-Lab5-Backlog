"""Offline tests for render-estimate-report-ja.py on a fictional estimate-swp report."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

from ja_report_block_fixtures import extract_payload, fixture_translations, valid_original_path

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPT = os.path.join(SKILL, "scripts", "render-estimate-report-ja.py")
ORIGINAL = valid_original_path()  # the shared fixture with a correction for its representative (a valid source payload)


def run(*args):
    return subprocess.run([sys.executable, SCRIPT] + list(args), capture_output=True, text=True, encoding="utf-8")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class RenderJaBase(unittest.TestCase):
    """Shared helpers (no tests here, so importing it never re-runs tests)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="swp-ja-")
        self.ja = os.path.join(self.dir, "reports", "estimate-swp-sample-ja.html")
        self.md = os.path.join(self.dir, "reports", "estimate-swp-verification-ja.md")

    def with_fixture_translations(self, extra, original):
        """Add translations for the fixture's Vietnamese texts (an untranslated text fails check).

        A --translations file given by the test is merged in (its entries win); fixture entries whose
        original is no longer in this variant's payload are left out."""
        extra = list(extra)
        mine = {}
        if "--translations" in extra:
            at = extra.index("--translations")
            with open(extra[at + 1], encoding="utf-8") as fh:
                mine = json.load(fh)
            del extra[at:at + 2]
        payload = extract_payload(self.read(original))
        merged = {**fixture_translations(payload), **mine}
        self.n_tr = getattr(self, "n_tr", 0) + 1
        path = os.path.join(self.dir, f"merged-tr-{self.n_tr}.json")
        self.write(path, json.dumps(merged, ensure_ascii=False))
        return extra + ["--translations", path]

    def render(self, *extra, original=ORIGINAL):
        return run("render", "--html", original, "--out", self.ja, *self.with_fixture_translations(extra, original))

    def check(self, *extra, original=ORIGINAL):
        return run("check", "--html", original, "--ja", self.ja, "--verification-md", self.md,
                   "--source-skill", "tkm:estimate-swp 9.9.9", *self.with_fixture_translations(extra, original))

    def read(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)


class RenderJaTest(RenderJaBase):
    def test_render_then_check_passes_and_original_untouched(self):
        before = sha(ORIGINAL)
        r = self.render()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("RESULT PASS", r.stdout)
        self.assertEqual(sha(ORIGINAL), before)
        doc = self.read(self.ja)
        self.assertIn('<html lang="ja">', doc)
        self.assertIn('data-v="sum|total|swp">21<', doc)
        self.assertIn("&lt;script&gt;", doc)  # hostile title stays inert text
        md = self.read(self.md)
        self.assertIn("判定: **合格**", md)
        self.assertIn(before, md)
        self.assertIn("estimate-swp-report-ja 0.7.0", md)
        self.assertIn("tkm:estimate-swp 9.9.9", md)
        self.assertNotIn(self.dir, md, "no absolute local paths in the recorded command")

    def test_tampered_number_fails(self):
        self.render()
        self.write(self.ja, self.read(self.ja).replace('data-v="sum|total|swp">21<', 'data-v="sum|total|swp">22<', 1))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertRegex(r.stdout, r"FAIL 数値 = 埋め込みデータ（data-v の印の付いた数値） 照合 \d+ 箇所、不一致 1\n")
        self.assertIn("| 要約 SWP 合計 SWP | 21 | 22 | × |", self.read(self.md))

    def test_vietnamese_text_fails(self):
        self.render()
        self.write(self.ja, self.read(self.ja).replace("算定方法", "Ph\u01b0\u01a1ng ph\u00e1p"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL ベトナム語の文字", r.stdout)

    def test_untranslated_text_is_omitted_and_fails_check(self):
        tr = os.path.join(self.dir, "tr.json")
        self.write(tr, json.dumps({"M\u1ed9t b\u1ea3ng m\u1edbi v\u00e0 hai r\u00e0ng bu\u1ed9c duy nh\u1ea5t.": "新しい表ひとつと一意制約ふたつ。"},
                                  ensure_ascii=False))
        r = run("render", "--html", ORIGINAL, "--out", self.ja, "--translations", tr)
        self.assertIn("省略 4 件", r.stdout)  # #7's rationale is shown twice (detail + low-confidence action)
        self.assertIn("置換 1 件", r.stdout)
        self.assertIn("新しい表ひとつと一意制約ふたつ。", self.read(self.ja))
        r = run("check", "--html", ORIGINAL, "--ja", self.ja, "--translations", tr)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FAIL 訳のない自由記述 0（日本語でない記述は訳文で置き換え） 4 件", r.stdout)
        self.assertEqual(self.render("--translations", tr, "--force").returncode, 0)
        self.assertEqual(self.check("--translations", tr).returncode, 0)
        self.write(tr, json.dumps({"x": "c\u00f2n ti\u1ebfng Vi\u1ec7t"}, ensure_ascii=False))
        r = run("render", "--html", ORIGINAL, "--out", self.ja, "--translations", tr, "--force")
        self.assertEqual(r.returncode, 2)

    def test_refuses_to_overwrite(self):
        r = run("render", "--html", ORIGINAL, "--out", ORIGINAL)
        self.assertEqual(r.returncode, 2)
        self.render()
        r = self.render()
        self.assertEqual(r.returncode, 2)
        self.assertIn("--force", r.stdout)

    def test_unmapped_enum_and_missing_payload(self):
        alt = os.path.join(self.dir, "alt.html")
        self.write(alt, self.read(ORIGINAL).replace('"workType":"test-execution"', '"workType":"mystery"'))
        self.render(original=alt)
        r = self.check(original=alt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL 列挙値の日本語化 workType:mystery", r.stdout)
        empty = os.path.join(self.dir, "empty.html")
        self.write(empty, "<html lang='vi'><body>no data</body></html>")
        r = run("render", "--html", empty, "--out", os.path.join(self.dir, "x.html"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("report-data", r.stdout)

    def test_page_names_the_verification_table_it_was_checked_against(self):
        """Review 22/10 + 23/10: the page pointed at 「照合表（estimate-swp-verification-ja.md）」 while the real table
        was estimate-swp-verification-ja-261022.md. render takes the name from --verification-md; check fails when
        the page names another table."""
        md = os.path.join(self.dir, "reports", "estimate-swp-verification-ja-261023.md")
        self.assertEqual(self.render("--verification-md", md).returncode, 0)
        self.assertIn('照合表（<span data-x="verify">estimate-swp-verification-ja-261023.md</span>）', self.read(self.ja))
        ok = run("check", "--html", ORIGINAL, "--ja", self.ja, "--verification-md", md,
                 "--source-skill", "tkm:estimate-swp 9.9.9", *self.with_fixture_translations([], ORIGINAL))
        self.assertEqual(ok.returncode, 0, ok.stdout[-600:])
        r = self.check()  # the default table name differs from the one the page names
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("FAIL 照合表の名前", r.stdout)

    def test_check_detects_other_source(self):
        self.render()
        alt = os.path.join(self.dir, "alt.html")
        self.write(alt, self.read(ORIGINAL).replace("d&#x1eef; li&#x1ec7;u h&#x01b0; c&#x1ea5;u", "d&#x1eef; li&#x1ec7;u kh&#x00e1;c"))
        r = self.check(original=alt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL 出所", r.stdout)


if __name__ == "__main__":
    unittest.main()
