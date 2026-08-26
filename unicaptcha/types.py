"""Public model vocabulary (ADR-0036): result/status types, task
addressing, proxy, secret strings, and the three config types.

All models are frozen dataclasses re-exported from the package root.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Generic, TypeVar

from unicaptcha._internal.repr import stub_bytes
from unicaptcha.errors import InvalidConfigError
from unicaptcha.solution.base import BaseSolution

T = TypeVar("T", bound=BaseSolution)


class TaskStatus(Enum):
    """Provider-side task outcomes, as answered by status queries."""

    PENDING = "PENDING"
    READY = "READY"
    NO_SOLUTION = "NO_SOLUTION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TaskRef:
    """Public, constructible identity of a task: ``(provider, task_id)``.

    Survives process restarts (persist the pair); routing vehicle for all
    task-addressing operations (ADR-0045).
    """

    provider: str
    task_id: int


@dataclass(frozen=True, slots=True)
class TaskResult(Generic[T]):
    """Rich result of a solved task (ADR-0008, ADR-0034).

    ``solution`` is non-optional: this type is produced only by ``solve()``
    and ``wait()``, which never return pending states.
    """

    solution: T
    task_id: int
    cost: Decimal | None
    raw: bytes
    provider: str
    created_at: datetime
    elapsed: timedelta

    @property
    def task_ref(self) -> TaskRef:
        """``TaskRef`` for aux-op addressing (ADR-0045)."""
        return TaskRef(provider=self.provider, task_id=self.task_id)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(solution={self.solution!r}, "
            f"task_id={self.task_id}, cost={self.cost!r}, raw={stub_bytes(self.raw)}, "
            f"provider={self.provider!r}, created_at={self.created_at!r}, "
            f"elapsed={self.elapsed!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True, slots=True)
class TaskStatusResult:
    """Answer of a single-shot status query (ADR-0032, ADR-0056).

    Non-generic and carries no submission metadata: ``solution`` is
    ``BaseSolution | None``, populated only when ``status`` is ``READY``.
    """

    task_id: int
    provider: str
    status: TaskStatus
    solution: BaseSolution | None
    cost: Decimal | None
    raw: bytes

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(task_id={self.task_id}, "
            f"provider={self.provider!r}, status={self.status!r}, "
            f"solution={self.solution!r}, "
            f"cost={self.cost!r}, raw={stub_bytes(self.raw)})"
        )

    __str__ = __repr__


@dataclass(frozen=True, slots=True)
class TaskTicket(Generic[T]):
    """Ticket issued by ``submit()`` (ADR-0067, ADR-0075).

    Not user-constructible: its value is provenance — the bound solution
    type ``T`` and ``submitted_at`` are only meaningful for a task the
    engine really submitted. Obtain one from ``Solver.submit()`` /
    ``AsyncSolver.submit()``. ``instant_answer`` is set iff the provider
    answered the submit itself (instant tasks); ``wait()`` fast-paths on it.
    ``time`` is the resolved solve-timeline config carried from submit
    (ADR-0030); ``wait()`` derives its default budget and poll cadence from
    it.
    """

    task_ref: TaskRef
    submitted_at: datetime
    instant_answer: ParsedTask | None = None
    time: TimeConfig | None = None

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(task_ref={self.task_ref!r}, "
            f"submitted_at={self.submitted_at!r}, "
            f"instant_answer={self.instant_answer!r}, time={self.time!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True, slots=True)
class ParsedTask:
    """Public adapter-SDK vocabulary: parsed ``getTaskResult`` response
    (ADR-0058, formalized by ADR-0075)."""

    state: TaskStatus
    solution: BaseSolution | None
    cost: Decimal | None
    raw: bytes
    detail: str | None = None

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(state={self.state!r}, solution={self.solution!r}, "
            f"cost={self.cost!r}, raw={stub_bytes(self.raw)}, detail={self.detail!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True, slots=True)
class SubmitAccepted:
    """Public adapter-SDK vocabulary: parsed ``createTask`` response
    (ADR-0075). ``task_id`` is always present; ``instant_answer`` is set iff
    the provider answered inline."""

    task_id: int
    instant_answer: ParsedTask | None = None

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(task_id={self.task_id}, "
            f"instant_answer={self.instant_answer!r})"
        )

    __str__ = __repr__


class ProxyKind(Enum):
    """Proxy scheme; values are sent verbatim (ADR-0012, ADR-0028)."""

    HTTP = "HTTP"
    HTTPS = "HTTPS"
    SOCKS4 = "SOCKS4"
    SOCKS5 = "SOCKS5"


@dataclass(frozen=True, slots=True)
class Proxy:
    """Structured proxy configuration (ADR-0012).

    ``host`` must be non-empty and ``port`` in 1..65535; violations raise
    ``InvalidConfigError`` at construction. ``password`` stays a plain
    ``str`` (masking contracts are scoped to API keys, ADR-0014).
    """

    host: str
    port: int
    kind: ProxyKind = ProxyKind.HTTP
    username: str | None = None
    password: str | None = None

    def __post_init__(self) -> None:
        if not self.host:
            raise InvalidConfigError("Proxy.host must be a non-empty string")
        if not 1 <= self.port <= 65535:
            raise InvalidConfigError(f"Proxy.port must be in 1..65535, got {self.port}")


class SecretStr:
    """Secret value wrapper with a full-mask repr/str (ADR-0014).

    - ``repr``/``str`` render ``***`` (no partial characters).
    - Value equality against another ``SecretStr``; comparing to anything
      else is a category error and raises ``TypeError`` (``None`` compares
      ``False``).
    - ``hash`` is the hash of the wrapped value.
    - Picklable.
    """

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "***"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if not isinstance(other, SecretStr):
            raise TypeError(
                "SecretStr can only be compared to SecretStr, "
                f"not {type(other).__name__}"
            )
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)


@dataclass(frozen=True, slots=True)
class NetworkConfig:
    """Network-level knobs (ADR-0024): per-request timeout and connection
    pool limits. ``None`` means "unspecified" (ADR-0043); explicit values
    are validated at construction (ADR-0042)."""

    timeout: float | None = None
    max_connections: int | None = None
    max_keepalive_connections: int | None = None

    def __post_init__(self) -> None:
        if self.timeout is not None and self.timeout <= 0:
            raise InvalidConfigError("NetworkConfig.timeout must be > 0")
        if self.max_connections is not None and self.max_connections <= 0:
            raise InvalidConfigError("NetworkConfig.max_connections must be > 0")
        if (
            self.max_keepalive_connections is not None
            and self.max_keepalive_connections <= 0
        ):
            raise InvalidConfigError(
                "NetworkConfig.max_keepalive_connections must be > 0"
            )


@dataclass(frozen=True, slots=True)
class TimeConfig:
    """Solve-timeline config (ADR-0043, ADR-0030): the outer wall-clock
    budget (``total_timeout``) and the poll cadence (``poll_interval``,
    ``poll_delay``). ``None`` means "unspecified"."""

    total_timeout: float | None = None
    poll_interval: float | None = None
    poll_delay: float | None = None

    def __post_init__(self) -> None:
        if self.total_timeout is not None and self.total_timeout <= 0:
            raise InvalidConfigError("TimeConfig.total_timeout must be > 0")
        if self.poll_interval is not None and self.poll_interval <= 0:
            raise InvalidConfigError("TimeConfig.poll_interval must be > 0")
        if self.poll_delay is not None and self.poll_delay < 0:
            raise InvalidConfigError("TimeConfig.poll_delay must be >= 0")


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Retry strategy (ADR-0043, ADR-0042): attempt count and backoff
    shape. ``backoff_cap`` must be ``>= backoff_base`` (a cap below its own
    base cannot back off)."""

    max_attempts: int | None = None
    backoff_base: float | None = None
    backoff_cap: float | None = None

    def __post_init__(self) -> None:
        if self.max_attempts is not None and self.max_attempts <= 0:
            raise InvalidConfigError("RetryConfig.max_attempts must be > 0")
        if self.backoff_base is not None and self.backoff_base <= 0:
            raise InvalidConfigError("RetryConfig.backoff_base must be > 0")
        if self.backoff_cap is not None and self.backoff_cap <= 0:
            raise InvalidConfigError("RetryConfig.backoff_cap must be > 0")
        if (
            self.backoff_base is not None
            and self.backoff_cap is not None
            and self.backoff_cap < self.backoff_base
        ):
            raise InvalidConfigError("RetryConfig.backoff_cap must be >= backoff_base")


__all__ = [
    "NetworkConfig",
    "ParsedTask",
    "Proxy",
    "ProxyKind",
    "RetryConfig",
    "SecretStr",
    "SubmitAccepted",
    "TaskRef",
    "TaskResult",
    "TaskStatus",
    "TaskStatusResult",
    "TaskTicket",
    "TimeConfig",
]
