"""Expected values, required keys and 照合表 row names for the numbers of the full report blocks.

expected_block() recomputes a data-v key from the payload (via ja_report_metrics, i.e. the source
skill's formulas) and returns NOT_MINE for keys of the original blocks (ja_report_numbers.expected).
A row in a block it does not belong to (e.g. an issue in the split table that has no split
recommendation) raises KeyError, so the checker reports an unknown key.
"""
from __future__ import annotations

from typing import Optional, Set

from ja_report_assessor_blocks import expected_agreement
from ja_report_metrics import NO_TEAM, approved_swp, metrics
from ja_report_text import label, short_ref

NOT_MINE = object()
SUM_KEYS = {("range", "min"), ("range", "max"), ("range", "uncertain"), ("state", "open"), ("state", "closed"),
            ("low", "swp"), ("split", "swp"), ("count", "changed"), ("count", "reps"), ("hours", "rate"),
            ("hours", "samples"), ("diff", "count")}
CAT_JA = {"build": "構築", "test": "テスト・品質確認", "planned": "計画の合計", "bug": "不具合・手戻り", "all": "全 issue の合計"}
TEAM_JA = {"count": "issue 数", "build": "構築", "bug": "不具合・手戻り", "total": "合計"}
AGR_JA = {"identical": "一致", "minor": "軽微な差", "major": "大きな差", "stratumSplit": "区分違い",
          "dual": "二回評価した issue", "unseen": "人が見ていない分かれた issue"}
DIFF_JA = {"old": "既存の SWP", "hours": "既存の時間", "new": "新しい SWP", "delta": "差"}
ISSUE_JA = {"wa": "評価 A の SWP（差の表示）", "wb": "評価 B の SWP（差の表示）", "wdetail": "評価 B の SWP（詳細）",
            "dfinal": "詳細の SWP", "dinitial": "詳細の初期 SWP"}
SUM_JA = {"range": {"min": "不確かさの幅 最小", "max": "不確かさの幅 最大", "uncertain": "幅を付けた issue 数"},
          "state": {"open": "オープン", "closed": "クローズ"}, "low": {"swp": "確信度「低」 SWP"},
          "split": {"swp": "分割提案 SWP"}, "count": {"changed": "点数が変わった issue 数", "reps": "代表 issue 数"},
          "hours": {"rate": "時間の換算率（既定）", "samples": "換算率の根拠の issue 数"}, "diff": {"count": "既存の見積もりとの比較 件数"}}


def _issue(payload: dict, ref: str) -> dict:
    return next(i for i in payload.get("issues", []) if i["issueRef"] == ref)


def _issue_field(payload: dict, ref: str, field: str):
    i = _issue(payload, ref)
    if field in ("wa", "wb", "wdetail"):
        check = i["assessorCheck"]
        return i["initialSWP"] if field == "wa" else check["witness"]["swp"]
    return i["finalSWP"] if field == "dfinal" else i["initialSWP"]


def expected_block(payload: dict, kind: str, ident: str, field: str):
    m = metrics(payload)
    if kind == "sum" and (ident, field) in SUM_KEYS:
        return {"range": lambda: m["range"][field], "state": lambda: m["state"][field], "low": lambda: m["low_swp"],
                "split": lambda: m["split_swp"], "diff": lambda: len(m["diff"]),
                "count": lambda: m["changed"] if field == "changed" else len(payload.get("representatives") or []),
                "hours": lambda: m["rate"] if field == "rate" else m["samples"]}[ident]()
    if kind == "dist":
        count = m["dist"][int(ident)]  # KeyError for a value no issue has
        return int(ident) if field == "value" else count
    if kind == "cat":
        return m["pct"][ident] if field == "pct" else m["cat"][ident][0 if field == "count" else 1]
    if kind in ("rsplit", "rlow"):
        i = _issue(payload, ident)
        member = i.get("splitRecommended") if kind == "rsplit" else i.get("confidence") == "low"
        if not member:
            raise KeyError(ident)
        return i["finalSWP"]
    if kind == "team":
        n, build, bug = m["teams"][ident]
        return {"count": n, "build": build, "bug": bug, "total": build + bug}[field]
    if kind == "agr":
        return expected_agreement(payload, ident)
    if kind == "sel":
        return ((payload.get("run") or {}).get("selection") or {}).get("excluded", {})[ident]
    if kind == "diff":
        i = next(r for r in m["diff"] if r["issueRef"] == ident)
        old = i["existingEstimate"]
        return {"old": old.get("standardWorkPoint"), "hours": old.get("estimatedHours"), "new": i["finalSWP"],
                "delta": i["finalSWP"] - (old.get("standardWorkPoint") or 0)}[field]
    if kind == "group" and field == "swp":
        return m["groups"][ident][1]
    if kind == "parent" and field == "initial":
        return next(p for p in payload.get("parents", []) if p["issueRef"] == ident).get("initialSWP")
    if kind == "rep" and field == "chip":
        return _issue(payload, ident)["finalSWP"]
    if kind == "issue" and field in ISSUE_JA:
        return _issue_field(payload, ident, field)
    if kind == "corr":
        c = (payload.get("corrections") or [])[int(ident)]
        if field == "approved":
            return approved_swp(c.get("approvedScope"), c.get("approvedComplexity"))
        return _issue(payload, (c.get("representative") or {}).get("issueRef")).get("initialSWP")
    if kind == "rule":
        r = (payload.get("calibrationRules") or [])[int(ident)]
        return r["scopeBandDelta"] if field == "scope" else r["complexityBandDelta"]
    return NOT_MINE


def block_required_keys(payload: dict) -> Set[str]:
    """Number cells every report must show (the checker also adds the data-v keys of a fresh render)."""
    m, issues = metrics(payload), payload.get("issues", [])
    need = {f"sum|{a}|{b}" for a, b in SUM_KEYS if (a, b) not in (("hours", "samples"), ("diff", "count"))}
    need |= {"sum|hours|samples"} if m["samples"] else set()
    need |= {"sum|diff|count"} | {f"diff|{i['issueRef']}|new" for i in m["diff"]} if m["diff"] else set()
    need |= {f"dist|{swp}|{f}" for swp in m["dist"] for f in ("value", "count")}
    need |= {f"cat|{k}|{f}" for k in CAT_JA for f in ("count", "swp")}
    need |= {"cat|bug|pct", "cat|planned|pct"} if m["cat"]["all"][1] else set()
    need |= {f"rsplit|{i['issueRef']}|swp" for i in issues if i.get("splitRecommended")}
    need |= {f"rlow|{i['issueRef']}|swp" for i in issues if i.get("confidence") == "low"}
    need |= {f"team|{name}|{f}" for name in m["teams"] for f in TEAM_JA}
    agreement = (payload.get("run") or {}).get("assessorAgreement") or {}
    if agreement.get("status") == "complete":
        need |= {f"agr|{k}|count" for k in AGR_JA if k != "unseen"} | ({"agr|unseen|count"} if m["unseen"] else set())
    need |= {f"sel|{g}|count" for g in (((payload.get("run") or {}).get("selection") or {}).get("excluded") or {})}
    need |= {f"group|{ref}|swp" for ref, (rows, _s) in m["groups"].items() if rows}
    need |= {f"parent|{p['issueRef']}|initial" for p in payload.get("parents", [])}
    need |= {f"rep|{r['issueRef']}|chip" for r in payload.get("representatives") or []}
    need |= {f"issue|{i['issueRef']}|dfinal" for i in issues}
    need |= {f"issue|{i['issueRef']}|wdetail" for i in issues if i.get("assessorCheck")}
    need |= {f"corr|{n}|{f}" for n in range(len(payload.get("corrections") or [])) for f in ("initial", "approved")}
    need |= {f"rule|{n}|{f}" for n in range(len(payload.get("calibrationRules") or [])) for f in ("scope", "complexity")}
    return need


def block_row_name(kind: str, ident: str, field: str, labels: dict) -> Optional[str]:
    """照合表 row name for a block key, or None for keys of the original blocks."""
    if kind == "sum":
        name = SUM_JA.get(ident, {}).get(field)
        return f"要約 {name}" if name else None
    names = {"dist": lambda: f"SWP の分布 SWP {ident} {'値' if field == 'value' else '件数'}",
             "cat": lambda: f"区分 {CAT_JA.get(ident, ident)} {({'count': '件数', 'swp': 'SWP'}).get(field, '割合（%）')}",
             "rsplit": lambda: f"リスク 分割の提案 {short_ref(ident)} SWP",
             "rlow": lambda: f"リスク 確信度「低」 {short_ref(ident)} SWP",
             "team": lambda: f"チーム別 {'（チーム未設定）' if ident == NO_TEAM else ident} {TEAM_JA.get(field, field)}",
             "agr": lambda: f"評価 A・B {AGR_JA.get(ident, ident)} 件数",
             "sel": lambda: f"除外 {label(labels, 'excludedGate', ident)} 件数",
             "diff": lambda: f"既存の見積もり {short_ref(ident)} {DIFF_JA.get(field, field)}",
             "corr": lambda: f"校正の修正 {int(ident) + 1} 件目 {'確定 SWP' if field == 'approved' else '初期 SWP'}",
             "rule": lambda: f"適用ルール {int(ident) + 1} 件目 {'範囲の段' if field == 'scope' else '複雑さの段'}"}
    if kind in names:
        return names[kind]()
    if kind == "group" and field == "swp":
        return f"親ごとの小計 {short_ref(ident) if ident != '-' else '親なし'} SWP"
    if kind == "rep" and field == "chip":
        return f"代表 {short_ref(ident)} SWP"
    if kind == "issue" and field in ISSUE_JA:
        return f"issue {short_ref(ident)} {ISSUE_JA[field]}"
    return None
