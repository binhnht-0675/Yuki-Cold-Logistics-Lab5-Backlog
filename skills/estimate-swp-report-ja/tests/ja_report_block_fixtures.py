"""In-process helpers for the content-block tests (no subprocess: render + check in one process).

rich_payload() turns the fictional fixture into a run that has every block of the estimate-swp report
contract: second assessor (level max) with contested rows, a split recommendation, low confidence with a
gap, a needs-breakdown container, team:* labels, a closed issue, a bug, existing estimates, a selection
scope, a correction and a calibration rule. Free text that is not Japanese gets a translation in
translations_for(); the Vietnamese originals are taken from the fixture payload (none typed here).
base_payload() is the shared fixture made valid for the source validate_payload (an accepted run needs a
correction for every representative); valid_original_path() writes it into a fictional original HTML.
The rich payload is NOT a valid source payload (#7 split at non-terminal axes, a partial assessorCheck),
kept for block coverage: failed(checks, rich=True) sets aside exactly that one schema item.
"""
import copy
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "..", "_shared"))
sys.path.insert(0, os.path.join(SKILL, "scripts"))

from estimate_swp_payload import extract_payload  # noqa: E402
from ja_report_check import run_checks, verification_md  # noqa: E402
from ja_report_html import render  # noqa: E402
from ja_report_payload import safe_json  # noqa: E402
from ja_report_payload_check import VALID as SOURCE_SCHEMA_CHECK  # noqa: E402
from ja_report_text import TextPolicy, load_labels  # noqa: E402

FIXTURE_HTML = os.path.join(SKILL, "..", "_shared", "tests", "fixtures", "example-estimate-swp-original.html")
PAYLOAD_RX = re.compile(r'(<script id="report-data" type="application/json">)(.*?)(</script>)', re.S)
_VALID_ORIGINAL = []
REPO = "example-org/sample-repo"
ORIGINAL_BYTES = b"fixture-original"
SOURCE_SHA = hashlib.sha256(ORIGINAL_BYTES).hexdigest()
FIXTURE_JA = {  # field of the fixture payload -> Japanese
    ("issue", "#4", "rationale"): "新しい表ひとつと一意制約ふたつ。",
    ("issue", "#6", "rationale"): "画面ひとつ、状態みっつ。",
    ("issue", "#7", "rationale"): "延滞料金の計算に境界条件が多い。",
    ("caveat", "0", ""): "処理レベル「低」: issue の内容だけを使用。",
}
WITNESS = {"#4": (5, "identical", "One table with two unique keys."),
           "#5": (4, "minor", "One endpoint, a few error branches."),
           "#6": (3, "stratum-split", "A screen with several states, mostly UI."),
           "#7": (13, "major", "Late fee rules have many edge cases."),
           "#8": (2, "identical", "Six end-to-end cases.")}
WITNESS_JA = {"One table with two unique keys.": "表ひとつと一意キーふたつ。",
              "One endpoint, a few error branches.": "エンドポイントひとつと、いくつかのエラー分岐。",
              "A screen with several states, mostly UI.": "状態がいくつかある画面。ほぼ UI。",
              "Late fee rules have many edge cases.": "延滞料金の規則に境界のケースが多い。",
              "Six end-to-end cases.": "通しのケースが六つ。"}
SPLIT_REASON = "Late fee calculation should be its own issue."
GAP = "Late fee rules are not written down."
EXTRA_JA = {SPLIT_REASON: "延滞料金の計算は別の issue に分けるべき。", GAP: "延滞料金の規則が文書になっていない。"}


def ref(n) -> str:
    return f"{REPO}#{n}"


def base_payload() -> dict:
    with open(FIXTURE_HTML, encoding="utf-8") as fh:
        p = extract_payload(fh.read())
    p["corrections"] = [{"representative": {"sourceType": "github", "issueRef": ref(5)}, "approvedScope": 2,
                         "approvedComplexity": 1, "issueSpecific": False, "rationale": "チームの基準どおり"}]
    issue(p, 5)["calibration"].update(status="approved", approvedScope=2, approvedComplexity=1)
    return p


def valid_original_path() -> str:
    """A fictional original report: the shared fixture HTML with base_payload() embedded (written once)."""
    if not _VALID_ORIGINAL:
        with open(FIXTURE_HTML, encoding="utf-8") as fh:
            text = fh.read()
        m = PAYLOAD_RX.search(text)
        raw = safe_json(base_payload())
        path = os.path.join(tempfile.mkdtemp(prefix="swp-ja-original-"), "example-estimate-swp-original.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text[:m.start(2)] + raw + text[m.end(2):])
        _VALID_ORIGINAL.append(path)
    return _VALID_ORIGINAL[0]


def issue(payload: dict, n) -> dict:
    return next(i for i in payload["issues"] if i["issueRef"] == ref(n))


def fixture_translations(payload: dict) -> dict:
    """Translations for the Vietnamese texts of the fixture that are still in `payload`."""
    out = {}
    for (kind, ident, field), ja in FIXTURE_JA.items():
        if kind == "issue":
            found = [i for i in payload["issues"] if i["issueRef"].endswith(ident)]
            text = found[0].get(field) if found else None
        else:
            caveats = payload.get("caveats") or []
            text = caveats[int(ident)] if len(caveats) > int(ident) else None
        if text and text not in out and text in base_strings():
            out[text] = ja
    return out


def base_strings() -> set:
    p = base_payload()
    return {i.get("rationale") for i in p["issues"]} | set(p.get("caveats") or [])


def rich_payload() -> dict:
    p = base_payload()
    run = p["run"]
    run["processingLevel"] = "max"
    run["assessors"] = {"primary": {"aiModel": "sonnet", "mode": "worker"}, "witness": {"aiModel": "opus"}}
    run["assessorAgreement"] = {"status": "complete", "dualAssessed": 5, "identical": 2, "minor": 1, "major": 1,
                                "stratumSplit": 1, "subsetRule": "all", "reason": None}
    run["selection"] = {"includeClosed": False, "reestimateExisting": True, "statusRule": "issue-state",
                        "existingEstimateCheck": "checked",
                        "filters": {"sprints": [], "milestones": [], "labels": ["種別:タスク"]},
                        "excluded": {"byStatus": 2}}
    for short, (swp, agreement, why) in WITNESS.items():
        i = issue(p, short[1:])
        i["assessorCheck"] = {"agreement": agreement, "scopeBandGap": 0, "complexityBandGap": 0,
                              "witness": {"swp": swp, "rationale": why}}
    seven = issue(p, 7)
    seven.update(splitRecommended=True, splitReason=SPLIT_REASON, gaps=[GAP], workType="bugfix")
    issue(p, 8)["state"] = "closed"
    for n, team in ((4, "team:backend"), (5, "team:backend"), (6, "team:frontend")):
        issue(p, n)["labels"] = issue(p, n)["labels"] + [team]
    issue(p, 4)["existingEstimate"] = {"standardWorkPoint": 3, "estimatedHours": 6, "source": "kpi"}
    issue(p, 6)["existingEstimate"] = {"standardWorkPoint": None, "estimatedHours": 4, "source": "board"}
    p["parents"].append({"issueRef": ref(9), "aggregationStatus": "needs-breakdown", "childRefs": [],
                         "finalSWP": None, "initialSWP": None, "issueType": "epic", "labels": [],
                         "title": "決済（未分解）", "url": f"https://github.com/{REPO}/issues/9",
                         "state": "open", "sourceType": "github", "parentRef": None})
    p["corrections"] = [{"representative": {"sourceType": "github", "issueRef": ref(5)}, "approvedScope": 2,
                         "approvedComplexity": 1, "issueSpecific": False, "rationale": "チームの基準どおり"}]
    issue(p, 5)["calibration"].update(status="approved", approvedScope=2, approvedComplexity=1)
    p["calibrationRules"] = [{"ruleId": "r1", "scopeBandDelta": 1, "complexityBandDelta": 0,
                              "representativeRefs": [ref(5)],
                              "stratum": {"primaryDiscipline": "API", "workType": "feature",
                                          "scopeSignature": [], "complexitySignature": []}}]
    return p


def translations_for(payload: dict) -> dict:
    tr = fixture_translations(payload)
    tr.update({k: v for k, v in {**WITNESS_JA, **EXTRA_JA}.items() if k in _strings(payload)})
    return tr


def _strings(payload) -> set:
    from ja_report_text import payload_strings
    return payload_strings(payload)


def render_doc(payload: dict, translations=None):
    """(html, policy) rendered in process."""
    policy = TextPolicy(translations if translations is not None else translations_for(payload))
    return render(copy.deepcopy(payload), load_labels(), policy, "original.html", SOURCE_SHA), policy


def check_doc(doc: str, payload: dict, translations=None):
    """(checks as {name: (ok, detail)}, number rows)."""
    tr = translations if translations is not None else translations_for(payload)
    checks, rows = run_checks(doc, ORIGINAL_BYTES, payload, load_labels(), tr, REPO)
    return {name: (ok, detail) for name, ok, detail in checks}, rows


def failed(checks: dict, rich: bool = False) -> list:
    out = [f"{name} {detail}" for name, (ok, detail) in checks.items() if not ok]
    if rich:  # the rich fixture is not a valid source payload (module docstring): that item must be failing
        assert any(x.startswith(SOURCE_SCHEMA_CHECK + " non-terminal-split") for x in out), out
        out = [x for x in out if not x.startswith(SOURCE_SCHEMA_CHECK)]
    return out


def md_for(payload: dict, doc: str, translations=None) -> str:
    tr = translations if translations is not None else translations_for(payload)
    checks, rows = run_checks(doc, ORIGINAL_BYTES, payload, load_labels(), tr, REPO)
    meta = {"original": "original.html", "original_sha": SOURCE_SHA, "ja": "x-ja.html", "ja_sha": "0" * 64,
            "source_skill": "tkm:estimate-swp 9.9.9", "version": "test", "command": "python3 x",
            "checked_at": "2030-01-01T00:00:00+09:00"}
    return verification_md(checks, rows, payload, meta, load_labels())
