"""Injectable clock/sleep seam for deterministic timing tests (ADR-0033,
architecture.md §10). The engine reads monotonic time for budgets/elapsed and
wall-clock for timestamps through this seam; task 16 injects a fake clock."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """The time-reading half of the seam (sleeps are per-tier)."""

    def monotonic(self) -> float: ...

    def wallclock(self) -> datetime: ...


class RealClock:
    """Production clock: ``time.monotonic`` and UTC ``datetime.now``."""

    def monotonic(self) -> float:
        return time.monotonic()

    def wallclock(self) -> datetime:
        return datetime.now(UTC)


__all__ = ["Clock", "RealClock"]
