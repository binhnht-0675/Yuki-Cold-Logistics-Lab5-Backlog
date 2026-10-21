"""Run-time estimate for `plan`: write pace + the hourly write cap of gh_runner (rolling 60 minutes)."""
from __future__ import annotations

WINDOW_S = 3600.0


def estimate_seconds(total: int, pace: float, per_hour: int) -> float:
    """Seconds for `total` writes at one per `pace` s, waiting whenever `per_hour` writes fall in 60 minutes.

    Rate-limit waits imposed by GitHub are not included.
    """
    if total <= 0:
        return 0
    if not per_hour or per_hour * pace >= WINDOW_S:
        return total * pace  # the pace alone keeps the run under the cap
    full_windows, last = (total - 1) // per_hour, (total - 1) % per_hour + 1
    return max(total * pace, full_windows * WINDOW_S + last * pace)


def format_duration(seconds: float) -> str:
    if seconds < WINDOW_S:
        return f"約 {seconds / 60:.0f} 分"
    return f"約 {seconds / WINDOW_S:.1f} 時間"
