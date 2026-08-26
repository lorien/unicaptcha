"""Abandoned-task registry (ADR-0038, ADR-0060).

Bounded, append-only, thread-safe; per-client best-effort advisory.
Entries are added at submission acceptance and removed on successful
delivery or when a same-client status query reaches a terminal state.
Mutations are synchronous (no awaits) so they are safe during
cancellation unwinding (ADR-0016). Survives close (ADR-0033).
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime

from unicaptcha.types import TaskRef

_logger = logging.getLogger("unicaptcha")

_DEFAULT_LIMIT = 1000


class AbandonedTaskRegistry:
    """Thread-safe ordered registry of ``TaskRef`` -> abandoned-at."""

    __slots__ = ("_abandoned_at", "_limit", "_lock")

    def __init__(self, limit: int | None = _DEFAULT_LIMIT) -> None:
        self._lock = threading.Lock()
        self._abandoned_at: dict[TaskRef, datetime] = {}
        self._limit = limit

    def add(self, ref: TaskRef, at: datetime) -> None:
        with self._lock:
            self._abandoned_at[ref] = at
            if self._limit is not None:
                while len(self._abandoned_at) > self._limit:
                    oldest = next(iter(self._abandoned_at))
                    del self._abandoned_at[oldest]
                    _logger.warning(
                        "abandoned-task registry full (limit %d): evicted %r",
                        self._limit,
                        oldest,
                    )

    def remove(self, ref: TaskRef) -> None:
        with self._lock:
            self._abandoned_at.pop(ref, None)

    def snapshot(self) -> tuple[TaskRef, ...]:
        """Snapshot of the recorded TaskRefs (oldest first)."""
        with self._lock:
            return tuple(self._abandoned_at)

    def abandoned_at(self, ref: TaskRef) -> datetime | None:
        with self._lock:
            return self._abandoned_at.get(ref)

    def __len__(self) -> int:
        with self._lock:
            return len(self._abandoned_at)


__all__ = ["AbandonedTaskRegistry"]
