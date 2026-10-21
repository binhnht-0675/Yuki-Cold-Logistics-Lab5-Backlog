"""Rolling 60-minute write window, kept in a JSON file so the cap holds across runs and skills.

File (default `<state-dir>/write-window.json`, never committed):
  {"version": 1, "windowSeconds": 3600, "writes": [<epoch seconds of each write attempt>, ...]}
Before each write attempt, `reserve` counts the last 60 minutes and, if a slot is free, appends the
attempt and saves (temp file + rename) - both inside ONE exclusive lock when the platform has `fcntl`,
so two runs sharing the file, even at the same moment, cannot both take the last slot.
Entries older than 60 minutes are dropped on each save.
An unreadable / malformed file raises WriteWindowError (the caller stops with exit 1) instead of
silently starting again from 0, unless `ignore_broken` is set explicitly.
"""
from __future__ import annotations

import contextlib
import json
import os
import tempfile
from typing import Callable, List, Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX: no lock, the re-read still merges most cases
    fcntl = None

WINDOW_S = 3600.0
VERSION = 1


class WriteWindowError(ValueError):
    """The window file cannot be trusted; nothing should be written until it is fixed."""


def _recent(times: List[float], now: float) -> List[float]:
    return sorted(t for t in times if now - t < WINDOW_S)


class MemoryWindow:
    """Window of the current process only (used when no file is given, e.g. read-only skills)."""

    path = None

    def __init__(self) -> None:
        self.times: List[float] = []

    def check(self) -> None:
        return None

    def reserve(self, now: float, cap: int) -> Optional[List[float]]:
        """Take a slot at `now`: None when taken, else the last-60-minute times (window full)."""
        self.times = _recent(self.times, now)
        if cap and len(self.times) >= cap:
            return list(self.times)
        self.times.append(now)
        return None


class FileWindow:
    def __init__(self, path: str, ignore_broken: bool = False, notify: Callable[[str], None] = print):
        self.path, self.ignore_broken, self.notify = path, ignore_broken, notify
        self._warned = False

    def _read(self) -> List[float]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
            writes = data.get("writes") if isinstance(data, dict) else None
            ok = (isinstance(data, dict) and data.get("version") == VERSION and isinstance(writes, list)
                  and all(isinstance(t, (int, float)) and not isinstance(t, bool) for t in writes))
        except (OSError, ValueError) as e:
            ok, why = False, str(e)
        else:
            why = "形式が違う（version / writes）"
        if ok:
            return [float(t) for t in writes]
        msg = (f"書き込み記録 {self.path} が読めません（{why}）。直近 60 分の書き込み数が分からないため止めます。"
               "ファイルを直すか、60 分以上あけてから --ignore-broken-write-window を付けて再実行")
        if not self.ignore_broken:
            raise WriteWindowError(msg)
        if not self._warned:
            self._warned = True
            self.notify("WARN " + msg.split("。")[0] + "。--ignore-broken-write-window のため 0 件から数えます")
        return []

    def check(self) -> None:
        self._read()

    @contextlib.contextmanager
    def _locked(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        if fcntl is None:
            yield
            return
        with open(self.path + ".lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def reserve(self, now: float, cap: int) -> Optional[List[float]]:
        """Count and take a slot under one lock: None when taken, else the last-60-minute times (window full)."""
        with self._locked():
            times = _recent(self._read(), now)
            if cap and len(times) >= cap:
                return times
            self._save(times + [now])
        self.ignore_broken = False  # the file is valid again from here on
        return None

    def _save(self, times: List[float]) -> None:
        body = json.dumps({"version": VERSION, "windowSeconds": int(WINDOW_S), "writes": times})
        fd, tmp = tempfile.mkstemp(prefix=".write-window-", dir=os.path.dirname(os.path.abspath(self.path)))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(body)
            os.replace(tmp, self.path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise


def add_write_window_args(parser) -> None:
    """Skills that write (skill 1 / skill 2): where the shared 60-minute window is kept."""
    parser.add_argument("--write-window", help="直近 60 分の書き込み記録（既定: <state-dir>/write-window.json。"
                        "スキル 1 / 2 で同じファイルを使う）")
    parser.add_argument("--ignore-broken-write-window", action="store_true",
                        help="書き込み記録が壊れていても 0 件から数えて続ける（既定は exit 1 で停止）")


def window_from_args(ns):
    """FileWindow for CLIs that called add_write_window_args, else None (per-process window)."""
    if not hasattr(ns, "write_window"):
        return None
    path = ns.write_window or os.path.join(getattr(ns, "state_dir", "state"), "write-window.json")
    window = FileWindow(path, ignore_broken=ns.ignore_broken_write_window)
    if getattr(ns, "apply", False):
        window.check()  # stop before the first read / write; dry-runs never open the file
    return window
