"""Second assessor (processing level high / max) in Japanese, following the source render_assessor.py.

Row badge when assessorCheck.agreement is not identical (source _contested), "A · B" SWP spread when
the two SWP differ, B's SWP and translated rationale in the issue detail, the agreement summary, and
the fixed caveats. Agreement is a detector, not a verdict: B never enters any total (no total reads
assessorCheck). B's rationale is free text and goes through the TextPolicy like every other text.
"""
from __future__ import annotations

from typing import List

from ja_report_html_parts import e, t, v
from ja_report_metrics import contested, metrics
from ja_report_text import TextPolicy, label

AGREEMENT_CAVEAT = ("一致は検証済みという意味ではない: 二つの AI が同じように間違えることもある。正式な点数は常に評価 A のもので、"
                    "評価 B は差を見つけるためだけに使う。")
AGREEMENT_KEYS = (("identical", "一致"), ("minor", "軽微な差"), ("major", "大きな差"), ("stratumSplit", "区分違い"))


def _check(issue: dict):
    return issue.get("assessorCheck")


def badge_html(issue: dict) -> str:
    if not contested(issue):
        return ""
    return ' <span class="flag contested" title="二つの AI の評価が分かれた">評価が分かれた</span>'


def spread_html(issue: dict) -> str:
    check = _check(issue)
    if not check or check["witness"]["swp"] == issue.get("initialSWP"):
        return ""
    ref = issue["issueRef"]
    return (f' <span class="spread" title="評価 A · 評価 B（SWP）">A {v(f"issue|{ref}|wa", issue.get("initialSWP"))}'
            f' · B {v(f"issue|{ref}|wb", check["witness"]["swp"])}</span>')


def detail_html(issue: dict, L: dict, T: TextPolicy) -> str:
    check = _check(issue)
    if not check:
        return ""
    witness, key = check["witness"], f"issue|{issue['issueRef']}|wdetail"
    return (f'<p>評価 B（別のモデルによる独立した評価）: {v(key, witness["swp"])} SWP'
            f'（{e(label(L, "agreement", check["agreement"]))}）— 根拠: {t(T(witness.get("rationale")))}</p>')


def _agreement(payload: dict):
    return (payload.get("run") or {}).get("assessorAgreement")


def summary_html(payload: dict) -> str:
    agreement = _agreement(payload)
    if not agreement or agreement.get("status") != "complete":
        return ""
    counts = " ・ ".join(f"{name} {v(f'agr|{key}|count', agreement.get(key))}" for key, name in AGREEMENT_KEYS)
    return (f"<p>評価 A・B の一致（二回評価した issue {v('agr|dual|count', agreement.get('dualAssessed'))} 件）: "
            f"{counts}。点数と合計は評価 A だけから出している。</p>")


def caveats_html(payload: dict, L: dict) -> List[str]:
    """<li> bodies for the caveats list (empty when there is no second assessor)."""
    agreement = _agreement(payload)
    if not agreement:
        return []
    if agreement.get("status") == "unavailable":
        reason = e(label(L, "unavailableReason", agreement.get("reason")))
        return [f"評価 B を実施できなかった（{reason}）。結果は評価者ひとりの評価で、処理レベル「中」と同じ。"]
    out = [e(AGREEMENT_CAVEAT)]
    unseen = metrics(payload)["unseen"]
    if unseen:
        out.append(f"評価が分かれた issue のうち {v('agr|unseen|count', unseen)} 件は、代表 issue の確認で人が見ていない。")
    return out


def expected_agreement(payload: dict, ident: str):
    """Expected value of agr|<ident>|count (checker)."""
    if ident == "unseen":
        return metrics(payload)["unseen"]
    agreement = _agreement(payload) or {}
    return agreement.get("dualAssessed" if ident == "dual" else ident)
