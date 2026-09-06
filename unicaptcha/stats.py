"""Client usage statistics via an ``on_event``-fed collector (ADR-0018).

A ``StatsCollector`` is a sync ``on_event`` handler: pass
``collector.on_event`` to ``Solver`` / ``AsyncSolver`` (constructor or
per call) and it tallies the terminal task events into cumulative
counts and elapsed time, per provider.

Terminal-event classification (events fire exactly one terminal event
per solve invocation):

- ``RESULT_RECEIVED`` → solved.
- ``PRE_FLIGHT_FAILED`` / ``SUBMIT_FAILED`` / ``RESULT_FAILED`` → failed.

Cost totals are deliberately out of scope here (USD/currency handling is
undecided — ADR-0040); this collector counts solves/failures and elapsed
time only. A ``threading.Lock`` keeps the counters safe for concurrent
solves (ADR-0027 thread-safe client).
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta

from unicaptcha.events import TaskEvent, TaskEventKind

__all__ = ["ProviderUsage", "StatsCollector", "UsageStats"]

_TERMINAL = frozenset(
    {
        TaskEventKind.PRE_FLIGHT_FAILED,
        TaskEventKind.SUBMIT_FAILED,
        TaskEventKind.RESULT_FAILED,
        TaskEventKind.RESULT_RECEIVED,
    }
)


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    """Cumulative usage for a single provider."""

    provider: str
    solved: int
    failed: int
    elapsed: timedelta

    @property
    def attempts(self) -> int:
        """Solved + failed tasks for this provider."""
        return self.solved + self.failed


@dataclass(frozen=True, slots=True)
class UsageStats:
    """Immutable usage snapshot; cost is out of scope (see module doc)."""

    solved: int
    failed: int
    elapsed: timedelta
    per_provider: Mapping[str, ProviderUsage]

    @property
    def attempts(self) -> int:
        """Solved + failed tasks across all providers."""
        return self.solved + self.failed


class StatsCollector:
    """Cumulative solve/failure counters fed by task lifecycle events.

    Use as an ``on_event`` handler — it is synchronous, so it works with
    both ``Solver`` and ``AsyncSolver``:

    .. code-block:: python

        collector = StatsCollector()
        with Solver([...], on_event=collector.on_event) as client:
            client.solve(...)
        collector.snapshot()
    """

    __slots__ = ("_elapsed", "_failed", "_lock", "_per_provider", "_solved")

    def __init__(self) -> None:
        self._solved = 0
        self._failed = 0
        self._elapsed = timedelta()
        self._per_provider: dict[str, ProviderUsage] = {}
        self._lock = threading.Lock()

    def on_event(self, event: TaskEvent) -> None:
        """Tally one task event; ignores non-terminal kinds."""
        if event.kind not in _TERMINAL:
            return
        solved = event.kind is TaskEventKind.RESULT_RECEIVED
        with self._lock:
            self._solved += 1 if solved else 0
            self._failed += 0 if solved else 1
            self._elapsed += event.elapsed
            prev = self._per_provider.get(event.provider)
            if prev is None:
                self._per_provider[event.provider] = ProviderUsage(
                    provider=event.provider,
                    solved=1 if solved else 0,
                    failed=0 if solved else 1,
                    elapsed=event.elapsed,
                )
            else:
                self._per_provider[event.provider] = ProviderUsage(
                    provider=event.provider,
                    solved=prev.solved + (1 if solved else 0),
                    failed=prev.failed + (0 if solved else 1),
                    elapsed=prev.elapsed + event.elapsed,
                )

    def snapshot(self) -> UsageStats:
        """An immutable copy of the current totals."""
        with self._lock:
            return UsageStats(
                solved=self._solved,
                failed=self._failed,
                elapsed=self._elapsed,
                per_provider=dict(self._per_provider),
            )

    def reset(self) -> None:
        """Zero all counters."""
        with self._lock:
            self._solved = 0
            self._failed = 0
            self._elapsed = timedelta()
            self._per_provider = {}
