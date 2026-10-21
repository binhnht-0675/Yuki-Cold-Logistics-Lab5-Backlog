"""`build-from-estimate-swp` / `build-from-sprint-plan`: make a change-set file (no GitHub access)."""
from __future__ import annotations

import json
import os

from change_set_builders import build_from_estimate, build_from_sprint_plan
from change_set_checks import review_record
from estimate_swp_payload import read_report
from key_map import load_key_map


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_change_set(path, cs):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cs, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"change-set: {len(cs['changes'])} 件 → {path}")


def cmd_build(ns, kmap_path):
    if ns.command == "build-from-estimate-swp":
        if not (ns.html and ns.backlog):
            print("ERROR --html と --backlog が必要です")
            return 2
        payload, digest = read_report(ns.html)
        backlog = load_json(ns.backlog)
        backlog = backlog["items"] if isinstance(backlog, dict) else backlog
        rule = load_json(ns.hour_rule) if ns.hour_rule else None
        cs, warns = build_from_estimate(payload, load_key_map(kmap_path), backlog, rule, ns.repo,
                                        ns.swp_field, ns.hours_field)
        review, review_errs = review_record(payload, ns.reviewed_by, ns.reviewed_at)
        cs["source"].update({"file": os.path.basename(ns.html), "sha256": digest, "review": review,
                             "generatedAt": (payload.get("run") or {}).get("generatedAt")})
        cs["blockingErrors"] = review_errs + cs["blockingErrors"]
    else:
        if not ns.plan:
            print("ERROR --plan が必要です")
            return 2
        cs, warns = build_from_sprint_plan(load_json(ns.plan), ns.status_field, ns.iteration_field)
        cs["source"]["file"] = os.path.basename(ns.plan)
    for w in warns:
        print("WARN " + w)
    for e in cs.get("blockingErrors") or []:
        print("WARN [apply 停止] " + e)
    if cs.get("blockingErrors"):
        print(f"WARN 上の {len(cs['blockingErrors'])} 件を change-set に記録しました。解消するまで apply は書き込みません。")
    save_change_set(ns.change_set, cs)
    return 0
