"""Regression tests for the 2026-10-20 review: bare numbers, NFD letters, Scope x Complexity,
person-confirmed columns, the 'issue' term, schema version and parent sums.
Vietnamese sample text is written as \\u escapes so this public file holds none."""
import json
import os
import re
import sys
import unicodedata
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_render_estimate_report_ja import ORIGINAL, SKILL, RenderJaBase, run  # noqa: E402

PAYLOAD_RX = re.compile(r'(<script id="report-data" type="application/json">)(.*?)(</script>)', re.S)
NFD_VI = unicodedata.normalize("NFD", "Ph\u01b0\u01a1ng ph\u00e1p")
REP = "example-org/sample-repo#5"
KADAI = "\u8ab2\u984c"  # the two-kanji word for "task / problem", kept out of the public text


class PublicChecksTest(RenderJaBase):
    def variant(self, mutate, name="variant.html"):
        text = self.read(ORIGINAL)
        m = PAYLOAD_RX.search(text)
        data = json.loads(m.group(2))
        mutate(data)
        raw = json.dumps(data, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e")
        path = os.path.join(self.dir, name)
        self.write(path, text[:m.start(2)] + raw + text[m.end(2):])
        return path

    def test_bare_number_outside_data_v_fails(self):
        self.render()
        doc = self.read(self.ja)
        self.write(self.ja, doc.replace("<h2>要約</h2>", "<h2>要約</h2><p>SWP 合計 999</p>", 1))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FAIL 印のない数値", r.stdout)
        self.write(self.ja, re.sub(r'(data-v="group\|[^"]+">)3<', r"\g<1>9<", doc, count=1))
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FAIL 数値 = 埋め込みデータ", r.stdout)

    def test_nfd_vietnamese_is_detected(self):
        self.render()
        self.write(self.ja, self.read(self.ja).replace("算定方法", NFD_VI))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL ベトナム語の文字", r.stdout)
        tr = os.path.join(self.dir, "tr.json")
        self.write(tr, json.dumps({"x": NFD_VI}))
        self.assertEqual(self.render("--translations", tr, "--force").returncode, 2)

    def test_scope_complexity_and_person_columns(self):
        def confirm(d):
            d["corrections"] = [{"representative": {"sourceType": "github", "issueRef": REP}, "approvedScope": 2,
                                 "approvedComplexity": 1, "issueSpecific": False, "rationale": "チームの基準どおり"}]
            rep = next(i for i in d["issues"] if i["issueRef"] == REP)
            rep["calibration"].update(status="approved", approvedScope=2, approvedComplexity=1)
        alt = self.variant(confirm)
        self.assertEqual(self.render(original=alt).returncode, 0)
        r = self.check(original=alt)
        self.assertEqual(r.returncode, 0, r.stdout)
        doc = self.read(self.ja)
        for head in ("スキルの評価（Scope × Complexity → SWP）", "担当者の確定（Scope × Complexity → SWP）", "調整の理由"):
            self.assertIn(head, doc)
        self.assertIn(f'data-v="rep|{REP}|ascope">2<', doc)
        self.assertIn(f'data-v="rep|{REP}|acomplexity">1<', doc)
        self.assertIn("チームの基準どおり", doc)
        for n in range(4, 9):
            self.assertIn(f'data-v="issue|example-org/sample-repo#{n}|fscope">', doc)
            self.assertIn(f'data-v="issue|example-org/sample-repo#{n}|icomplexity">', doc)
        self.assertIn("| #5 | 2 × 1 → 3 | 2 × 1 → 3 | チームの基準どおり |", self.read(self.md))

    def test_missing_reason_shows_dash_and_is_noted(self):
        self.render()
        self.assertEqual(self.check().returncode, 0)
        self.assertIn("| #5 | 2 × 1 → 3 | — | —（埋め込みデータに理由なし） |", self.read(self.md))

    def test_issue_term_replaces_kadai(self):
        self.render()
        self.check()
        self.assertNotIn(KADAI, self.read(self.ja))
        self.assertNotIn(KADAI, self.read(self.md))
        self.assertIn("issue 一覧", self.read(self.ja))

    def test_schema_version_and_broken_payload(self):
        alt = self.variant(lambda d: d.update(schemaVersion="3.0"))
        r = run("render", "--html", alt, "--out", self.ja)
        self.assertEqual(r.returncode, 1)
        self.assertIn("schemaVersion", r.stdout)
        alt = self.variant(lambda d: d["issues"][0].pop("issueRef"), "noref.html")
        r = run("render", "--html", alt, "--out", self.ja)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ERROR", r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_parent_not_sum_of_children_fails(self):
        alt = self.variant(lambda d: d["parents"][1].update(finalSWP=12))
        self.render(original=alt)
        r = self.check(original=alt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL 親 = 子の合計", r.stdout)

    def test_skill_files_hold_no_vietnamese_or_course_terms(self):
        vi = re.compile("[\u00c0-\u00c3\u00c8-\u00ca\u00cc\u00cd\u00d2-\u00d5\u00d9\u00da\u00dd\u00e0-\u00e3"
                        "\u00e8-\u00ea\u00ec\u00ed\u00f2-\u00f5\u00f9\u00fa\u00fd\u0102\u0103\u0110\u0111"
                        "\u0128\u0129\u0168\u0169\u01a0\u01a1\u01af\u01b0\u1ea0-\u1ef9]")
        terms = re.compile("LAB-[0-9n]|\u63a1\u70b9|\u8b1b\u5e2b|" + KADAI)
        for dp, dn, fn in os.walk(SKILL):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for f in fn:
                with open(os.path.join(dp, f), encoding="utf-8") as fh:
                    text = unicodedata.normalize("NFC", fh.read())
                self.assertFalse(vi.search(text), f)
                self.assertFalse(terms.search(text), f)


if __name__ == "__main__":
    unittest.main()
