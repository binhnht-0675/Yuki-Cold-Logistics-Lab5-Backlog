"""Checks for the JA report (lang, no Vietnamese, numbers = payload, no bare numbers, sums, provenance,
offline, no Scope x Complexity in the visible part, the embedded payload) + 照合表."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Dict, List, Optional, Tuple

from estimate_swp_payload import REVIEWED_CALIBRATION
from ja_report_axis_guard import visible_axis_errors
from ja_report_block_numbers import block_row_name
from ja_report_enum_values import enum_values
from ja_report_html import render
from ja_report_interaction import SCRIPT
from ja_report_layout_check import layout_errors, translation_errors, value_keys
from ja_report_numbers import (approval_errors, compare_numbers, parent_sum_errors, required_keys, scan_markers)
from ja_report_payload_check import payload_checks
from ja_report_public_guard import allowed_repo, findings, html_entries
from ja_report_text import TextPolicy, approval, canonical_sha256, fmt, short_ref, vi_count

EMBED_RX = re.compile(r'<script id="report-data-ja" type="application/json">(.*?)</script>', re.S)
SCRIPT_RX = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
UNTRANSLATED = "訳のない自由記述 0（日本語でない記述は訳文で置き換え）"
AXIS = "表示部に Scope × Complexity の表記・軸の値がない（埋め込みデータと折りたたみの「技術的な詳細」を除く）"
OFFLINE = "外部読み込み・スクリプトなし（固定の表示用スクリプトだけ）"


def offline_ok(ja_html: str) -> bool:
    """Only JSON data blocks and the one fixed display script; no handler, external load or foreign link."""
    scripts = SCRIPT_RX.findall(ja_html)
    plain = [body for attrs, body in scripts if 'type="application/json"' not in attrs]
    if any(attrs.strip() and 'type="application/json"' not in attrs for attrs, _ in scripts) or plain not in ([], [SCRIPT]):
        return False
    rest = SCRIPT_RX.sub(" ", ja_html)
    return (not re.search(r"\son\w+\s*=", rest, re.I) and not re.search(r"<(link|img|iframe|object|embed)\b|\ssrc\s*=", rest, re.I)
            and all(h.startswith("https://github.com/") for h in re.findall(r'href="([^"]*)"', rest)))
def _detail(items: List[str], label: str) -> str:
    return f"{label} {len(items)}" + (": " + " / ".join(items[:3]) if items else "")


def run_checks(ja_html: str, original_bytes: bytes, payload: dict, labels: dict,
               translations: Optional[Dict[str, str]] = None, repo: Optional[str] = None
               ) -> Tuple[List[tuple], List[tuple]]:
    """Return (checks, number_rows). checks: (name, ok, detail); number_rows: (key, expected, shown, ok)."""
    translations = translations or {}
    m = EMBED_RX.search(ja_html)
    emb = json.loads(m.group(1)) if m else {}
    src_sha = hashlib.sha256(original_bytes).hexdigest()
    policy = TextPolicy(translations)  # a fresh render: the reference for counts, cells and their order
    fresh = render(payload, labels, policy, emb.get("sourceFile") or "", src_sha)
    checks = [("lang=\"ja\"", bool(re.search(r'<html[^>]*\blang="ja"', ja_html)), "")]
    n_vi = vi_count(ja_html)
    checks.append(("ベトナム語の文字（NFC / NFD とも）", n_vi == 0, f"{n_vi} 文字"))
    rows = compare_numbers(ja_html, payload, {"omitted": policy.omitted, "translated": policy.translated})
    bad = [r for r in rows if not r[3]]
    checks.append(("数値 = 埋め込みデータ（data-v の印の付いた数値）", bool(rows) and not bad,
                   f"照合 {len(rows)} 箇所、不一致 {len(bad)}"))
    missing = sorted((required_keys(payload) | value_keys(fresh)) - {r[0] for r in rows})
    checks.append(("網羅（全表の数値の欄: issue・確定・親・合計・分割の提案・作業種別・代表・件数）", not missing,
                   f"不足 {len(missing)}" + (f": {missing[:3]}" if missing else "")))
    layout = layout_errors(ja_html, fresh)
    checks.append(("印の並び = 埋め込みデータから描き直した版（数値の欄を自由記述で置き換えていない）", not layout,
                   _detail(layout, "違い")))
    wrong = translation_errors(translations, payload)
    checks.append(("訳文（原文が埋め込みデータにある・数値が原文と同じ）", not wrong,
                   _detail(wrong, "不一致") if translations else "訳なし"))
    embedded_checks, payload_omitted = payload_checks(ja_html, payload, translations)
    missing_tr = policy.omitted + payload_omitted
    checks.append((UNTRANSLATED, missing_tr == 0, f"{policy.omitted} 件・埋め込みデータ {payload_omitted} 件"
                   + ("（訳文を --translations で渡す）" if missing_tr else "")))
    axis = visible_axis_errors(ja_html)
    checks.append((AXIS, not axis, _detail(axis, "該当")))
    blocked = [s.replace("|", "／") for s in findings(html_entries(ja_html), allowed_repo(payload, repo))
               if s.startswith("BLOCKED")]
    checks.append(("内容検査（公開リポジトリに出せない内容がない）", not blocked, _detail(blocked, "該当")))
    unknown, bare = scan_markers(ja_html, payload, translations,
                                 {"file": emb.get("sourceFile"), "sha": src_sha[:16]})
    checks.append(("印のない数値 0（固定文・自由記述・出所欄を除く）", not bare,
                   f"{len(bare)} 個" + (": " + " / ".join(bare[:3]) if bare else "")))
    hint = "（訳文を使った版は --translations を指定）" if unknown and emb.get("translatedTexts") else ""
    checks.append(("自由記述 = 埋め込みデータ／訳文", not unknown,
                   f"不明 {len(unknown)}" + (": " + " / ".join(unknown[:3]) if unknown else "") + hint))
    sums = parent_sum_errors(payload)
    checks.append(("親 = 子の合計（集計 derived）", not sums, "、".join(sums[:5])))
    appr = approval_errors(payload)
    checks.append(("代表の担当者確定 = 最終の Scope × Complexity", not appr, "、".join(appr[:5])))
    ok_src = emb.get("sourceSha256") == src_sha
    ok_pay = emb.get("sourcePayloadSha256") == canonical_sha256(payload)
    checks.append(("出所（原本 sha256・データ sha256）", ok_src and ok_pay, f"原本 {'一致' if ok_src else '不一致'} / データ {'一致' if ok_pay else '不一致'}"))
    checks.append((OFFLINE, offline_ok(ja_html), ""))
    checks += embedded_checks
    unmapped = sorted({f"{g}:{v}" for g, v in enum_values(payload) if v is not None and v not in labels.get(g, {})})
    checks.append(("列挙値の日本語化", not unmapped, ", ".join(unmapped[:5])))
    cal = (payload.get("run") or {}).get("calibrationStatus")
    checks.append(("校正済み（calibrationStatus が " + " / ".join(REVIEWED_CALIBRATION) + "）",
                   cal in REVIEWED_CALIBRATION, f"calibrationStatus = {cal}"))
    return checks, rows


FIELD_JA = {"final": "最終 SWP", "initial": "初期 SWP", "children": "子の数", "count": "件数", "swp": "SWP",
            "issues": "issue 数", "parents": "親の数", "corrections": "修正数", "rules": "ルール数", "high": "高", "medium": "中", "low": "低"}
SUM_JA = {"total": "SWP 合計", "count": "", "conf": "確信度", "split": "分割提案", "needs": "分解が必要な親"}
NOTE_JA = {"omitted": "省略した記述", "translated": "訳文に置換した記述"}


def row_name(key: str, labels: dict) -> str:
    kind, ident, field = key.split("|")
    block = block_row_name(kind, ident, field, labels)
    if block:
        return block
    if kind == "sum":
        return f"要約 {SUM_JA.get(ident, ident)} {FIELD_JA.get(field, field)}".replace("  ", " ").strip()
    if kind == "wt":
        return f"作業種別 {labels.get('workType', {}).get(ident, ident)} {FIELD_JA.get(field, field)}"
    if kind == "note":
        return f"注意事項 {NOTE_JA.get(ident, ident)} 件数"
    if kind == "group":
        return f"親ごとの件数 {short_ref(ident) if ident != '-' else '親なし'}"
    name = {"issue": "issue", "parent": "親", "rep": "代表"}.get(kind, kind)
    return f"{name} {short_ref(ident)} {FIELD_JA.get(field, field)}"


def rep_lines(payload: dict) -> List[str]:
    issues = {i["issueRef"]: i for i in payload.get("issues", [])}
    out = []
    for r in payload.get("representatives") or []:
        i, a = issues.get(r["issueRef"]) or {}, approval(payload, r["issueRef"])
        skill = f"{fmt(i.get('initialScope'))} × {fmt(i.get('initialComplexity'))} → {fmt(i.get('initialSWP'))}"
        conf = ("—" if a["scope"] is None and a["complexity"] is None else
                f"{fmt(a['scope'])} × {fmt(a['complexity'])} → {fmt(i.get('finalSWP'))}")
        reason = a["reason"] if a["reason"] and not vi_count(a["reason"]) else (
            "（ベトナム語のため日本語版 HTML を参照）" if a["reason"] else "—（埋め込みデータに理由なし）")
        out.append(f"| {short_ref(r['issueRef'])} | {skill} | {conf} | {reason.replace('|', '／')} |")
    return out


SCOPE_NOTE = ("- 数値の検査範囲: data-v の印が付いた数値は、すべて原本の埋め込みデータから再計算した値と照合する。"
              "印のない数値は、表示される本文（タグ・属性・style・script を除く）で、固定文（算定方法の難易度の目安、"
              "語「sha256」）、照合済みの自由記述（data-t: 埋め込みデータの文字列か訳文と完全一致）、出所欄（data-x: 原本のファイル名と sha256 の先頭）を除いて 0 個であることを検査する。")


def verification_md(checks, rows, payload, meta: dict, labels: dict) -> str:
    ok_all = all(c[1] for c in checks)
    out = ["# estimate-swp 照合表（日本語版 HTML と原本 HTML）", "",
           f"- 判定: **{'合格' if ok_all else '不合格'}**",
           f"- 原本 HTML: `{meta['original']}`（sha256 `{meta['original_sha']}`。公開リポジトリには置かず、sha256 で照合）",
           f"- 日本語版 HTML: `{meta['ja']}`（sha256 `{meta['ja_sha']}`）",
           f"- 埋め込みデータの sha256（正規化 JSON）: `{canonical_sha256(payload)}`",
           f"- 原本を作ったスキル: {meta.get('source_skill') or '（未指定）'}",
           f"- 変換スキル: estimate-swp-report-ja {meta['version']}",
           f"- 照合日時: {meta['checked_at']}",
           f"- 実行したコマンド: `{meta['command']}`", SCOPE_NOTE, "",
           "## 検査項目", "", "| 検査 | 結果 | 詳細 |", "|---|---|---|"]
    out += [f"| {n} | {'合格' if ok else '不合格'} | {d} |" for n, ok, d in checks]
    out += ["", "## 代表 issue（スキルの評価・担当者の確定・調整の理由）", "",
            "| issue | スキルの評価（Scope × Complexity → SWP） | 担当者の確定（Scope × Complexity → SWP） | 調整の理由 |",
            "|---|---|---|---|"] + rep_lines(payload)
    out += ["", "## 数値の照合（埋め込みデータから再計算 → 日本語版の表示）", "",
            "| 項目 | 埋め込みデータから再計算 | 日本語版 | 一致 |", "|---|---|---|---|"]
    for key, exp, shown, ok in rows:
        out.append(f"| {row_name(key, labels)} | {exp} | {shown} | {'○' if ok else '×'} |")
    return "\n".join(out) + "\n"
