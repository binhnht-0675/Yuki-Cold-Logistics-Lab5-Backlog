"""Decision 3A (22/10): the JA report embeds the FULL validated payload of the source report.

Same structure as the source payload; only the free text is replaced by its Japanese text (translation,
or the original when it is already Japanese / an identifier, or the omission note), and run.sourceLabel
(may name an organization / a private Project) by a fixed neutral text. Enum codes and signatures stay.
No issue body, no Vietnamese, no local path; JSON escaped per the source contract.
The free-text slots are listed here on purpose (independently of scripts/ja_report_payload.py).
"""
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ja_report_block_fixtures import (base_payload, check_doc, issue, ref, render_doc, rich_payload,  # noqa: E402
                                      translations_for)
from ja_report_metrics import SRC_SCHEMA  # noqa: E402  (core/schema.py of the installed tkm:estimate-swp skill)
from ja_report_text import vi_count  # noqa: E402

EMBED_RX = re.compile(r'<script id="report-data" type="application/json">(.*?)</script>', re.S)
PLAN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SCAN = os.path.join(PLAN, "tools", "scan-public-leaks.py")
HOSTILE = "</ScRiPt><!-- a & b \u2028\u2029 -->"
NEUTRAL = "estimate-swp の評価結果（対象の名前は公開版に載せない。原本 HTML の sha256 で照合）"


def valid_payload() -> dict:
    """The fixture made valid for the source validate_payload (accepted run: one correction per representative)."""
    p = base_payload()
    p["corrections"] = [{"representative": {"sourceType": "github", "issueRef": ref(5)}, "approvedScope": 2,
                         "approvedComplexity": 1, "issueSpecific": False, "rationale": "チームの基準どおり"}]
    issue(p, 5)["calibration"].update(status="approved", approvedScope=2, approvedComplexity=1)
    return p


def free_text(p: dict) -> dict:
    """{key path: text} of every free-text slot (title / rationale / ... / caveats)."""
    out = {}
    for group in ("issues", "parents"):
        for n, i in enumerate(p.get(group, [])):
            for f in ("title", "rationale", "splitReason"):
                if f in i:
                    out[(group, n, f)] = i[f]
            for f in ("assumptions", "gaps", "supportingEvidence"):
                out.update({(group, n, f, k): s for k, s in enumerate(i.get(f) or [])})
            notes = (i.get("provenance") or {}).get("notes") or []
            out.update({(group, n, "provenance", "notes", k): s for k, s in enumerate(notes)})
            if ((i.get("assessorCheck") or {}).get("witness") or {}).get("rationale") is not None:
                out[(group, n, "assessorCheck", "witness", "rationale")] = i["assessorCheck"]["witness"]["rationale"]
    out.update({("corrections", n, "rationale"): c.get("rationale") for n, c in enumerate(p.get("corrections") or [])})
    out.update({("caveats", k): s for k, s in enumerate(p.get("caveats") or [])})
    return out


def without_free_text(p: dict) -> dict:
    """The payload with every free-text slot set to None and no issue body (never embedded)."""
    q = copy.deepcopy(p)
    for path in free_text(q):
        node = q
        for step in path[:-1]:
            node = node[step]
        node[path[-1]] = None
    q["run"]["sourceLabel"] = None
    for i in q.get("issues", []) + q.get("parents", []):
        i.pop("body", None)
    return q


def embedded(doc: str):
    m = EMBED_RX.search(doc)
    return (json.loads(m.group(1)), m.group(1)) if m else (None, None)


class EmbeddedPayloadTest(unittest.TestCase):
    def test_embedded_payload_passes_the_source_validate_payload(self):
        p = valid_payload()
        emb, _ = embedded(render_doc(p)[0])
        self.assertIsNotNone(emb, 'the JA report must embed <script id="report-data" type="application/json">')
        SRC_SCHEMA.validate_payload(copy.deepcopy(emb))  # raises SchemaError when invalid

    def test_only_free_text_differs_and_it_is_the_translation(self):
        p, tr = rich_payload(), translations_for(rich_payload())
        emb, _ = embedded(render_doc(p)[0])
        self.assertIsNotNone(emb)
        self.assertEqual(without_free_text(emb), without_free_text(p))
        got, want = free_text(emb), free_text(p)
        self.assertEqual(set(got), set(want))
        translated = 0
        for path, original in want.items():
            if original in tr:
                translated += 1
                self.assertEqual(got[path], tr[original], path)
            else:
                self.assertEqual(got[path], original, path)  # Japanese already / identifier / empty
        self.assertGreaterEqual(translated, 10)
        self.assertEqual(emb["run"]["sourceLabel"], NEUTRAL)
        self.assertNotEqual(p["run"]["sourceLabel"], NEUTRAL)

    def test_issue_and_parent_identities_match_the_rows_shown(self):
        p = rich_payload()
        doc = render_doc(p)[0]
        emb, _ = embedded(doc)
        self.assertIsNotNone(emb)
        rows = re.findall(r'data-v="issue\|([^|"]+)\|final"', doc)
        self.assertEqual(sorted(i["issueRef"] for i in emb["issues"]), sorted(rows))
        self.assertEqual(len(emb["issues"]), len(p["issues"]))
        prow = re.findall(r'data-v="parent\|([^|"]+)\|final"', doc)
        self.assertEqual(sorted(x["issueRef"] for x in emb["parents"]), sorted(prow))

    def test_escaping_no_body_no_vietnamese_even_without_translations(self):
        p = valid_payload()
        issue(p, 5)["title"] = "貸出 " + HOSTILE
        issue(p, 6)["body"] = "raw issue body that must not be embedded"
        doc, _ = render_doc(p, {})
        emb, raw = embedded(doc)
        self.assertIsNotNone(emb)
        for ch in ("<", ">", "&", "\u2028", "\u2029"):
            self.assertNotIn(ch, raw)
        self.assertNotRegex(raw, re.compile(r"</script", re.I))
        self.assertEqual(issue(emb, 5)["title"], "貸出 " + HOSTILE)
        self.assertTrue(all("body" not in x for x in emb["issues"] + emb["parents"]))
        self.assertEqual(vi_count(raw), 0, "untranslated Vietnamese becomes the omission note")

    def test_public_leak_scan_passes_on_the_output(self):
        p = rich_payload()
        doc = render_doc(p)[0]
        self.assertIsNotNone(embedded(doc)[0])
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as side:
            with open(os.path.join(root, "report-ja.html"), "w", encoding="utf-8") as fh:
                fh.write(doc)
            ex = os.path.join(side, "exceptions.json")
            with open(ex, "w", encoding="utf-8") as fh:
                json.dump({"allowRepos": {"repos": ["example-org/sample-repo"], "reason": "fixture repo"}}, fh)
            r = subprocess.run([sys.executable, SCAN, "--root", root, "--exceptions", ex],
                               capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_check_verifies_the_embedded_payload(self):
        p, tr = valid_payload(), translations_for(valid_payload())
        doc = render_doc(p)[0]
        emb, raw = embedded(doc)
        self.assertIsNotNone(emb)
        checks, _ = check_doc(doc, p, tr)
        names = [n for n in checks if n.startswith("埋め込みデータ")]
        self.assertGreaterEqual(len(names), 4, names)
        self.assertEqual([n for n in names if not checks[n][0]], [])

        def tampered(change):
            data = copy.deepcopy(emb)
            change(data)
            text = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            failed = [n for n, (ok, _) in check_doc(doc.replace(raw, text), p, tr)[0].items() if not ok]
            return [n for n in failed if n.startswith("埋め込みデータ")]

        self.assertTrue(tampered(lambda d: d["issues"][0].update(finalScope=13)))
        self.assertTrue(tampered(lambda d: d["issues"][0].update(rationale="別の文")))
        self.assertTrue(tampered(lambda d: d["issues"].pop()))
        self.assertTrue(tampered(lambda d: d["issues"][0].update(body="本文")))


if __name__ == "__main__":
    unittest.main()
