"""Shared test fakes. Not collected by pytest (filename not test_*)."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from unicaptcha._internal.clock import Clock
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import ErrorKind, error_from_kind
from unicaptcha.solution.base import BaseSolution
from unicaptcha.types import ParsedTask, SubmitAccepted, TaskRef, TaskStatus


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


class StubAdapter(BaseAdapter):
    """Shared minimal concrete adapter speaking the createTask/getTaskResult
    shape, driven by respx response sequences in engine and SDK-contract
    tests."""

    provider = "myservice"
    challenges: frozenset[type[BaseChallenge]] = frozenset()
    default_base_url = "https://myservice.example"

    def build_payload(self, challenge: BaseChallenge) -> dict[str, object]:
        return {"clientKey": "test-key", "task": "data"}

    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        data = json.loads(raw)
        if data.get("errorId"):
            kind, message = self.map_provider_error(raw)
            raise error_from_kind(kind, message, raw)
        instant = None
        if data.get("status") == "ready":
            instant = ParsedTask(
                state=TaskStatus.READY,
                solution=FakeSolution("tok1234"),
                cost=Decimal("0.001"),
                raw=raw,
            )
        return SubmitAccepted(task_id=data["taskId"], instant_answer=instant)

    def parse_task_status(self, raw: bytes) -> ParsedTask:
        data = json.loads(raw)
        status = data["status"]
        if status == "ready":
            return ParsedTask(
                state=TaskStatus.READY,
                solution=FakeSolution("tok1234"),
                cost=Decimal("0.001"),
                raw=raw,
            )
        if status == "unsolvable":
            return ParsedTask(
                state=TaskStatus.NO_SOLUTION, solution=None, cost=None, raw=raw
            )
        if status == "notfound":
            return ParsedTask(
                state=TaskStatus.UNKNOWN,
                solution=None,
                cost=None,
                raw=raw,
                detail="no such task",
            )
        return ParsedTask(state=TaskStatus.PENDING, solution=None, cost=None, raw=raw)

    def parse_balance(self, raw: bytes) -> Decimal:
        return Decimal(str(json.loads(raw)["balance"]))

    def report_bad_supported(self, challenge_type: type[BaseChallenge]) -> bool:
        return True

    def build_report_bad(self, task: TaskRef) -> dict[str, object]:
        return {"clientKey": "test-key", "taskId": task.task_id}

    def parse_report_bad(self, raw: bytes) -> bool:
        return json.loads(raw)["status"] == "success"

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        code = json.loads(raw).get("errorCode", "")
        if code == "ERROR_KEY_DOES_NOT_EXIST":
            return ErrorKind.AUTHENTICATION, "bad key"
        if code == "ERROR_TOO_MANY_REQUESTS":
            return ErrorKind.RATE_LIMIT, "too many requests"
        if code == "ERROR_NO_SLOT_AVAILABLE":
            return ErrorKind.SERVICE_BUSY, "no slot"
        return ErrorKind.PROVIDER, code
