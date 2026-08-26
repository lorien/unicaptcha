"""TaskEngine core tests (submit/solve/wait, both tiers).

Timing is kept fast through the engine-level config (poll_delay 0, tiny
intervals/budgets/backoff); the full deterministic timing suite is task 16.
"""

import asyncio
import json
import threading
from decimal import Decimal

import httpx
import pytest
import respx
from _fake import FakeSolution

from unicaptcha import (
    AuthenticationError,
    ImageChallenge,
    NetworkError,
    NoSolutionError,
    ProviderError,
    RateLimitError,
    RetryConfig,
    ServiceBusyError,
    TaskEventKind,
    TaskStatus,
    TaskTimeoutError,
    TimeConfig,
)
from unicaptcha._internal.async_engine import AsyncTaskEngine
from unicaptcha._internal.engine import TaskEngine
from unicaptcha._internal.errors import error_from_kind
from unicaptcha._internal.http import AsyncHttpTransport, HttpTransport
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import ErrorKind
from unicaptcha.types import ParsedTask, SubmitAccepted

BASE = "https://myservice.example"
CREATE = f"{BASE}/createTask"
STATUS = f"{BASE}/getTaskResult"

FAST_TIME = TimeConfig(poll_delay=0.0, poll_interval=0.01, total_timeout=0.5)
FAST_RETRY = RetryConfig(max_attempts=3, backoff_base=0.001, backoff_cap=0.001)


class ScriptedAdapter(BaseAdapter):
    """JSON-family adapter speaking the createTask/getTaskResult shape."""

    provider = "myservice"
    challenges: frozenset[type[BaseChallenge]] = frozenset()
    default_base_url = BASE

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
        return Decimal(json.loads(raw)["balance"])

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        code = json.loads(raw).get("errorCode", "")
        if code == "ERROR_KEY_DOES_NOT_EXIST":
            return ErrorKind.AUTHENTICATION, "bad key"
        if code == "ERROR_TOO_MANY_REQUESTS":
            return ErrorKind.RATE_LIMIT, "too many requests"
        if code == "ERROR_NO_SLOT_AVAILABLE":
            return ErrorKind.SERVICE_BUSY, "no slot"
        return ErrorKind.PROVIDER, code


def _submit_body(task_id: int = 777, **extra: object) -> bytes:
    payload: dict[str, object] = {"errorId": 0, "taskId": task_id}
    payload.update(extra)
    return json.dumps(payload).encode()


def _status_body(status: str) -> bytes:
    return json.dumps({"errorId": 0, "status": status}).encode()


def make_engine() -> TaskEngine:
    return TaskEngine(
        HttpTransport(),
        shutdown=threading.Event(),
        time=FAST_TIME,
        retry=FAST_RETRY,
    )


def make_async_engine() -> AsyncTaskEngine:
    return AsyncTaskEngine(
        AsyncHttpTransport(),
        time=FAST_TIME,
        retry=FAST_RETRY,
    )


@pytest.fixture
def adapter() -> ScriptedAdapter:
    return ScriptedAdapter("test-key")


@pytest.fixture
def challenge() -> ImageChallenge:
    return ImageChallenge(b"png-bytes")


class TestSyncCore:
    def test_solve_happy_path(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        events = []
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit_body(777))
            )
            status = respx.post(STATUS).mock(
                side_effect=[
                    httpx.Response(200, content=_status_body("processing")),
                    httpx.Response(200, content=_status_body("ready")),
                ]
            )
            engine = make_engine()
            result = engine.solve(adapter, challenge, on_event=events.append)
        assert result.task_id == 777
        assert result.provider == "myservice"
        assert result.cost == Decimal("0.001")
        assert result.solution == FakeSolution("tok1234")
        assert result.created_at.tzinfo is not None
        assert status.call_count == 2
        assert [e.kind for e in events] == [
            TaskEventKind.SUBMIT_REQUESTED,
            TaskEventKind.SUBMIT_ACCEPTED,
            TaskEventKind.RESULT_REQUESTED,
            TaskEventKind.RESULT_REQUESTED,
            TaskEventKind.RESULT_RECEIVED,
        ]
        poll_request = json.loads(status.calls.last.request.content)
        assert poll_request == {"clientKey": "test-key", "taskId": 777}

    def test_instant_answer_fast_path(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        events = []
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(
                    200, content=_submit_body(5, status="ready")
                )
            )
            status = respx.post(STATUS)
            engine = make_engine()
            result = engine.solve(adapter, challenge, on_event=events.append)
        assert result.task_id == 5
        assert status.call_count == 0
        assert [e.kind for e in events] == [
            TaskEventKind.SUBMIT_REQUESTED,
            TaskEventKind.SUBMIT_ACCEPTED,
            TaskEventKind.RESULT_RECEIVED,
        ]

    def test_submit_then_wait_two_phase(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit_body(9))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            engine = make_engine()
            ticket = engine.submit(adapter, challenge)
            assert ticket.task_ref.task_id == 9
            assert ticket.instant_answer is None
            assert ticket.time is not None and ticket.time.poll_delay == 0.0
            result = engine.wait(adapter, ticket)
        assert result.task_id == 9

    def test_retry_on_500_then_success(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            create = respx.post(CREATE).mock(
                side_effect=[
                    httpx.Response(500, content=b"boom"),
                    httpx.Response(200, content=_submit_body(1)),
                ]
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            engine = make_engine()
            result = engine.solve(adapter, challenge)
        assert result.task_id == 1
        assert create.call_count == 2

    def test_429_exhaustion_raises_rate_limit(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            create = respx.post(CREATE).mock(
                return_value=httpx.Response(429, content=b"slow")
            )
            engine = make_engine()
            with pytest.raises(RateLimitError):
                engine.solve(adapter, challenge)
        assert create.call_count == 3

    def test_502_fails_fast(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            create = respx.post(CREATE).mock(
                return_value=httpx.Response(502, content=b"gw")
            )
            engine = make_engine()
            with pytest.raises(NetworkError):
                engine.solve(adapter, challenge)
        assert create.call_count == 1

    def test_presend_network_error_retried(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            create = respx.post(CREATE).mock(
                side_effect=[
                    httpx.ConnectError("refused"),
                    httpx.Response(200, content=_submit_body(2)),
                ]
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            engine = make_engine()
            result = engine.solve(adapter, challenge)
        assert result.task_id == 2
        assert create.call_count == 2

    def test_read_timeout_fails_fast(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            create = respx.post(CREATE).mock(side_effect=httpx.ReadTimeout("late"))
            engine = make_engine()
            with pytest.raises(NetworkError):
                engine.solve(adapter, challenge)
        assert create.call_count == 1

    def test_provider_payload_error_maps_kind(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        body = json.dumps(
            {"errorId": 12, "errorCode": "ERROR_KEY_DOES_NOT_EXIST"}
        ).encode()
        with respx.mock:
            respx.post(CREATE).mock(return_value=httpx.Response(403, content=body))
            engine = make_engine()
            with pytest.raises(AuthenticationError) as excinfo:
                engine.solve(adapter, challenge)
        assert excinfo.value.raw_response == body

    def test_busy_payload_retried_then_service_busy(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        body = json.dumps(
            {"errorId": 1, "errorCode": "ERROR_NO_SLOT_AVAILABLE"}
        ).encode()
        with respx.mock:
            create = respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=body)
            )
            engine = make_engine()
            with pytest.raises(ServiceBusyError):
                engine.solve(adapter, challenge)
        assert create.call_count == 3

    def test_no_solution(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit_body(3))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("unsolvable"))
            )
            engine = make_engine()
            with pytest.raises(NoSolutionError):
                engine.solve(adapter, challenge)

    def test_unknown_fails_fast_provider_error(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit_body(4))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("notfound"))
            )
            engine = make_engine()
            with pytest.raises(ProviderError):
                engine.solve(adapter, challenge)

    def test_total_timeout(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit_body(6))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("processing"))
            )
            engine = make_engine()
            with pytest.raises(TaskTimeoutError):
                engine.solve(adapter, challenge)


class TestAsyncCore:
    @pytest.mark.asyncio
    async def test_solve_happy_path(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit_body(11))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            engine = make_async_engine()
            result = await engine.solve(adapter, challenge)
        assert result.task_id == 11
        assert result.solution == FakeSolution("tok1234")

    @pytest.mark.asyncio
    async def test_instant_answer(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(
                    200, content=_submit_body(12, status="ready")
                )
            )
            status = respx.post(STATUS)
            engine = make_async_engine()
            result = await engine.solve(adapter, challenge)
        assert result.task_id == 12
        assert status.call_count == 0

    @pytest.mark.asyncio
    async def test_429_exhaustion(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            create = respx.post(CREATE).mock(
                return_value=httpx.Response(429, content=b"x")
            )
            engine = make_async_engine()
            with pytest.raises(RateLimitError):
                await engine.solve(adapter, challenge)
        assert create.call_count == 3

    @pytest.mark.asyncio
    async def test_total_timeout(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit_body(13))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("processing"))
            )
            engine = make_async_engine()
            with pytest.raises(TaskTimeoutError):
                await engine.solve(adapter, challenge)

    @pytest.mark.asyncio
    async def test_external_cancellation_passes_through(
        self, adapter: ScriptedAdapter, challenge: ImageChallenge
    ) -> None:
        slow_time = TimeConfig(poll_delay=0.0, poll_interval=0.05, total_timeout=30.0)
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit_body(14))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status_body("processing"))
            )
            engine = AsyncTaskEngine(
                AsyncHttpTransport(), time=slow_time, retry=FAST_RETRY
            )
            task = asyncio.get_running_loop().create_task(
                engine.solve(adapter, challenge)
            )
            await asyncio.sleep(0.05)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
