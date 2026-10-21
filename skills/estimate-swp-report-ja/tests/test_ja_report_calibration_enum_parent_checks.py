"""check: the report must be calibrated (accepted / calibrated, as github-project-field-writer requires), every
enum shown in the report must be in the label map, and a derived parent with a child lacking SWP fails."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_ja_report_public_checks as public_checks  # noqa: E402
from test_render_estimate_report_ja import RenderJaBase  # noqa: E402


class CalibrationEnumParentChecksTest(RenderJaBase):
    variant = public_checks.PublicChecksTest.variant

    def checked(self, mutate):
        alt = self.variant(mutate)
        r = self.render(original=alt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return self.check(original=alt)

    def test_uncalibrated_report_fails(self):
        for status in ("pending", "skipped", None):
            r = self.checked(lambda d, s=status: d["run"].update(calibrationStatus=s))
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("FAIL 校正済み", r.stdout)
            self.assertIn("RESULT FAIL", r.stdout)
            os.remove(self.ja)

    def test_calibrated_report_passes(self):
        r = self.checked(lambda d: d["run"].update(calibrationStatus="calibrated"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PASS 校正済み", r.stdout)

    def test_every_enum_group_shown_is_checked(self):
        def mutate(d):
            d["run"]["processingLevel"] = "ultra"
            d["parents"][0]["issueType"] = "saga"
            d["issues"][0]["calibration"]["status"] = "mystery-cal"
            d["representatives"][0]["selectionReasons"] = ["mystery-reason"]
        r = self.checked(mutate)
        self.assertEqual(r.returncode, 1, r.stdout)
        line = next(x for x in r.stdout.splitlines() if "列挙値の日本語化" in x)
        for found in ("processingLevel:ultra", "issueType:saga", "issueCalibration:mystery-cal",
                      "selectionReason:mystery-reason"):
            self.assertIn(found, line)

    def test_derived_parent_with_a_child_without_swp_fails(self):
        def mutate(d):
            refs = {x["issueRef"]: x for x in d["issues"] + d["parents"]}
            refs["example-org/sample-repo#8"]["finalSWP"] = None  # sums still hold if a missing SWP counted as 0
            refs["example-org/sample-repo#3"]["finalSWP"] = 8
            refs["example-org/sample-repo#1"]["finalSWP"] = 19
        r = self.checked(mutate)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FAIL 親 = 子の合計", r.stdout)
        self.assertIn("#8", next(x for x in r.stdout.splitlines() if "親 = 子の合計" in x))


if __name__ == "__main__":
    unittest.main()
