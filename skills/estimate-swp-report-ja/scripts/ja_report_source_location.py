"""Where the source skill's scripts (tkm:estimate-swp scripts/) live on this machine.

Order: ESTIMATE_SWP_SCRIPTS when set, then the legacy install (home .claude/skills/estimate-swp), then the
kit layout used since the 24/10 reinstall (home .claude/skills/tkm/skills/estimate-swp). A folder counts only when
it has core/__init__.py. Nothing found → ImportError naming every place looked at.
"""
from __future__ import annotations

import os
from typing import Mapping

CANDIDATES = (("skills", "estimate-swp", "scripts"), ("skills", "tkm", "skills", "estimate-swp", "scripts"))


def find_source_scripts(home: str, env: Mapping[str, str]) -> str:
    looked = ([env["ESTIMATE_SWP_SCRIPTS"]] if env.get("ESTIMATE_SWP_SCRIPTS") else []) + \
             [os.path.join(home, ".claude", *parts) for parts in CANDIDATES]
    for path in looked:
        if os.path.exists(os.path.join(path, "core", "__init__.py")):
            return path
    raise ImportError("tkm:estimate-swp のスクリプトが見つかりません（" + "、".join(looked) + "）")
