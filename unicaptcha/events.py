"""Task lifecycle events (ADR-0018, as amended).

``TaskEvent`` describes what just happened in a task's life. Every solve
invocation ends in exactly one terminal event — ``PRE_FLIGHT_FAILED``,
``SUBMIT_FAILED``, ``RESULT_FAILED``, or ``RESULT_RECEIVED``. The terminal
failure kinds fire immediately before the terminal raise and carry the
matching ``error_kind``; cancellation is eventless.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from unicaptcha.errors import ErrorKind


class TaskEventKind(Enum):
    """What event just happened in the task's life."""

    PRE_FLIGHT_FAILED = "PRE_FLIGHT_FAILED"
    SUBMIT_REQUESTED = "SUBMIT_REQUESTED"
    SUBMIT_ACCEPTED = "SUBMIT_ACCEPTED"
    SUBMIT_FAILED = "SUBMIT_FAILED"
    RESULT_REQUESTED = "RESULT_REQUESTED"
    RESULT_RECEIVED = "RESULT_RECEIVED"
    RESULT_FAILED = "RESULT_FAILED"


@dataclass(frozen=True, slots=True)
class TaskEvent:
    """An observation about a task's lifecycle (ADR-0018).

    ``error_kind`` is set only on the terminal failure kinds (see the
    per-kind matrix in ADR-0018); it is ``None`` on in-progress and success
    kinds, and ``None`` on ``PRE_FLIGHT_FAILED`` caused by a wrong-provider
    ``TypeError``. ``detail`` never carries credentials.
    """

    kind: TaskEventKind
    provider: str
    elapsed: timedelta
    attempt: int
    task_id: int | None = None
    detail: str | None = None
    error_kind: ErrorKind | None = None


SyncEventHandler = Callable[[TaskEvent], None]
AsyncEventHandler = Callable[[TaskEvent], Awaitable[None] | None]

__all__ = [
    "AsyncEventHandler",
    "SyncEventHandler",
    "TaskEvent",
    "TaskEventKind",
]
