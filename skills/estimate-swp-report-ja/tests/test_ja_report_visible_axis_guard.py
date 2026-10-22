"""Decision 2A (22/10): no Scope x Complexity notation and no per-issue axis value anywhere visible.

Source contract (estimate-swp references/html-report.md): "never render S x C notation or raw axis values
anywhere visible — they live only in the embedded payload". Visible = the page minus <script> / <style>
and minus the collapsed 技術的な詳細 block (which may name the bands and the valid values). The 照合表
keeps S x C (it is the verification record, not the report). Vietnamese samples are \\u escapes.
"""
import html
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ja_report_block_fixtures import (check_doc, md_for, ref, render_doc, rich_payload,  # noqa: E402
                                      translations_for)
from ja_report_layout_check import translation_errors  # noqa: E402

SCRIPT_STYLE_RX = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TECH_RX = re.compile(r"<details[^>]*>\s*<summary>技術的な詳細.*?</details>", re.S)
AXIS_FIELDS = {"iscope", "icomplexity", "fscope", "fcomplexity", "ascope", "acomplexity"}
AXIS_WORDS_RX = re.compile(r"Scope|Complexity|×", re.I)
KEEP_10 = "Gi\u1eef 10 SWP (S5 × C3)."  # a correction reason that quotes the axes


def visible(doc: str):
    """(data-v keys, plain text) of the visible part."""
    body = TECH_RX.sub(" ", SCRIPT_STYLE_RX.sub(" ", doc))
    keys = [html.unescape(k) for k in re.findall(r'data-v="([^"]+)"', body)]
    return keys, html.unescape(re.sub(r"<[^>]+>", " ", body))


def axis_check(checks: dict):
    names = [n for n in checks if "Scope × Complexity の表記" in n]
    return (names[0], checks[names[0]]) if names else (None, None)


class VisibleAxisGuardTest(unittest.TestCase):
    def setUp(self):
        self.p = rich_payload()
        self.doc, _ = render_doc(self.p)

    def test_no_axis_cell_header_or_notation_is_visible(self):
        keys, text = visible(self.doc)
        self.assertEqual([k for k in keys if k.split("|")[2] in AXIS_FIELDS], [])
        self.assertEqual(AXIS_WORDS_RX.findall(text), [], "S x C must not be visible outside 技術的な詳細")
        tech = TECH_RX.search(self.doc)
        self.assertIsNotNone(tech, "the collapsed technical block stays")
        self.assertIn("有効な値", tech.group(0))

    def test_representative_scores_stay_checkable_as_swp(self):
        rep = ref(5)  # the fixture's representative, confirmed 2 x 1 -> 3 by a correction
        self.assertIn(f'data-v="rep|{rep}|initial">3<', self.doc)
        self.assertIn(f'data-v="rep|{rep}|final">3<', self.doc)
        for head in ("スキルの評価（SWP）", "担当者の確定（SWP）", "調整の理由"):
            self.assertIn(head, self.doc)
        checks, rows = check_doc(self.doc, self.p)
        self.assertTrue(all(r[3] for r in rows), [r for r in rows if not r[3]][:3])
        md = md_for(self.p, self.doc)
        self.assertIn("| #5 | 2 × 1 → 3 | 2 × 1 → 3 | チームの基準どおり |", md)  # 照合表 keeps S x C

    def test_check_fails_when_axis_notation_is_visible(self):
        checks, _ = check_doc(self.doc, self.p)
        name, result = axis_check(checks)
        self.assertIsNotNone(name, "check must have an item for S x C in the visible part")
        self.assertTrue(result[0], result[1])
        ja = translations_for(self.p)
        target = next(v for v in ja.values() if v in self.doc)
        for bad in (target + "（S5 × C3）", target + "（Scope を 2 に）", "スキルの評価（Scope × Complexity → SWP）"):
            checks, _ = check_doc(self.doc.replace(target, bad, 1), self.p)
            self.assertFalse(axis_check(checks)[1][0], bad)
        tech = TECH_RX.search(self.doc).group(0)
        checks, _ = check_doc(self.doc.replace(tech, tech.replace("有効な値", "Scope と Complexity の有効な値")), self.p)
        self.assertTrue(axis_check(checks)[1][0], "the technical block may name the axes")

    def test_translation_may_drop_the_axis_notation_only(self):
        p = rich_payload()
        p["corrections"][0]["rationale"] = KEEP_10
        self.assertEqual(translation_errors({KEEP_10: "10 SWP を維持。"}, p), [])
        self.assertEqual(translation_errors({KEEP_10: "10 SWP を維持（S5 × C3）。"}, p), [])
        self.assertNotEqual(translation_errors({KEEP_10: "SWP を維持。"}, p), [])
        self.assertNotEqual(translation_errors({KEEP_10: "12 SWP を維持。"}, p), [])

    def test_band_labels_of_assessor_rationales_count_as_axis_notation(self):
        """22/10 run 261022: worker rationales write the bands as "Scope 3:" / "Complexity 2:" / "S5"; the translation
        drops them (decision 2A) and must still pass, while every other number stays mandatory."""
        p = rich_payload()
        text = "Scope 3: 2 endpoints over 3 tables (RFP S3-04). Complexity 2: lock order; B saw S5 and C3."
        p["issues"][0]["rationale"] = text
        ok = "範囲：3 テーブルにまたがる 2 エンドポイント（RFP S3-04）。複雑さ：ロック順。B の評価は別。"
        self.assertEqual(translation_errors({text: ok}, p), [])
        self.assertNotEqual(translation_errors({text: ok.replace("3 テーブル", "テーブル")}, p), [],
                            "a number that is not a band label stays mandatory")
        self.assertNotEqual(translation_errors({text: ok.replace("S3-04", "S-04")}, p), [],
                            "S3-04 is a reference, not a band label")


if __name__ == "__main__":
    unittest.main()
