"""The source skill (tkm:estimate-swp) moved when the Takumi kit was reinstalled on 24/10:
home .claude/skills/estimate-swp → home .claude/skills/tkm/skills/estimate-swp. The JA report must find its scripts in
either place (an explicit ESTIMATE_SWP_SCRIPTS wins), and say every place it looked when none exists.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from ja_report_source_location import find_source_scripts  # noqa: E402

LEGACY = (".claude", "skills", "estimate-swp", "scripts")
KIT = (".claude", "skills", "tkm", "skills", "estimate-swp", "scripts")


def make(home, parts):
    path = os.path.join(home, *parts)
    os.makedirs(os.path.join(path, "core"))
    open(os.path.join(path, "core", "__init__.py"), "w").close()
    return path


class SourceScriptsLocationTest(unittest.TestCase):
    def test_kit_layout_is_found_when_the_legacy_folder_is_gone(self):
        with tempfile.TemporaryDirectory() as home:
            kit = make(home, KIT)
            self.assertEqual(find_source_scripts(home, {}), kit)

    def test_legacy_layout_still_wins_when_both_exist(self):
        with tempfile.TemporaryDirectory() as home:
            legacy = make(home, LEGACY)
            make(home, KIT)
            self.assertEqual(find_source_scripts(home, {}), legacy)

    def test_explicit_env_wins(self):
        with tempfile.TemporaryDirectory() as home:
            make(home, KIT)
            other = make(home, ("elsewhere", "scripts"))
            self.assertEqual(find_source_scripts(home, {"ESTIMATE_SWP_SCRIPTS": other}), other)

    def test_missing_everywhere_names_every_candidate(self):
        with tempfile.TemporaryDirectory() as home:
            with self.assertRaises(ImportError) as ctx:
                find_source_scripts(home, {})
            for parts in (LEGACY, KIT):
                self.assertIn(os.path.join(home, *parts), str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
