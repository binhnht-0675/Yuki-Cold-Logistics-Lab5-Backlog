"""Checks that must pass before `apply --apply` writes anything.

- review_record: the estimate-swp run must be reviewed (calibrationStatus) and the reviewer named.
- preflight_value_errors: every field value must exist in field-map (option / iteration / number).
- blocking_errors: errors recorded at build time + re-checks that survive hand edits
  (parent = sum of children, review record). The estimate gate follows the CONTENT, not source.kind:
  a change-set that looks estimate-made (source sha256 / hourRule / review, rows with derived / children)
  needs kind estimate-swp + the review record + the HTML sha256; any other change-set that writes the
  SWP / hours fields must be `manual` (parent = sum of children is then checked on the Project before
  apply, change_set_project_checks.py) or a revert built in-process by revert-from-log.
  Kept on purpose: an estimate change-set with EVERY mark stripped and kind `manual` passes without the
  review record; write-fields.py prints a WARN for it and the #run log row records kind=manual.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from estimate_swp_payload import REVIEWED_CALIBRATION
from project_fields import encode_value

DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def review_record(payload: dict, reviewed_by: Optional[str], reviewed_at: Optional[str]) -> Tuple[dict, List[str]]:
    """The payload has calibrationStatus but no reviewer name, so the name and date come from the CLI."""
    status = (payload.get("run") or {}).get("calibrationStatus")
    review = {"calibrationStatus": status, "reviewedBy": reviewed_by or None, "reviewedAt": reviewed_at or None}
    return review, review_errors(review) + split_errors(payload)


def review_errors(review: Optional[dict]) -> List[str]:
    review = review or {}
    errors = []
    if review.get("calibrationStatus") not in REVIEWED_CALIBRATION:
        errors.append(f"calibrationStatus が {review.get('calibrationStatus')!r}（{' / '.join(REVIEWED_CALIBRATION)}"
                      " のレポートだけ書き込めます。代表 issue のレビューを先に終える）")
    if not review.get("reviewedBy") or not DATE_RX.match(str(review.get("reviewedAt") or "")):
        errors.append("代表 issue をレビューした人と日付の記録がない（build で --reviewed-by <名前> "
                      "--reviewed-at YYYY-MM-DD を指定）")
    return errors


def split_errors(payload: dict) -> List[str]:
    refs = [i.get("issueRef") for i in payload.get("issues", []) if i.get("splitRecommended")]
    return [f"分割推奨（splitRecommended）の issue が {len(refs)} 件: {refs[:5]}（分割してから見積もり直す）"] if refs else []


def preflight_value_errors(cs: dict, fmap: Optional[dict]) -> List[str]:
    """Same encoding as the write itself, run offline before the first write."""
    errors = []
    if not fmap:
        return errors
    for c in cs.get("changes", []):
        for field, value in (c.get("fields") or {}).items():
            if field not in fmap["fields"]:
                continue  # reported by validate_change_set
            try:
                encode_value(fmap, field, value)
            except (KeyError, ValueError) as e:
                errors.append(f"{c.get('key')}: {e}")
    return errors


def parent_sum_errors(cs: dict) -> List[str]:
    """Every change with `children` must hold the sum of its children's numbers, field by field."""
    by_key = {c.get("key"): c for c in cs.get("changes", [])}
    errors = []
    for c in cs.get("changes", []):
        kids = c.get("children")
        if not kids:
            continue
        for field, value in (c.get("fields") or {}).items():
            if not isinstance(value, (int, float)):
                continue
            parts = [(by_key.get(k) or {}).get("fields", {}).get(field) for k in kids]
            if any(not isinstance(p, (int, float)) for p in parts):
                errors.append(f"{c['key']}: 子の {field} がそろっていない（子の合計を確認できない）")
            elif abs(sum(parts) - value) > 1e-9:
                errors.append(f"{c['key']}: {field} {value} が子の合計 {sum(parts)} と一致しません")
    return errors


ESTIMATE_SOURCE_KEYS = ("sha256", "hourRule", "review")


def writes_estimate(cs: dict, estimate_fields) -> bool:
    return any(f in estimate_fields for c in cs.get("changes", []) for f in (c.get("fields") or {}))


def looks_estimate(cs: dict) -> bool:
    src = cs.get("source") or {}
    return (src.get("kind") == "estimate-swp" or any(src.get(k) for k in ESTIMATE_SOURCE_KEYS)
            or any(c.get("derived") or c.get("children") for c in cs.get("changes", [])))


def kind_errors(cs: dict, estimate_fields, in_process_revert: bool) -> List[str]:
    """Which rules apply is decided from the content; editing source.kind cannot skip the review."""
    src = cs.get("source") or {}
    kind = src.get("kind")
    if looks_estimate(cs):
        errors = review_errors(src.get("review"))
        if kind != "estimate-swp":
            errors.append(f"見積もり由来の内容（sha256・hourRule・review・derived・children）なのに source.kind が {kind!r}"
                          "（build-from-estimate-swp で作り直す）")
        if not src.get("sha256"):
            errors.append("見積もりの元 HTML の sha256 がない（build-from-estimate-swp で作り直す）")
        return errors
    if not writes_estimate(cs, estimate_fields) or kind == "manual" or (kind == "revert" and in_process_revert):
        return []
    hint = "。revert は revert-from-log でログから作り直す" if kind == "revert" else ""
    return [f"SWP / 見積時間を書く change-set は estimate-swp（レビュー済み）か manual だけ（source.kind = {kind!r}）{hint}"]


def blocking_errors(cs: dict, estimate_fields=("SWP", "見積時間(h)"), in_process_revert: bool = False) -> List[str]:
    errors = list(cs.get("blockingErrors") or [])
    errors += [e for e in kind_errors(cs, estimate_fields, in_process_revert) if e not in errors]
    errors += [e for e in parent_sum_errors(cs) if e not in errors]
    return errors
