"""Thin wrapper around the logged-in `gh` CLI (no token / env reading).

- Every call is `gh <args>`; JSON request bodies go through stdin (`--input -`).
- Each call has a timeout (default 120 s).
- Write calls are paced (default 1 write / 2.5 s) and capped per rolling 60 minutes
  (default 450, below GitHub's ~500 content-creating requests / hour): at the cap the
  runner WAITS until enough writes in the window are 60 minutes old, then continues.
  The window is kept in a file (write_window_store.py, default `<state-dir>/write-window.json`)
  so the cap holds across runs and across skill 1 / skill 2; without a file it is per process.
  Counting the window and taking a slot happen under one lock, so concurrent runs cannot overshoot.
- Rate limits (secondary: HTTP 403/429 or HTTP 200 with "secondary rate limit" in the body;
  primary: "API rate limit exceeded", GraphQL `errors` of type RATE_LIMITED, also inside an
  HTTP 200 response) -> wait `retry-after` seconds if given, else until `x-ratelimit-reset`
  when `x-ratelimit-remaining: 0`, else `retry_wait` (60 s); doubling on each repeat, at most
  `max_retries` times; then raise RateLimitStop so the caller stops with exit 75. The headers are
  read from the response itself: every call runs `gh api ... --include` and the header block is
  split off the body (gh_include_response.py) before the body is parsed.
- Transient errors (timeout, HTTP 5xx, network) on READS are retried (5 s, doubling, at most
  `max_retries`). On WRITES only errors that prove nothing was sent (DNS / connect) are
  retried; a write whose effect is unknown (timeout, 5xx) stops at once: re-running the
  command re-reads GitHub first, so it continues without duplicates.
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import time
from typing import Any, Callable, List, Optional

from gh_include_response import body_errors, split_include  # noqa: F401
from write_window_store import WINDOW_S, MemoryWindow, add_write_window_args, window_from_args  # noqa: F401

RATE_LIMIT_RX = re.compile(
    r"secondary rate limit|HTTP 429|submitted too quickly|abuse detection|"
    r"HTTP 403.*rate limit|rate limit.*HTTP 403|API rate limit exceeded|RATE_LIMITED",
    re.I,
)
RETRY_AFTER_RX = re.compile(r"retry-after:\s*(\d+)", re.I)
RESET_RX = re.compile(r"x-ratelimit-reset:\s*(\d+)", re.I)
REMAINING_ZERO_RX = re.compile(r"x-ratelimit-remaining:\s*0\b", re.I)
NOT_SENT_RX = re.compile(r"dial tcp|no such host|could not resolve host|connection refused|"
                         r"network is unreachable|TLS handshake timeout", re.I)
TRANSIENT_RX = re.compile(r"HTTP 5\d\d|Bad Gateway|Service Unavailable|Gateway Timeout|Server Error|"
                          r"connection reset|unexpected EOF|i/o timeout", re.I)
EXIT_RATE_LIMIT_STOP = 75  # EX_TEMPFAIL: re-run the same command later
EXIT_TIMEOUT = 124


class GhError(RuntimeError):
    def __init__(self, args: List[str], code: int, stderr: str):
        super().__init__(f"gh exited {code}: {stderr.strip()[:300]}")
        self.args_list, self.code, self.stderr = args, code, stderr


class RateLimitStop(GhError):
    """Raised after retries are exhausted on a rate limit."""


class GhRunner:
    def __init__(self, gh: str = "gh", pace: float = 2.5, retry_wait: float = 60.0,
                 max_retries: int = 5, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, timeout: float = 120.0,
                 max_per_hour: int = 450, transient_wait: float = 5.0,
                 wall: Callable[[], float] = time.time, notify: Callable[[str], None] = print,
                 window=None):
        self.cmd = shlex.split(gh)
        self.pace, self.retry_wait, self.max_retries = pace, retry_wait, max_retries
        self.timeout, self.max_per_hour, self.transient_wait = timeout, max_per_hour, transient_wait
        self.sleep, self.clock, self.wall, self.notify = sleep, clock, wall, notify
        self._last_write: Optional[float] = None
        self.window = window or MemoryWindow()  # wall() epoch of every write attempt in the last 60 minutes
        self.writes = 0

    def _pace(self) -> None:
        if self._last_write is not None and self.pace > 0:
            wait = self.pace - (self.clock() - self._last_write)
            if wait > 0:
                self.sleep(wait)

    def _take_slot(self) -> None:
        """Count the window and take a slot in one step (one lock), waiting while the window is full."""
        while True:  # re-read each time: another run sharing the file may have written meanwhile
            times = self.window.reserve(self.wall(), self.max_per_hour)
            if times is None:
                return
            freed_at = times[len(times) - self.max_per_hour]  # once this one is 60 minutes old, one slot is free
            wait = min(max(WINDOW_S - (self.wall() - freed_at), 1.0), WINDOW_S)
            resume = time.strftime("%H:%M", time.localtime(self.wall() + wait))
            self.notify(f"WAIT 書き込み上限 {self.max_per_hour} 件 / 60 分に到達（記録: {self.window.path or 'この実行のみ'}）:"
                        f" 約 {wait / 60:.0f} 分待機（{resume} ごろ再開。止めても同じコマンドの再実行で続きから）")
            self.sleep(wait)

    def _exec(self, args: List[str], stdin: Optional[str]):
        try:
            proc = subprocess.run(self.cmd + list(args), input=stdin, capture_output=True,
                                  text=True, encoding="utf-8", timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return None, "", f"timeout: gh が {self.timeout:g} 秒以内に終わりませんでした"
        return proc.returncode, proc.stdout or "", proc.stderr or ""

    def _limit_wait(self, text: str, attempt: int) -> float:
        m = RETRY_AFTER_RX.search(text)
        if m:
            return float(m.group(1)) * (2 ** attempt)
        reset = RESET_RX.search(text)
        if reset and REMAINING_ZERO_RX.search(text):
            return max(float(reset.group(1)) - self.wall(), 0.0) + 1
        return self.retry_wait * (2 ** attempt)

    def run(self, args: List[str], stdin: Optional[str] = None, write: bool = False) -> str:
        attempt = 0
        while True:
            if write:
                if attempt == 0:
                    self._pace()  # a retry already waited longer than the pace
                self._take_slot()
            code, out, err = self._exec(args, stdin)
            headers, out = split_include(out) if "--include" in args else ("", out)
            if write:
                self._last_write = self.clock()
            text = (err if code != 0 else "") + "\n" + body_errors(out)
            if RATE_LIMIT_RX.search(text):  # also an HTTP 200 whose body reports the limit
                if attempt >= self.max_retries:
                    raise RateLimitStop(list(args), code or 1, text)
                self.sleep(self._limit_wait(text + "\n" + headers, attempt))
                attempt += 1
                continue
            if code == 0:
                if write:
                    self.writes += 1
                return out
            not_sent = bool(NOT_SENT_RX.search(text))
            transient = not_sent or (not write and (code is None or bool(TRANSIENT_RX.search(text))))
            if not transient or attempt >= self.max_retries:
                raise GhError(list(args), EXIT_TIMEOUT if code is None else code, self._explain(text, write, transient))
            self.sleep(self.transient_wait * (2 ** attempt))
            attempt += 1

    def _explain(self, text: str, write: bool, transient: bool) -> str:
        if transient:
            return f"一時的なエラーが {self.max_retries + 1} 回続いたため停止（時間をおいて再実行）: {text.strip()}"
        if write and (text.startswith("timeout") or TRANSIENT_RX.search(text)):
            return ("書き込みの結果が不明のため再送せず停止（同じコマンドを再実行すると GitHub の現状を読み直して"
                    f"続きから進む）: {text.strip()}")
        return text.strip()

    def api_json(self, path: str, method: str = "GET", body: Optional[dict] = None,
                 write: bool = False) -> Any:
        args = ["api", path, "--method", method]
        stdin = None
        if body is not None:
            args += ["--input", "-"]
            stdin = json.dumps(body, ensure_ascii=False)
        args.append("--include")  # response headers (retry-after, x-ratelimit-*) for the rate-limit wait
        out = self.run(args, stdin=stdin, write=write)
        return json.loads(out) if out.strip() else None

    def graphql(self, query: str, variables: Optional[dict] = None, write: bool = False) -> dict:
        body = {"query": query, "variables": variables or {}}
        out = self.run(["api", "graphql", "--input", "-", "--include"],
                       stdin=json.dumps(body, ensure_ascii=False), write=write)
        data = json.loads(out)
        if data.get("errors"):  # rate limits were already waited out / raised in run()
            raise GhError(["api", "graphql"], 1, body_errors(out))
        return data["data"]


def add_runner_args(parser) -> None:
    """Common CLI options for every skill script."""
    parser.add_argument("--gh", default="gh", help="gh コマンド（テストでは偽 gh を指定）")
    parser.add_argument("--pace", type=float, default=2.5, help="書き込み間隔（秒）")
    parser.add_argument("--retry-wait", type=float, default=60.0, help="レート制限時の初回待機（秒、retry-after がなければ）")
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=120.0, help="gh 1 回あたりの制限時間（秒）")
    parser.add_argument("--max-writes-per-hour", type=int, default=450,
                        help="直近 60 分の書き込み上限（到達で待機。0 = 無効）")


def runner_from_args(ns) -> GhRunner:
    return GhRunner(gh=ns.gh, pace=ns.pace, retry_wait=ns.retry_wait, max_retries=ns.max_retries,
                    timeout=getattr(ns, "timeout", 120.0), max_per_hour=getattr(ns, "max_writes_per_hour", 450),
                    window=window_from_args(ns))
