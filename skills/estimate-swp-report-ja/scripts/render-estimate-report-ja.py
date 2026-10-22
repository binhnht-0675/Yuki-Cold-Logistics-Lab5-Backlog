#!/usr/bin/env python3
"""estimate-swp-report-ja: Japanese HTML from the payload embedded in a tkm:estimate-swp report.

Commands:
  render --html ORIGINAL --out JA.html [--translations ja-texts.json] [--repo owner/name] [--force]
  check  --html ORIGINAL --ja JA.html [--verification-md OUT.md] [--source-skill "tkm:estimate-swp X.Y"]
         [--translations ja-texts.json] [--repo owner/name]   (the same files given to render, if any)
The original HTML is only read, never changed. The JA HTML and the 照合表 pass the content guard
(../_shared/content_guard.py) before they are written. Exit: 0 ok, 1 check failed / error, 2 usage /
bad translations, 3 render stopped by the content guard (nothing written).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared"))
sys.path.insert(0, HERE)

from estimate_swp_payload import extract_payload  # noqa: E402
from ja_report_check import run_checks, verification_md  # noqa: E402
from ja_report_html import render  # noqa: E402
from ja_report_layout_check import translation_errors  # noqa: E402
from ja_report_payload import embedded_copy  # noqa: E402
from ja_report_public_guard import allowed_repo, command_line, findings, html_entries  # noqa: E402
from ja_report_text import TextPolicy, check_payload_shape, load_labels, skill_version, vi_count  # noqa: E402


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["render", "check"])
    p.add_argument("--html", required=True, help="estimate-swp が出力した原本 HTML")
    p.add_argument("--out", help="render の出力（日本語版 HTML）")
    p.add_argument("--ja", help="check の対象（日本語版 HTML）")
    p.add_argument("--translations", help='自由記述の訳: {"原文": "日本語訳"}（render と check で同じファイル）')
    p.add_argument("--verification-md", help="照合表（Markdown）の出力先")
    p.add_argument("--source-skill", help="原本を作ったスキルと版（例: tkm:estimate-swp 2.1.0-beta.1）")
    p.add_argument("--repo", help="GitHub の URL を許すリポジトリ（owner/name。省略時は issueRef のリポジトリが 1 つならそれ）")
    p.add_argument("--force", action="store_true", help="既存の出力を上書きする")
    return p.parse_args(argv)


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def read_payload(path):
    raw = read_bytes(path)
    payload = extract_payload(raw.decode("utf-8"))
    check_payload_shape(payload)
    return raw, payload


def read_translations(path):
    """None when the file holds Vietnamese letters (NFC or NFD) in a translated text."""
    if not path:
        return {}
    with open(path, encoding="utf-8") as fh:
        translations = json.load(fh)
    bad = [k for k, v in translations.items() if vi_count(v)]
    if bad:
        print(f"ERROR 訳文にベトナム語の文字があります: {len(bad)} 件")
        return None
    return translations


def cmd_render(ns):
    if not ns.out:
        print("ERROR --out が必要です")
        return 2
    if os.path.abspath(ns.out) == os.path.abspath(ns.html):
        print("ERROR 原本 HTML は上書きしません（--out を別のパスに）")
        return 2
    if os.path.exists(ns.out) and not ns.force:
        print(f"ERROR 出力先が既にあります: {ns.out}（上書きするなら --force）")
        return 2
    raw, payload = read_payload(ns.html)
    translations = read_translations(ns.translations)
    if translations is None:
        return 2
    wrong = translation_errors(translations, payload)
    if wrong:
        print("\n".join("ERROR " + w for w in wrong[:20]))
        return 2
    policy = TextPolicy(translations)
    doc = render(payload, load_labels(), policy, os.path.basename(ns.html), hashlib.sha256(raw).hexdigest())
    blocked = findings(html_entries(doc), allowed_repo(payload, ns.repo))
    if blocked:
        print("\n".join(blocked))
        print("日本語版 HTML を書き出しません（公開できない内容。該当の記述は --translations で置き換える）。")
        return 3
    os.makedirs(os.path.dirname(os.path.abspath(ns.out)), exist_ok=True)
    with open(ns.out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    _, in_payload = embedded_copy(payload, translations)
    print(f"日本語版: {ns.out}（issue {len(payload.get('issues', []))} 件、訳のない記述の省略 {policy.omitted} 件、"
          f"訳文に置換 {policy.translated} 件。埋め込みデータ: 省略 {in_payload.omitted} 件、置換 {in_payload.translated} 件）")
    return 0


def cmd_check(ns, argv):
    if not ns.ja:
        print("ERROR --ja が必要です")
        return 2
    original, payload = read_payload(ns.html)
    ja_raw = read_bytes(ns.ja)
    translations = read_translations(ns.translations)
    if translations is None:
        return 2
    labels = load_labels()
    checks, rows = run_checks(ja_raw.decode("utf-8"), original, payload, labels, translations, ns.repo)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name} {detail}")
    ok_all = all(c[1] for c in checks)
    if ns.verification_md:
        meta = {"original": os.path.basename(ns.html), "original_sha": hashlib.sha256(original).hexdigest(),
                "ja": os.path.basename(ns.ja), "ja_sha": hashlib.sha256(ja_raw).hexdigest(),
                "source_skill": ns.source_skill, "version": skill_version(), "command": command_line(argv),
                "checked_at": _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")}
        md = verification_md(checks, rows, payload, meta, labels)
        blocked = findings([("照合表", "本文", md)], allowed_repo(payload, ns.repo))
        if blocked:  # covers Vietnamese letters too (category 1)
            print("\n".join(blocked))
            print("FAIL 照合表に公開できない内容があるため書き出しません")
            ok_all = False
        else:
            os.makedirs(os.path.dirname(os.path.abspath(ns.verification_md)), exist_ok=True)
            with open(ns.verification_md, "w", encoding="utf-8") as fh:
                fh.write(md)
            print(f"照合表: {ns.verification_md}")
    print("RESULT " + ("PASS" if ok_all else "FAIL"))
    return 0 if ok_all else 1


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    ns = parse_args(argv)
    try:
        return cmd_render(ns) if ns.command == "render" else cmd_check(ns, argv)
    except (OSError, ValueError) as e:
        print(f"ERROR {e}")
        return 1
    except (KeyError, TypeError, AttributeError) as e:
        print(f"ERROR 埋め込みデータの形式が想定と違います（{type(e).__name__}: {e}）")
        return 1


if __name__ == "__main__":
    sys.exit(main())
