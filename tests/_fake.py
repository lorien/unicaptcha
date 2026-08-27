"""Shared test fakes. Not collected by pytest (filename not test_*)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, ClassVar

from unicaptcha._internal.clock import Clock
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import ErrorKind
from unicaptcha.solution.base import BaseSolution
from unicaptcha.types import ParsedTask, SubmitAccepted, TaskStatus


@dataclass(frozen=True, slots=True)
class FakeSolution(BaseSolution):
    """Concrete BaseSolution subclass for tests (its repr will be
    token-truncating per policy once solution kinds land, task 6)."""

    text: str = "token1234"


class FakeClock(Clock):
    """Instant, deterministic clock/sleep seam for engine timing tests
    (task 16). ``sleep`` advances fake monotonic/wall time immediately, so
    backoff and poll pauses consume no real time."""

    def __init__(
        self,
        start: float = 1000.0,
        start_wall: datetime | None = None,
    ) -> None:
        self._mono = float(start)
        self._wall = start_wall or datetime(2026, 8, 27, 12, 0, 0, tzinfo=UTC)
        self.sleep_calls: list[float] = []

    def monotonic(self) -> float:
        return self._mono

    def wallclock(self) -> datetime:
        return self._wall

    def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self._mono += seconds
        self._wall += timedelta(seconds=seconds)

    def advance(self, seconds: float) -> None:
        """Advance fake time without recording a 'sleep' call (used to
        simulate a stale ticket)."""
        self._mono += seconds
        self._wall += timedelta(seconds=seconds)

    @property
    def sleep_total(self) -> float:
        return sum(self.sleep_calls)


class FakeAdapter(BaseAdapter):
    """Minimal concrete adapter implementing the SDK contract (ADR-0046
    reference-adapter stand-in for tests)."""

    provider: ClassVar[str] = "myservice"
    challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset()
    default_base_url: ClassVar[str] = "https://myservice.example"

    def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
        return {}

    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        return SubmitAccepted(task_id=1)

    def parse_task_status(self, raw: bytes) -> ParsedTask:
        return ParsedTask(state=TaskStatus.PENDING, solution=None, cost=None, raw=raw)

    def parse_balance(self, raw: bytes) -> Decimal:
        return Decimal("0.00")

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        return ErrorKind.PROVIDER, "provider error"
