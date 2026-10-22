"""Every (label group, value) the JA report shows through the label map, for the 列挙値の日本語化 check.

An enum value missing from the label map would be shown as the raw (English) value, so check fails on it.
Groups follow the renderers: ja_report_html*.py, ja_report_issue_rows.py, ja_report_summary_blocks.py,
ja_report_assessor_blocks.py, ja_report_calibration_blocks.py, ja_report_decision_blocks.py.
"""
from __future__ import annotations

from typing import Iterator, Tuple

from ja_report_metrics import metrics

ISSUE_GROUPS = [("discipline", "primaryDiscipline"), ("workType", "workType"), ("confidence", "confidence"),
                ("evidenceStatus", "evidenceStatus"), ("activityType", "activityType")]


def _issue_values(i: dict) -> Iterator[Tuple[str, object]]:
    yield from ((g, i.get(f)) for g, f in ISSUE_GROUPS)
    yield "issueCalibration", (i.get("calibration") or {}).get("status")
    prov = i.get("provenance") or {}
    yield "retrievedVia", prov.get("retrievedVia")
    yield "detailStatus", prov.get("detailStatus")
    yield from (("provenanceField", f) for f in prov.get("fields") or [])
    if i.get("assessorCheck"):
        yield "agreement", i["assessorCheck"].get("agreement")


def enum_values(payload: dict) -> Iterator[Tuple[str, object]]:
    run = payload.get("run") or {}
    yield "processingLevel", run.get("processingLevel", "medium")
    yield "runCalibration", run.get("calibrationStatus")
    agreement = run.get("assessorAgreement") or {}
    if agreement.get("status") == "unavailable":
        yield "unavailableReason", agreement.get("reason")
    sel = run.get("selection")
    if sel:
        yield "statusRule", sel.get("statusRule")
        yield "estimateCheck", sel.get("existingEstimateCheck")
        yield from (("excludedGate", g) for g in sel.get("excluded") or {})
    for i in payload.get("issues", []):
        yield from _issue_values(i)
    for i in metrics(payload)["diff"]:
        yield "estimateSource", i["existingEstimate"].get("source")
    for p in payload.get("parents", []):
        yield "issueType", p.get("issueType")
        yield "aggregationStatus", p.get("aggregationStatus")
    for r in payload.get("representatives") or []:
        yield from (("selectionReason", s) for s in r.get("selectionReasons") or [])
    for r in payload.get("calibrationRules") or []:
        stratum = r.get("stratum") or {}
        yield "discipline", stratum.get("primaryDiscipline")
        yield "workType", stratum.get("workType")
