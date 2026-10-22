"""Negative tests (review of 2026-10-20, round 2): M5 numbers in translations, M6 number cells replaced or
dropped, M-4 content guard on the JA HTML / 照合表 and file names only in the recorded command.
Vietnamese sample text is written as \\u escapes so this public file holds none."""
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared", "tests"))
from content_guard_samples import SAMPLES  # noqa: E402
from ja_report_block_fixtures import extract_payload, fixture_translations  # noqa: E402
from test_render_estimate_report_ja import ORIGINAL, SCRIPT, RenderJaBase  # noqa: E402

PAYLOAD_RX = re.compile(r'(<script id="report-data" type="application/json">)(.*?)(</script>)', re.S)
REF4, REF6 = "example-org/sample-repo#4", "example-org/sample-repo#6"
VI_3 = "M\u1ed9t m\u00e0n h\u00ecnh, 3 tr\u1ea1ng th\u00e1i."  # "one screen, 3 states"
COMPANY = "sun" + "-asterisk"


class LayoutTranslationGuardTest(RenderJaBase):
    def variant(self, mutate, name="variant.html"):
        text = self.read(ORIGINAL)
        m = PAYLOAD_RX.search(text)
        data = json.loads(m.group(2))
        mutate(data)
        raw = json.dumps(data, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e")
        path = os.path.join(self.dir, name)
        self.write(path, text[:m.start(2)] + raw + text[m.end(2):])
        return path

    def issue(self, data, ref):
        return next(i for i in data["issues"] if i["issueRef"] == ref)

    def tr_file(self, mapping, name="tr.json"):
        path = os.path.join(self.dir, name)
        self.write(path, json.dumps(mapping, ensure_ascii=False))
        return path

    def check_fails(self, label, *extra, original=ORIGINAL):
        r = self.check(*extra, original=original)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FAIL " + label, r.stdout)
        return r

    # M5
    def test_translation_with_a_changed_number_fails(self):
        alt = self.variant(lambda d: self.issue(d, REF6).update(rationale=VI_3))
        good = self.tr_file({VI_3: "画面ひとつ、状態 3 つ。"})
        self.assertEqual(self.render("--translations", good, original=alt).returncode, 0)
        self.assertEqual(self.check("--translations", good, original=alt).returncode, 0)
        bad = self.tr_file({VI_3: "画面ひとつ、状態 5 つ。"}, "bad.json")
        self.assertEqual(self.render("--translations", bad, "--force", original=alt).returncode, 2)
        self.write(self.ja, self.read(self.ja).replace("状態 3 つ", "状態 5 つ"))
        self.check_fails("訳文", "--translations", bad, original=alt)

    def test_translation_key_not_in_payload_fails(self):
        self.render()
        tr = self.tr_file({"dummy-original": "SWP 合計 999 日"})
        self.write(self.ja, self.read(self.ja).replace("<h2>要約</h2>", '<h2>要約</h2><p><span data-t="1">SWP 合計 999 日</span></p>', 1))
        self.check_fails("訳文", "--translations", tr)

    # M6
    def test_number_cell_swapped_for_free_text_fails(self):
        self.render()
        doc = self.read(self.ja)
        cell = f'<span data-v="issue|{REF4}|dfinal">5</span>'
        self.assertIn(cell, doc)
        self.write(self.ja, doc.replace(cell, '<span data-t="1">2.0</span>'))
        self.check_fails("印の並び")

    def test_dropped_number_cells_fail(self):
        self.render()
        doc = self.read(self.ja)
        for key in (f"issue|{REF4}|dfinal", "sum|split|count"):
            cut = re.sub(r'<span data-v="%s">[^<]*</span>' % re.escape(key), "", doc)
            self.assertNotEqual(cut, doc, key)
            self.write(self.ja, cut)
            self.check_fails("網羅")

    # M-4
    def test_internal_path_in_free_text_stops_render(self):
        alt = self.variant(lambda d: self.issue(d, REF6).update(rationale=SAMPLES["path"]))
        r = self.render(original=alt)
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertFalse(os.path.exists(self.ja), "nothing is written")

    def test_check_scans_visible_text_of_ja_html(self):
        self.render()
        no_digits = "手順は " + "plans" + "/sample/readme.md を参照"  # no digit: the bare-number check cannot see it
        self.write(self.ja, self.read(self.ja).replace("<h2>要約</h2>", "<h2>要約</h2><p>" + no_digits + "</p>", 1))
        self.check_fails("内容検査")

    def test_source_label_with_company_name_is_not_shown(self):
        alt = self.variant(lambda d: d["run"].update(sourceLabel=COMPANY + " project 33"))
        self.assertEqual(self.render(original=alt).returncode, 0)
        self.assertNotIn(COMPANY, self.read(self.ja).lower())
        self.assertEqual(self.check(original=alt).returncode, 0)

    def test_recorded_command_holds_file_names_only(self):
        sub = os.path.join(self.dir, "plans", "260101-0000-sample")
        os.makedirs(sub)
        orig = os.path.join(sub, "original.html")
        self.write(orig, self.read(ORIGINAL))
        rel = lambda p: os.path.relpath(p, self.dir)  # noqa: E731
        ja, md = os.path.join(sub, "x-ja.html"), os.path.join(sub, "verification.md")
        tr = os.path.join(sub, "tr.json")
        self.write(tr, json.dumps(fixture_translations(extract_payload(self.read(orig))), ensure_ascii=False))
        for args in (["render", "--html", rel(orig), "--out", rel(ja), "--translations", rel(tr)],
                     ["check", "--html", rel(orig), "--ja", rel(ja), "--verification-md", rel(md),
                      "--translations", rel(tr)]):
            r = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True, encoding="utf-8",
                               cwd=self.dir)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = self.read(md)
        self.assertNotIn("plans" + "/", text)
        self.assertIn("--html original.html --ja x-ja.html", text)


if __name__ == "__main__":
    unittest.main()
