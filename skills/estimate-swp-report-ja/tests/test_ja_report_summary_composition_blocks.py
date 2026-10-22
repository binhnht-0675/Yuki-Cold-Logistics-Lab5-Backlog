"""Contract items 1, 2, 3, 3a, 3b, 4 (low level): summary with uncertainty range, exclusions, tiles and SWP
distribution; methodology details; scope banner and old-estimate diff; planned-vs-rework composition;
group subtotals and the container table. Every number is a data-v marker the checker verifies."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ja_report_block_fixtures as fx  # noqa: E402


def marked(doc: str, key: str) -> list:
    return re.findall(r'data-v="%s">([^<]*)<' % re.escape(key), doc)


class SummaryCompositionBlocksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = fx.rich_payload()
        cls.doc, _ = fx.render_doc(cls.payload)

    def test_rich_run_passes_every_check(self):
        checks, rows = fx.check_doc(self.doc, self.payload)
        self.assertEqual(fx.failed(checks, rich=True), [])
        self.assertTrue(rows)

    def test_uncertainty_range_with_formula(self):
        # high: #4 5, #8 2 keep; medium #5 3 and #6 3 -> 2..4; low #7 8 -> 6..9 (valid SWP steps)
        self.assertEqual(marked(self.doc, "sum|range|min")[0], "17")
        self.assertEqual(marked(self.doc, "sum|range|max")[0], "24")
        self.assertEqual(marked(self.doc, "sum|range|uncertain")[0], "3")
        self.assertIn("確信度が「高」の issue は点数のまま", self.doc)

    def test_exclusions_split_low_and_tiles(self):
        self.assertIn("合計に含まない", self.doc)
        self.assertRegex(self.doc, r"合計に含まない[^。]*#9")
        self.assertEqual(marked(self.doc, "sum|split|count")[0], "1")
        self.assertEqual(marked(self.doc, "sum|conf|low")[0], "1")
        self.assertEqual(marked(self.doc, "sum|low|swp")[0], "8")
        self.assertEqual(marked(self.doc, "sum|state|open")[0], "4")
        self.assertEqual(marked(self.doc, "sum|state|closed")[0], "1")
        self.assertIn('class="tiles"', self.doc)

    def test_swp_distribution_table(self):
        dist = {m.group(1): m.group(2) for m in re.finditer(r'data-v="dist\|(\d+)\|count">(\d+)<', self.doc)}
        self.assertEqual(dist, {"2": "1", "3": "2", "5": "1", "8": "1"})
        self.assertIn("SWP の分布", self.doc)

    def test_planned_vs_rework_composition(self):
        want = {"cat|build|swp": "11", "cat|test|swp": "2", "cat|planned|swp": "13", "cat|bug|swp": "8",
                "cat|all|swp": "21", "cat|bug|pct": "38", "cat|planned|pct": "62", "cat|bug|count": "1"}
        for key, value in want.items():
            self.assertEqual(marked(self.doc, key)[0], value, key)
        self.assertIn("計画の合計", self.doc)
        self.assertIn("不具合・手戻り", self.doc)

    def test_methodology_details_hours_reference_only(self):
        self.assertIn('<details id="tech-details"><summary>技術的な詳細', self.doc)
        self.assertIn("時間への換算は参考値", self.doc)

    def test_scope_banner_and_existing_estimate_diff(self):
        self.assertIn('id="scope"', self.doc)
        self.assertEqual(marked(self.doc, "sel|byStatus|count")[0], "2")
        self.assertIn("状態で除外", self.doc)
        self.assertEqual(marked(self.doc, f"diff|{fx.ref(4)}|old")[0], "3")
        self.assertEqual(marked(self.doc, f"diff|{fx.ref(4)}|delta")[0], "2")
        self.assertEqual(marked(self.doc, f"diff|{fx.ref(6)}|hours")[0], "4")

    def test_group_subtotals_and_container_table(self):
        self.assertEqual(marked(self.doc, f"group|{fx.ref(2)}|swp")[0], "11")
        self.assertEqual(marked(self.doc, f"parent|{fx.ref(2)}|initial")[0], "11")
        self.assertRegex(self.doc, r"<td>[^<]*<span data-t=\"1\">#4</span>[^<]*<span data-t=\"1\">#5</span>")

    def test_low_level_caveat_only_at_level_low(self):
        low = fx.base_payload()
        doc, _ = fx.render_doc(low)
        self.assertIn("処理レベル「低」: issue の内容だけで評価", doc)
        self.assertNotIn("処理レベル「低」: issue の内容だけで評価", self.doc)

    def test_empty_run_is_readable_and_fails_only_the_calibration_gate(self):
        # A valid empty run is "skipped" with a caveat (source schema), so the reviewed-calibration gate fails.
        empty = fx.base_payload()
        empty.update(issues=[], parents=[], representatives=[], corrections=[], calibrationRules=[],
                     caveats=["対象の issue はない。"])
        empty["run"]["calibrationStatus"] = "skipped"
        doc, _ = fx.render_doc(empty)
        self.assertIn("対象の issue はありません", doc)
        self.assertIn("<h2>算定方法</h2>", doc)
        checks, _ = fx.check_doc(doc, empty)
        self.assertEqual([x.split("（")[0] for x in fx.failed(checks)], ["校正済み"])

    def test_wrong_range_value_fails_the_number_check(self):
        doc = self.doc.replace('data-v="sum|range|max">24<', 'data-v="sum|range|max">25<', 1)
        checks, _ = fx.check_doc(doc, self.payload)
        self.assertFalse(checks["数値 = 埋め込みデータ（data-v の印の付いた数値）"][0])

    def test_verification_table_names_the_new_rows(self):
        md = fx.md_for(self.payload, self.doc)
        for name in ("要約 不確かさの幅 最小", "SWP の分布 SWP 8 件数", "区分 不具合・手戻り SWP",
                     "除外 状態で除外 件数", "既存の見積もり #4 差"):
            self.assertIn(name, md)


if __name__ == "__main__":
    unittest.main()
