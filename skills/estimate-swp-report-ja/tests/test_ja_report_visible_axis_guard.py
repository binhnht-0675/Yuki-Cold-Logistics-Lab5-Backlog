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

    def _axis_ok(self, bad: str) -> bool:
        ja = translations_for(self.p)
        target = next(v for v in ja.values() if v in self.doc)
        checks, _ = check_doc(self.doc.replace(target, target + bad, 1), self.p)
        return axis_check(checks)[1][0]

    def test_review_22_10_full_width_colon_and_japanese_band_labels_are_axis_notation(self):
        """Review team 22/10: full-width 「Ｓ５ × Ｃ３」, "Scope: 3" and Japanese band labels slipped through."""
        for bad in ("（Ｓ５ × Ｃ３）", "（Ｓ×Ｃ）", "（スコープ 3、複雑度 2）", "（範囲 3 / 複雑さ 2）", "（範囲：３）",
                    "（スコープは 3）", "（Scope: 3, Complexity: 2）"):
            self.assertFalse(self._axis_ok(bad), bad)
        p = rich_payload()
        text = "Keep 10 SWP (Scope: 3, Complexity: 2)."
        p["corrections"][0]["rationale"] = text
        self.assertEqual(translation_errors({text: "10 SWP を維持。"}, p), [])
        full = "Keep 10 SWP (Ｓ５ × Ｃ３)."
        p["corrections"][0]["rationale"] = full
        self.assertEqual(translation_errors({full: "10 SWP を維持。"}, p), [])

    def test_counts_after_a_scope_heading_are_not_band_labels(self):
        """Assessor rationales open with "Scope: 3 new tables" — the 3 is a count, the translation must keep it."""
        # run 261023: a thousands separator or a run of values is a count, not a lone band value
        for ok in ("（範囲:3 セクションを一覧に追加）", "（範囲:2個のエンドポイント）", "（複雑さ:4 ステータス）",
                   "（複雑さ:4つの表示状態）", "（複雑さ：1,000行ごとのチャンク分割）", "（複雑さ：239/240/241分の境界）"):
            self.assertTrue(self._axis_ok(ok), ok)
        p = rich_payload()
        text = "Scope: 3 new tables. Complexity: 4 statuses."
        p["issues"][0]["rationale"] = text
        self.assertEqual(translation_errors({text: "範囲:3 テーブル。複雑さ:4 ステータス。"}, p), [])
        self.assertNotEqual(translation_errors({text: "範囲:テーブル。複雑さ:ステータス。"}, p), [])

    def test_run_261023_vietnamese_reviewer_band_labels(self):
        """Run 261023: reviewers write sample rationales in Vietnamese (axes noted as "<scope> 8, <difficulty> 1"
        or "<difficulty> at level 2"); the translation drops those band values and the page must not show 「範囲8」
        or 「難易度は水準2」. A count after the label ("<scope> 3 tables") stays mandatory."""
        for bad in ("（範囲8、複雑さ1）", "（難易度は水準2とする）", "（難易度はレベル2）"):
            self.assertFalse(self._axis_ok(bad), bad)
        for ok in ("（難易度は通常水準とする）", "（範囲は変わらない）"):
            self.assertTrue(self._axis_ok(ok), ok)
        p = rich_payload()
        axes = "Gi\u1eef 10. Ghi tr\u1ee5c: ph\u1ea1m vi 8, \u0111\u1ed9 kh\u00f3 1."
        level = "Kh\u00f4ng backfill n\u00ean \u0111\u1ed9 kh\u00f3 \u1edf m\u1ee9c 2, ch\u01b0a t\u1edbi m\u1ee9c migration."
        count = "Ph\u1ea1m vi 3 b\u1ea3ng m\u1edbi."
        for text, ja in ((axes, "10 を維持する。評価軸は記録した。"), (level, "バックフィルがないため難易度は中程度とする。")):
            p["corrections"][0]["rationale"] = text
            self.assertEqual(translation_errors({text: ja}, p), [], text)
        p["corrections"][0]["rationale"] = count
        self.assertNotEqual(translation_errors({count: "新しいテーブルが対象。"}, p), [],
                            "a count after the label is not a band value")

    def test_review_23_10_bracketed_values_and_unaccented_vietnamese(self):
        """Review team 23/10: a band value followed or wrapped by a bracket 「範囲8（42表）」「Scope（3）」 and Vietnamese
        axis labels written without diacritics are axis notation; counts such as 「1,000行」「239/240/241分」 are not."""
        for bad in ("（範囲8（42表））", "（複雑さ3（移行））", "（難易度2（通常））", "（Scope（3））", "（複雑さ(2)）"):
            self.assertFalse(self._axis_ok(bad), bad)
        for ok in ("（複雑さ：1,000行ごとのチャンク分割）", "（複雑さ：239/240/241分の境界）"):
            self.assertTrue(self._axis_ok(ok), ok)
        p = rich_payload()
        for text, ja in (("Giu 10. Ghi truc: pham vi 8, do kho 1.", "10 を維持する。評価軸は記録した。"),
                         ("Khong backfill nen do kho o muc 2, chua toi muc migration.", "難易度は中程度とする。")):
            p["corrections"][0]["rationale"] = text
            self.assertEqual(translation_errors({text: ja}, p), [], text)
        count = "Pham vi 3 bang moi."
        p["corrections"][0]["rationale"] = count
        self.assertNotEqual(translation_errors({count: "新しいテーブルが対象。"}, p), [])

    def test_product_names_are_not_lone_band_labels(self):
        """"Amazon S3" is a product, not band S3; a lone S5 / C3 of an assessor rationale stays axis notation."""
        for ok in ("（Amazon S3 に退避）", "（AWS S3 に保存）", "（S3 バケットに保存）", "（S3 bucket）"):
            self.assertTrue(self._axis_ok(ok), ok)
        for bad in ("（B は S5 と C3）", "（C3）"):
            self.assertFalse(self._axis_ok(bad), bad)
        p = rich_payload()
        text = "Back up to Amazon S3 nightly."
        p["issues"][0]["rationale"] = text
        self.assertEqual(translation_errors({text: "毎晩 Amazon S3 にバックアップ。"}, p), [])
        self.assertNotEqual(translation_errors({text: "毎晩 Amazon にバックアップ。"}, p), [],
                            "the 3 of S3 is part of the product name and stays mandatory")


if __name__ == "__main__":
    unittest.main()
