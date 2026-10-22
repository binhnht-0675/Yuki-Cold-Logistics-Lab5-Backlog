"""Contract items 3c and 4 (high/max): risk & action tables, team load (only with team:* labels), the
client-side SWP-hours reference view, and the second assessor (badge, A · B spread, B rationale, summary,
caveats). Free text without a translation must fail the check; B never enters a total."""
import copy
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ja_report_block_fixtures as fx  # noqa: E402

UNTRANSLATED = "訳のない自由記述 0（日本語でない記述は訳文で置き換え）"


def marked(doc: str, key: str) -> list:
    return re.findall(r'data-v="%s">([^<]*)<' % re.escape(key), doc)


def section(doc: str, sid: str) -> str:
    m = re.search(r'<section id="%s">(.*?)</section>' % sid, doc, re.S)
    return m.group(1) if m else ""


class DecisionSupportBlocksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = fx.rich_payload()
        cls.doc, _ = fx.render_doc(cls.payload)

    def test_risk_tables_carry_translated_actions(self):
        risks = section(self.doc, "risks")
        self.assertEqual(marked(risks, f"rsplit|{fx.ref(7)}|swp"), ["8"])
        self.assertEqual(marked(risks, f"rlow|{fx.ref(7)}|swp"), ["8"])
        self.assertIn("独立した issue に分けてから", risks)
        self.assertIn(fx.EXTRA_JA[fx.SPLIT_REASON], risks)
        self.assertIn(fx.EXTRA_JA[fx.GAP], risks)
        self.assertIn("見積もれる子タスクに分解", risks)
        self.assertRegex(risks, r"#9")
        self.assertNotIn(fx.SPLIT_REASON, self.doc)

    def test_no_risk_section_without_risks(self):
        p = fx.base_payload()
        fx.issue(p, 7)["confidence"] = "medium"  # the fixture's only low-confidence row
        doc, _ = fx.render_doc(p)
        self.assertNotIn('<section id="risks">', doc)

    def test_team_load_with_labels(self):
        team = section(self.doc, "team")
        self.assertEqual(marked(team, "team|backend|build"), ["8"])
        self.assertEqual(marked(team, "team|frontend|total"), ["3"])
        self.assertEqual(marked(team, "team|-|bug"), ["8"])
        self.assertEqual(marked(team, "team|-|count"), ["2", "2"])  # row + warning
        self.assertIn("（チーム未設定）", team)

    def test_no_team_section_without_labels(self):
        doc, _ = fx.render_doc(fx.base_payload())
        self.assertNotIn('<section id="team">', doc)
        self.assertNotIn("team|", doc)

    def test_hours_view_is_reference_only_and_not_persisted(self):
        hours = section(self.doc, "hours")
        self.assertIn("時間への換算（参考値）", hours)
        self.assertEqual(marked(hours, "sum|hours|rate"), ["1.27"])  # median 6/5 and 4/3
        self.assertEqual(marked(hours, "sum|hours|samples"), ["2"])
        self.assertIn('id="hours-view" hidden', hours)
        script = re.findall(r"<script>(.*?)</script>", self.doc, re.S)
        self.assertEqual(len(script), 1)
        for bad in ("innerHTML", "outerHTML", "eval(", "Function(", "localStorage", "sessionStorage",
                    "fetch(", "XMLHttpRequest", "import(", "document.write"):
            self.assertNotIn(bad, script[0])
        self.assertIn("textContent", script[0])

    def test_tampered_script_fails_the_offline_check(self):
        doc = self.doc.replace("<script>", "<script>fetch('https://example.invalid');", 1)
        checks, _ = fx.check_doc(doc, self.payload)
        self.assertFalse(checks["外部読み込み・スクリプトなし（固定の表示用スクリプトだけ）"][0])


class SecondAssessorBlocksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = fx.rich_payload()
        cls.doc, _ = fx.render_doc(cls.payload)

    def row(self, n) -> str:
        m = re.search(r'<tr data-search="[^"]*"[^>]*>(?:(?!</tr>).)*?data-v="issue\|%s\|final"(.*?)</tr>'
                      % re.escape(fx.ref(n)), self.doc, re.S)
        return m.group(0) if m else ""

    def test_contested_badge_only_when_not_identical(self):
        for n in (5, 6, 7):
            self.assertIn("評価が分かれた", self.row(n), n)
        for n in (4, 8):
            self.assertNotIn("評価が分かれた", self.row(n), n)

    def test_spread_only_when_swp_differs(self):
        self.assertEqual((marked(self.row(5), f"issue|{fx.ref(5)}|wa"), marked(self.row(5), f"issue|{fx.ref(5)}|wb")),
                         (["3"], ["4"]))
        self.assertEqual(marked(self.row(7), f"issue|{fx.ref(7)}|wb"), ["13"])
        self.assertEqual(marked(self.row(6), f"issue|{fx.ref(6)}|wb"), [])

    def test_b_rationale_translated_in_detail(self):
        self.assertIn(fx.WITNESS_JA["Late fee rules have many edge cases."], self.row(7))
        self.assertEqual(marked(self.row(7), f"issue|{fx.ref(7)}|wdetail"), ["13"])
        self.assertNotIn("Late fee rules have many edge cases.", self.doc)

    def test_summary_and_fixed_caveats(self):
        for key, value in (("agr|identical|count", "2"), ("agr|minor|count", "1"), ("agr|major|count", "1"),
                           ("agr|stratumSplit|count", "1"), ("agr|dual|count", "5"), ("agr|unseen|count", "2")):
            self.assertEqual(marked(self.doc, key)[0], value, key)
        self.assertIn("一致は検証済みという意味ではない", section(self.doc, "caveats"))
        self.assertIn("代表 issue の確認で人が見ていない", section(self.doc, "caveats"))

    def test_b_never_enters_a_total(self):
        p = copy.deepcopy(self.payload)
        for i in p["issues"]:
            i["assessorCheck"]["witness"]["swp"] = 40
        doc, _ = fx.render_doc(p)
        for key in ("sum|total|swp", "cat|all|swp", "sum|range|min", "sum|range|max", f"group|{fx.ref(2)}|swp"):
            self.assertEqual(marked(doc, key), marked(self.doc, key), key)

    def test_unavailable_agreement_states_the_reason(self):
        p = copy.deepcopy(self.payload)
        p["run"]["assessorAgreement"] = {"status": "unavailable", "reason": "witness-model-unavailable"}
        for i in p["issues"]:
            i.pop("assessorCheck")
        doc, _ = fx.render_doc(p)
        self.assertIn("評価 B を実施できなかった", doc)
        self.assertIn("評価 B に使える別のモデルがない", doc)
        self.assertNotIn("agr|", doc)

    def test_untranslated_b_rationale_fails_the_check(self):
        tr = fx.translations_for(self.payload)
        tr.pop("Late fee rules have many edge cases.")
        doc, policy = fx.render_doc(self.payload, tr)
        self.assertNotIn("Late fee rules have many edge cases.", doc)
        checks, _ = fx.check_doc(doc, self.payload, tr)
        self.assertFalse(checks[UNTRANSLATED][0])
        self.assertIn("1 件", checks[UNTRANSLATED][1])
        checks, _ = fx.check_doc(self.doc, self.payload)
        self.assertTrue(checks[UNTRANSLATED][0])


if __name__ == "__main__":
    unittest.main()
