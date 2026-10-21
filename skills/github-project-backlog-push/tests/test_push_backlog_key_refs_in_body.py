"""Team review 21/10: keys in every body section (not only 依存) must become 「#123（E07-I05-S01）」, so outsiders
can follow them; the marker and the キー footer keep the bare key. update-body may rewrite a body only when the
difference comes from those references; any other difference is a hand edit and is skipped."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "..", "_shared", "tests"))
sys.path.insert(0, os.path.join(SKILL, "..", "_shared"))
from fake_gh_harness import REPO, FakeGitHub  # noqa: E402

SCRIPT = os.path.join(SKILL, "scripts", "push-backlog.py")
EXAMPLE = os.path.join(SKILL, "assets", "example-backlog.json")


class KeyRefsInBodyTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.state = self.gh.path("state")
        os.makedirs(self.state)
        with open(os.path.join(self.state, "field-map.json"), "w", encoding="utf-8") as fh:
            json.dump(self.gh.field_map(), fh, ensure_ascii=False)
        with open(EXAMPLE, encoding="utf-8") as fh:
            data = json.load(fh)
        items = data["items"] if isinstance(data, dict) else data
        by = {i["key"]: i for i in items}
        by["E01"]["bodyJa"]["備考"] = "返却は E01-I02 で扱う。"  # E01-I02 is created after E01
        by["E01-I01"]["bodyJa"]["完了の定義"] = by["E01-I01"]["bodyJa"]["完了の定義"] + ["E01-I02-S01 と結合して確認"]
        by["E01-I02"]["bodyJa"]["概要"] = "返却を登録する（貸出は E01-I01）。"  # key already inside brackets
        self.backlog = self.gh.path("backlog.json")
        with open(self.backlog, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)

    def run_cmd(self, *args):
        return self.gh.run(SCRIPT, list(args) + ["--backlog", self.backlog, "--repo", REPO, "--state-dir", self.state])

    def issue(self, key):
        return next(i for i in self.gh.load()["issues"] if f"<!-- backlog-key: {key} -->" in i["body"])

    def test_update_body_links_keys_in_every_section_then_noop(self):
        r = self.run_cmd("apply", "--project", "9", "--pace", "0", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        n_i02 = self.issue("E01-I02")["number"]
        r = self.run_cmd("update-body", "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("WARN", r.stdout, "a difference made only of key references is not a hand edit")
        epic, story = self.issue("E01"), self.issue("E01-I01")
        self.assertIn(f"返却は #{n_i02}（E01-I02） で扱う。", epic["body"])
        self.assertIn("（E01-I02-S01） と結合して確認", story["body"])
        self.assertIn("<!-- backlog-key: E01 -->", epic["body"])
        self.assertIn("キー: E01\n", epic["body"], "the footer keeps the bare key")
        n_i01 = self.issue("E01-I01")["number"]
        self.assertIn(f"返却を登録する（貸出は #{n_i01} E01-I01）。", self.issue("E01-I02")["body"], "no nested brackets")
        n = len(self.gh.writes())
        r = self.run_cmd("update-body", "--apply")
        self.assertEqual(len(self.gh.writes()), n, "second run writes nothing")

    def test_hand_edit_outside_references_is_still_skipped(self):
        self.run_cmd("apply", "--project", "9", "--pace", "0", "--apply")
        st = self.gh.load()
        epic = next(i for i in st["issues"] if "<!-- backlog-key: E01 -->" in i["body"])
        epic["body"] = epic["body"].replace("返却は", "返却と延長は")
        self.gh.save(st)
        n = len(self.gh.writes())
        r = self.run_cmd("update-body", "--apply", "--keys", "E01")
        self.assertIn("--force-body", r.stdout)
        self.assertEqual(len(self.gh.writes()), n)


    def test_wrong_number_in_a_reference_is_put_back_and_a_changed_key_is_not(self):
        self.run_cmd("apply", "--project", "9", "--pace", "0", "--apply")
        self.run_cmd("update-body", "--apply")
        st = self.gh.load()
        epic = next(i for i in st["issues"] if "<!-- backlog-key: E01 -->" in i["body"])
        good = epic["body"]
        epic["body"] = good.replace("返却は #", "返却は #9")  # number edited by hand
        self.gh.save(st)
        n = len(self.gh.writes())
        r = self.run_cmd("update-body", "--apply", "--keys", "E01")
        self.assertNotIn("WARN", r.stdout)
        self.assertEqual(len(self.gh.writes()), n + 1, "a wrong number is written back")
        self.assertEqual(self.issue("E01")["body"], good)
        st = self.gh.load()
        epic = next(i for i in st["issues"] if "<!-- backlog-key: E01 -->" in i["body"])
        epic["body"] = good.replace("（E01-I02）", "（E01-I01）")  # the key inside the reference edited by hand
        self.gh.save(st)
        r = self.run_cmd("update-body", "--apply", "--keys", "E01")
        self.assertIn("--force-body", r.stdout)
        self.assertEqual(len(self.gh.writes()), n + 1, "a changed key is a hand edit: nothing written")


    def test_hand_added_dependency_line_is_a_hand_edit(self):
        """Team 2 (21/10): the old guard dropped the whole 依存 section, so a dependency added by hand was overwritten."""
        self.run_cmd("apply", "--project", "9", "--pace", "0", "--apply")
        self.run_cmd("update-body", "--apply")
        st = self.gh.load()
        task = next(i for i in st["issues"] if "<!-- backlog-key: E01-I01-S02 -->" in i["body"])
        self.assertIn("## 依存\n", task["body"])
        task["body"] = task["body"].replace("## 依存\n", "## 依存\n- 手で追加した前提\n")
        self.gh.save(st)
        n = len(self.gh.writes())
        r = self.run_cmd("update-body", "--apply", "--keys", "E01-I01-S02")
        self.assertIn("WARN", r.stdout)
        self.assertEqual(len(self.gh.writes()), n, "a hand-added dependency must not be overwritten")

class KeyRefFunctionsTest(unittest.TestCase):
    def test_link_is_idempotent_and_reversible(self):
        from key_refs import link_keys, unlink_keys
        nums = {"E07": 7, "E07-I05": 75, "E07-I05-S01": 751}
        text = "E07-I05-S01 と E07-I05、E07 を参照。E99 は未作成。AE07 や E07-I05-S01X は対象外"
        once = link_keys(text, nums)
        self.assertEqual(once, "#751（E07-I05-S01） と #75（E07-I05）、#7（E07） を参照。E99 は未作成。AE07 や E07-I05-S01X は対象外")
        self.assertEqual(link_keys(once, nums), once)
        self.assertEqual(unlink_keys(once), text)
        base = "https://github.com/binhnht-0675/Yuki-Cold-Logistics-Lab5-Backlog/issues"
        linked = link_keys(text, nums, url_base=base)
        self.assertIn(f"[#75]({base}/75)（E07-I05）", linked)
        self.assertEqual(link_keys(linked, nums, url_base=base), linked)
        self.assertEqual(unlink_keys(linked), text)
        inside = "共通部品（E07-I05）と確定（API-006、E07）で、E07の規則"
        out = link_keys(inside, nums)
        self.assertEqual(out, "共通部品（#75 E07-I05）と確定（API-006、#7 E07）で、#7（E07）の規則")
        self.assertEqual((link_keys(out, nums), unlink_keys(out)), (out, inside))
        self.assertEqual(unlink_keys("（#1〜#3）は対象"), "（#1〜#3）は対象")


if __name__ == "__main__":
    unittest.main()
