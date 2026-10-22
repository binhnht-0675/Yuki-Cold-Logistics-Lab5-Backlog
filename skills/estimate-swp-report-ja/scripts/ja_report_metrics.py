"""Derived numbers of the report blocks, computed with the SOURCE skill's own functions.

The uncertainty range, the build / test / bug split, the team load and the default hours-per-SWP rate
are imported from tkm:estimate-swp (scripts/core/render_html.py, schema.py, render_assessor.py), never
re-derived here, so the Japanese report shows the same numbers as the original. Both the renderer and
the checker (expected values) read metrics(); the checker recomputes them from the embedded payload.
The source package is loaded under its own name ("estimate_swp_core") from its install path.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from collections import Counter
from typing import Dict

SOURCE_SCRIPTS = os.path.expanduser(os.path.join("~", ".claude", "skills", "estimate-swp", "scripts"))
NO_PARENT = "-"
NO_TEAM = "-"


def _load_source():
    name = "estimate_swp_core"
    if name not in sys.modules:
        init = os.path.join(SOURCE_SCRIPTS, "core", "__init__.py")
        if not os.path.exists(init):
            raise ImportError(f"tkm:estimate-swp のスクリプトが見つかりません（{init}）")
        spec = importlib.util.spec_from_file_location(name, init, submodule_search_locations=[os.path.dirname(init)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return (importlib.import_module(name + ".render_html"), importlib.import_module(name + ".schema"),
            importlib.import_module(name + ".render_assessor"))


SRC_HTML, SRC_SCHEMA, SRC_ASSESSOR = _load_source()
VALID_SWP = SRC_HTML.VALID_SWP
SCOPE_BANDS, COMPLEXITY_BANDS = SRC_SCHEMA.SCOPE_BANDS, SRC_SCHEMA.COMPLEXITY_BANDS
COMPLEXITY_MULTIPLIERS = SRC_SCHEMA.COMPLEXITY_MULTIPLIERS


def contested(issue: dict) -> bool:
    return SRC_ASSESSOR._contested(issue)


def approved_swp(scope, complexity):
    """SWP of a person's confirmed axes (source derive_swp); None when the axes are not valid bands."""
    try:
        return SRC_SCHEMA.derive_swp(scope, complexity)
    except (ValueError, TypeError):
        return None


def _diff_rows(issues):
    """Source rule (render_html, old-estimate diff): differing SWP, or an hours-only existing estimate."""
    out = []
    for item in issues:
        old = item.get("existingEstimate")
        if not old:
            continue
        swp, hours = old.get("standardWorkPoint"), old.get("estimatedHours")
        if (swp is not None and swp != item.get("finalSWP")) or (swp is None and hours is not None):
            out.append(item)
    return sorted(out, key=lambda x: x["issueRef"])


def _teams(issues) -> Dict[str, tuple]:
    """{team key: (count, build, bug)} in source order; the row without a team label gets NO_TEAM."""
    named = {lab.split(":", 1)[1] for i in issues for lab in i.get("labels") or [] if lab.startswith("team:")}
    return {(name if name in named else NO_TEAM): (n, build, bug)
            for name, n, build, bug in SRC_HTML._team_rows(issues)}


def _groups(payload) -> Dict[str, tuple]:
    """{parent ref or NO_PARENT: (members, subtotal)}; subtotal = parent finalSWP, else the sum (source)."""
    parents = {p["issueRef"]: p for p in payload.get("parents", [])}
    members: Dict[str, list] = {ref: [] for ref in parents}
    members[NO_PARENT] = []
    for i in payload.get("issues", []):
        members.setdefault(i.get("parentRef") or NO_PARENT, []).append(i)
    out = {}
    for ref, rows in members.items():
        own = (parents.get(ref) or {}).get("finalSWP")
        out[ref] = (rows, own if own is not None else sum(r.get("finalSWP") or 0 for r in rows))
    return out


_CACHE: list = [None, None]


def metrics(payload: dict) -> dict:
    """All derived numbers of one payload (cached for the same payload object)."""
    if _CACHE[0] is payload:
        return _CACHE[1]
    issues = payload.get("issues", [])
    cats = SRC_HTML._categorize(issues)
    cat = {k: (len(v), sum(i["finalSWP"] for i in v)) for k, v in cats.items()}
    cat["planned"] = (cat["build"][0] + cat["test"][0], cat["build"][1] + cat["test"][1])
    cat["all"] = (cat["planned"][0] + cat["bug"][0], cat["planned"][1] + cat["bug"][1])
    bug_pct = round(cat["bug"][1] * 100 / cat["all"][1]) if cat["all"][1] else 0
    low, high, uncertain = SRC_HTML._uncertainty_range(issues)
    rate, samples = SRC_HTML._default_hour_rate(issues)
    summary = SRC_HTML._summary({"issues": issues, "parents": payload.get("parents", []),
                                 "representatives": payload.get("representatives") or []})
    seen = {(r.get("sourceType"), r["issueRef"]) for r in payload.get("representatives") or []}
    result = {
        "range": {"min": low, "max": high, "uncertain": uncertain},
        "cat": cat, "pct": {"bug": bug_pct, "planned": 100 - bug_pct},
        "dist": dict(sorted(Counter(i["finalSWP"] for i in issues).items())),
        "state": {"open": summary["issues"] - summary["closed"], "closed": summary["closed"]},
        "changed": summary["changed"],
        "low_swp": sum(i["finalSWP"] for i in issues if i.get("confidence") == "low"),
        "split_swp": sum(i["finalSWP"] for i in issues if i.get("splitRecommended")),
        "teams": _teams(issues), "rate": rate, "samples": samples,
        "unseen": sum(1 for i in issues if contested(i) and (i.get("sourceType"), i["issueRef"]) not in seen),
        "diff": _diff_rows(issues), "groups": _groups(payload),
    }
    _CACHE[0], _CACHE[1] = payload, result
    return result
