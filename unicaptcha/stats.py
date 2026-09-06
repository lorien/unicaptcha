"""Client usage statistics via an ``on_event``-fed collector (ADR-0018).

A ``StatsCollector`` is a sync ``on_event`` handler: pass
``collector.on_event`` to ``Solver`` / ``AsyncSolver`` (constructor or
per call) and it tallies the terminal task events into cumulative
counts, elapsed time, and cost — per provider and per currency.

Terminal-event classification (events fire exactly one terminal event
per solve invocation):

- ``RESULT_RECEIVED`` → solved (carries ``cost`` in the adapter's
  currency).
- ``PRE_FLIGHT_FAILED`` / ``SUBMIT_FAILED`` / ``RESULT_FAILED`` → failed.

Cost totals are currency-safe: ``ProviderUsage.cost`` sums only one
adapter's costs (one currency per adapter instance), and
``UsageStats.cost_totals`` keys totals by currency code — there is never
a blind cross-currency sum (ADR-0040). A ``threading.Lock`` keeps the
counters safe for concurrent solves (ADR-0027 thread-safe client).
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

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
    """Cumulative usage for a single provider.

    ``cost`` sums the solved tasks' prices for this provider (one
    currency per adapter instance); ``currency`` is that currency.
    """

    provider: str
    solved: int
    failed: int
    elapsed: timedelta
    cost: Decimal | None = None
    currency: str | None = None

    @property
    def attempts(self) -> int:
        """Solved + failed tasks for this provider."""
        return self.solved + self.failed


@dataclass(frozen=True, slots=True)
class UsageStats:
    """Immutable usage snapshot (ADR-0040 currency-safe costs)."""

    solved: int
    failed: int
    elapsed: timedelta
    per_provider: Mapping[str, ProviderUsage]
    cost_totals: Mapping[str, Decimal] = field(default_factory=dict[str, Decimal])

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

    __slots__ = (
        "_cost_totals",
        "_elapsed",
        "_failed",
        "_lock",
        "_per_provider",
        "_solved",
    )

    def __init__(self) -> None:
        self._solved = 0
        self._failed = 0
        self._elapsed = timedelta()
        self._per_provider: dict[str, ProviderUsage] = {}
        self._cost_totals: dict[str, Decimal] = {}
        self._lock = threading.Lock()

    def on_event(self, event: TaskEvent) -> None:
        """Tally one task event; ignores non-terminal kinds."""
        if event.kind not in _TERMINAL:
            return
        solved = event.kind is TaskEventKind.RESULT_RECEIVED
        cost = event.cost
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
                    cost=cost.amount if cost is not None else None,
                    currency=cost.currency if cost is not None else None,
                )
            else:
                self._per_provider[event.provider] = ProviderUsage(
                    provider=event.provider,
                    solved=prev.solved + (1 if solved else 0),
                    failed=prev.failed + (0 if solved else 1),
                    elapsed=prev.elapsed + event.elapsed,
                    cost=(
                        (prev.cost or Decimal("0")) + cost.amount
                        if cost is not None
                        else prev.cost
                    ),
                    currency=(
                        cost.currency if cost is not None else prev.currency or None
                    ),
                )
            if cost is not None:
                self._cost_totals[cost.currency] = (
                    self._cost_totals.get(cost.currency, Decimal("0")) + cost.amount
                )

    def snapshot(self) -> UsageStats:
        """An immutable copy of the current totals."""
        with self._lock:
            return UsageStats(
                solved=self._solved,
                failed=self._failed,
                elapsed=self._elapsed,
                per_provider=dict(self._per_provider),
                cost_totals=dict(self._cost_totals),
            )

    def reset(self) -> None:
        """Zero all counters."""
        with self._lock:
            self._solved = 0
            self._failed = 0
            self._elapsed = timedelta()
            self._per_provider = {}
            self._cost_totals = {}
