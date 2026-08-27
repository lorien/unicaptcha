"""Injectable clock/sleep seam for deterministic timing tests (ADR-0033,
architecture.md §10). The engine reads monotonic time for budgets/elapsed and
wall-clock for timestamps through this seam; task 16 injects a fake clock."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """The injectable clock/sleep seam (ADR-0033, architecture.md §10).

    ``monotonic``/``wallclock`` drive budgets/elapsed/timestamps for both
    engines; ``sleep`` is the blocking wait used by the sync engine for
    backoff/poll pauses (the async engine awaits ``asyncio.sleep`` instead).
    A fake clock advances time instantly, giving deterministic timing tests.
    """

    def monotonic(self) -> float: ...

    def wallclock(self) -> datetime: ...

    def sleep(self, seconds: float) -> None: ...


class RealClock:
    """Production clock: ``time.monotonic``, UTC ``datetime.now`` and real
    ``time.sleep``."""

    def monotonic(self) -> float:
        return time.monotonic()

    def wallclock(self) -> datetime:
        return datetime.now(UTC)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


__all__ = ["Clock", "RealClock"]
