"""Contract items 5-8: calibration opening sentence and representatives (SWP chip, difficulty, reason),
corrections as score movements and rules per group, search/filters/numeric sort as progressive
enhancement, and the per-issue detail (score audit, function/activity, provenance, closed flag)."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ja_report_block_fixtures as fx  # noqa: E402


def marked(doc: str, key: str) -> list:
    return re.findall(r'data-v="%s">([^<]*)<' % re.escape(key), doc)


def section(doc: str, sid: str) -> str:
    m = re.search(r'<section id="%s">(.*?)</section>' % sid, doc, re.S)
    return m.group(1) if m else ""


class CalibrationBlocksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = fx.rich_payload()
        cls.doc, _ = fx.render_doc(cls.payload)
        cls.cal = section(cls.doc, "calibration")

    def test_opening_sentence_in_user_terms(self):
        self.assertIn("最大五件", self.cal)
        self.assertIn("五段階の難易度", self.cal)

    def test_representative_row_has_chip_difficulty_and_reason(self):
        self.assertEqual(marked(self.cal, f"rep|{fx.ref(5)}|chip"), ["3"])
        self.assertIn("<td>易しい</td>", self.cal)
        self.assertIn("中央値付近", self.cal)
        self.assertNotIn("lower-median", self.cal)

    def test_corrections_as_score_movements_and_rules_per_group(self):
        self.assertEqual(marked(self.cal, "corr|0|initial"), ["3"])
        self.assertEqual(marked(self.cal, "corr|0|approved"), ["3"])  # 2 x 1 -> 3 SWP
        self.assertIn("似た issue にも適用", self.cal)
        self.assertEqual(marked(self.cal, "rule|0|scope"), ["1"])
        self.assertEqual(marked(self.cal, "rule|0|complexity"), ["0"])
        self.assertRegex(self.cal, r"分野 API ・ 作業種別 機能開発")
        self.assertEqual(marked(self.cal, "sum|count|changed"), ["0"])

    def test_issue_specific_correction_wording(self):
        p = fx.rich_payload()
        p["corrections"][0]["issueSpecific"] = True
        doc, _ = fx.render_doc(p)
        self.assertIn("この issue だけ", section(doc, "calibration"))


class InteractionAndDetailBlocksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = fx.rich_payload()
        cls.doc, _ = fx.render_doc(cls.payload)

    def test_controls_are_progressive_enhancement(self):
        self.assertIn('<div class="controls" id="controls" hidden>', self.doc)
        for control in ('id="f-search"', 'id="f-discipline"', 'id="f-work-type"', 'id="f-confidence"',
                        'id="f-calibration"'):
            self.assertIn(control, self.doc)
        self.assertIn('<option value="low">低</option>', self.doc)
        self.assertIn('data-sort="final-swp"', self.doc)

    def test_rows_carry_filter_attributes_without_js(self):
        m = re.search(r'<tr data-search="([^"]*)" data-discipline="([^"]*)" data-work-type="([^"]*)" '
                      r'data-confidence="([^"]*)" data-calibration="([^"]*)" data-final-swp="(\d+)">', self.doc)
        self.assertIsNotNone(m)
        self.assertNotIn(" hidden>", re.sub(r'id="(controls|hours-view)" hidden', "", self.doc))

    def test_issue_detail_audit_function_activity_provenance(self):
        self.assertEqual(marked(self.doc, f"issue|{fx.ref(7)}|dfinal"), ["8"])
        self.assertIn("機能: ", self.doc)
        self.assertIn("作業: 実装", self.doc)
        self.assertIn("取得: GitHub CLI（gh）", self.doc)
        self.assertIn("取得状況: 全文", self.doc)
        self.assertIn("取得した項目: 本文、ラベル、タイトル、URL", self.doc)

    def test_changed_score_shows_initial_to_final(self):
        p = fx.rich_payload()
        six = fx.issue(p, 6)
        six.update(initialSWP=2, initialScope=2, initialComplexity=0)
        doc, _ = fx.render_doc(p)
        self.assertEqual(marked(doc, f"issue|{fx.ref(6)}|dinitial"), ["2"])
        self.assertEqual(marked(doc, "sum|count|changed"), ["1"])
        checks, _ = fx.check_doc(doc, p)
        self.assertEqual(fx.failed(checks, rich=True), [])

    def test_closed_flag(self):
        self.assertRegex(self.doc, r'data-v="issue\|%s\|final"(?:(?!</tr>).)*（クローズ）' % re.escape(fx.ref(8)))

    def test_unknown_provenance_value_fails_enum_check(self):
        p = fx.rich_payload()
        fx.issue(p, 4)["provenance"]["retrievedVia"] = "carrier-pigeon"
        doc, _ = fx.render_doc(p)
        checks, _ = fx.check_doc(doc, p)
        self.assertIn("retrievedVia:carrier-pigeon", checks["列挙値の日本語化"][1])


if __name__ == "__main__":
    unittest.main()
