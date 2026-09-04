"""Deterministic engine timing tests via the injectable clock/sleep seam
(task 16, ADR-0033 / architecture.md §10).

A ``FakeClock`` advances time instantly, so backoff, poll cadence, and
timeout budgets are asserted against exact fake-clock state rather than
wall-clock sleep. Both sync (``TaskEngine``) and async (``AsyncTaskEngine``)
tiers are exercised.
"""

from __future__ import annotations

import asyncio
import json
import threading
from decimal import Decimal

import httpx
import pytest
import respx
from _fake import FakeAsyncSleep, FakeClock, FakeSolution

from unicaptcha import (
    ClientClosedError,
    NetworkError,
    NoSolutionError,
    ProviderError,
    RateLimitError,
    RetryConfig,
    ServiceBusyError,
    TaskStatus,
    TaskTimeoutError,
    TimeConfig,
)
from unicaptcha._internal.async_engine import AsyncTaskEngine
from unicaptcha._internal.backoff import backoff_sleep
from unicaptcha._internal.engine import TaskEngine
from unicaptcha._internal.errors import error_from_kind
from unicaptcha._internal.http import AsyncHttpTransport, HttpTransport
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge import (
    FunCaptchaChallenge,
    GeeTestV4Challenge,
    RecaptchaV2Challenge,
    TextChallenge,
    TurnstileChallenge,
)
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.challenge.image import ImageChallenge
from unicaptcha.errors import ErrorKind
from unicaptcha.types import ParsedTask, SubmitAccepted, TaskRef

BASE = "https://timing.example"
CREATE = f"{BASE}/createTask"
STATUS = f"{BASE}/getTaskResult"


class TimingAdapter(BaseAdapter):
    """Adapter with **no** ``default_task_config``: per-kind timing comes
    from the built-in ADR-0030 table. Accepts every challenge kind and is
    respx-scripted per test."""

    provider = "timing"
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
        return ParsedTask(state=TaskStatus.PENDING, solution=None, cost=None, raw=raw)

    def parse_balance(self, raw: bytes) -> Decimal:
        return Decimal("0.00")

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        code = json.loads(raw).get("errorCode", "")
        if code == "ERROR_TOO_MANY_REQUESTS":
            return ErrorKind.RATE_LIMIT, "too many requests"
        if code == "ERROR_NO_SLOT_AVAILABLE":
            return ErrorKind.SERVICE_BUSY, "no slot"
        return ErrorKind.PROVIDER, code

    def report_bad_supported(self, challenge_type: type[BaseChallenge]) -> bool:
        return True

    def build_report_bad(self, task: TaskRef) -> dict[str, object]:
        return {"taskId": task.task_id}

    def parse_report_bad(self, raw: bytes) -> bool:
        return json.loads(raw)["status"] == "success"


def _submit(task_id: int = 100) -> bytes:
    return json.dumps({"errorId": 0, "taskId": task_id}).encode()


def _status(status: str) -> bytes:
    return json.dumps({"errorId": 0, "status": status}).encode()


@pytest.fixture
def adapter() -> TimingAdapter:
    return TimingAdapter("test-key")


@pytest.fixture
def challenge() -> ImageChallenge:
    return ImageChallenge(b"png-bytes")


def make_engine(
    clock: FakeClock,
    *,
    time: TimeConfig | None = None,
    retry=None,
) -> TaskEngine:
    return TaskEngine(
        HttpTransport(),
        shutdown=threading.Event(),
        time=time,
        retry=retry,
        clock=clock,
    )


def make_async_engine(
    clock: FakeClock,
    *,
    time: TimeConfig | None = None,
    retry=None,
) -> AsyncTaskEngine:
    return AsyncTaskEngine(
        AsyncHttpTransport(),
        time=time,
        retry=retry,
        clock=clock,
        sleep=FakeAsyncSleep(clock),
    )


# -- backoff math -------------------------------------------------------


class TestBackoffMath:
    def test_full_jitter_bounds(self) -> None:
        for attempt, lo, hi in ((0, 0.0, 1.0), (1, 0.0, 2.0), (2, 0.0, 4.0)):
            for _ in range(100):
                val = backoff_sleep(attempt, base=1.0, cap=30.0)
                assert lo <= val <= hi

    def test_cap_is_respected(self) -> None:
        for attempt in (4, 5, 10):
            for _ in range(200):
                assert 0.0 <= backoff_sleep(attempt, base=1.0, cap=30.0) <= 30.0


# -- total-budget semantics ---------------------------------------------


class TestTotalBudget:
    def test_submit_backoff_and_poll_fit_in_budget(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            create = respx.post(CREATE).mock(
                side_effect=[
                    httpx.Response(500, content=b"boom"),
                    httpx.Response(200, content=_submit(1)),
                ]
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("ready"))
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=30.0, poll_interval=1.0, poll_delay=1.0),
                retry=RetryConfig(max_attempts=3, backoff_base=1.0, backoff_cap=1.0),
            )
            result = engine.solve(adapter, challenge)
        assert result.task_id == 1
        assert create.call_count == 2
        assert clock.sleep_total <= 30.0

    @pytest.mark.asyncio
    async def test_async_backoff_and_poll_fit_in_budget(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            create = respx.post(CREATE).mock(
                side_effect=[
                    httpx.Response(500, content=b"boom"),
                    httpx.Response(200, content=_submit(13)),
                ]
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("ready"))
            )
            engine = make_async_engine(
                clock,
                time=TimeConfig(total_timeout=30.0, poll_interval=1.0, poll_delay=1.0),
                retry=RetryConfig(max_attempts=3, backoff_base=1.0, backoff_cap=1.0),
            )
            result = await engine.solve(adapter, challenge)
        assert result.task_id == 13
        assert create.call_count == 2
        assert clock.sleep_total <= 30.0

    def test_task_timeout_on_exhaustion(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(2))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("processing"))
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=5.0, poll_interval=1.0, poll_delay=0.0),
            )
            with pytest.raises(TaskTimeoutError):
                engine.solve(adapter, challenge)
        assert clock.sleep_total >= 5.0

    def test_per_kind_default_rows(self, adapter: TimingAdapter) -> None:
        cases = {
            ImageChallenge(b"png"): (30.0, 2.0, 5.0),
            TextChallenge("If tomorrow is Saturday, what day is today?"): (
                120.0,
                2.0,
                5.0,
            ),
            RecaptchaV2Challenge(sitekey="k", pageurl="https://x"): (
                120.0,
                5.0,
                15.0,
            ),
            FunCaptchaChallenge(public_key="k", pageurl="https://x"): (
                180.0,
                3.0,
                10.0,
            ),
            GeeTestV4Challenge(captcha_id="k", pageurl="https://x"): (
                180.0,
                3.0,
                10.0,
            ),
            TurnstileChallenge(sitekey="k", pageurl="https://x"): (
                120.0,
                3.0,
                5.0,
            ),
        }
        clock = FakeClock()
        engine = make_engine(clock)  # no client time -> kind defaults
        for ch, (total, interval, delay) in cases.items():
            with respx.mock:
                respx.post(CREATE).mock(
                    return_value=httpx.Response(200, content=_submit(10))
                )
                ticket = engine.submit(adapter, ch)
            assert ticket.time is not None
            assert ticket.time.total_timeout == total
            assert ticket.time.poll_interval == interval
            assert ticket.time.poll_delay == delay


# -- retry / backoff -----------------------------------------------------


class TestRetryBackoff:
    def test_attempt_cap_three(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        body = json.dumps({"errorId": 1, "errorCode": "ERROR_UNKNOWN"}).encode()
        with respx.mock:
            create = respx.post(CREATE).mock(
                return_value=httpx.Response(500, content=body)
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("processing"))
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=60.0, poll_interval=1.0, poll_delay=0.0),
                retry=RetryConfig(max_attempts=3, backoff_base=1.0, backoff_cap=10.0),
            )
            with pytest.raises(ProviderError):
                engine.solve(adapter, challenge)
        assert create.call_count == 3

    def test_429_retries_then_rate_limit(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            create = respx.post(CREATE).mock(
                return_value=httpx.Response(429, content=b"slow")
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=60.0, poll_interval=1.0, poll_delay=0.0),
                retry=RetryConfig(max_attempts=3, backoff_base=1.0, backoff_cap=10.0),
            )
            with pytest.raises(RateLimitError):
                engine.solve(adapter, challenge)
        assert create.call_count == 3

    def test_busy_payload_service_busy(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        body = json.dumps(
            {"errorId": 1, "errorCode": "ERROR_NO_SLOT_AVAILABLE"}
        ).encode()
        clock = FakeClock()
        with respx.mock:
            create = respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=body)
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=60.0, poll_interval=1.0, poll_delay=0.0),
                retry=RetryConfig(max_attempts=3, backoff_base=1.0, backoff_cap=10.0),
            )
            with pytest.raises(ServiceBusyError):
                engine.solve(adapter, challenge)
        assert create.call_count == 3

    @pytest.mark.parametrize("status", [502, 504])
    def test_gateway_fails_fast(
        self, adapter: TimingAdapter, challenge: ImageChallenge, status: int
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            create = respx.post(CREATE).mock(
                return_value=httpx.Response(status, content=b"gw")
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=60.0, poll_interval=1.0, poll_delay=0.0),
                retry=RetryConfig(max_attempts=3, backoff_base=1.0, backoff_cap=10.0),
            )
            with pytest.raises(NetworkError):
                engine.solve(adapter, challenge)
        assert create.call_count == 1


# -- poll cadence --------------------------------------------------------


class TestPollCadence:
    def test_fresh_ticket_applies_poll_delay(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(3))
            )
            respx.post(STATUS).mock(
                side_effect=[
                    httpx.Response(200, content=_status("processing")),
                    httpx.Response(200, content=_status("ready")),
                ]
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=30.0, poll_interval=3.0, poll_delay=2.0),
            )
            engine.solve(adapter, challenge)
        # poll_delay (2.0) + one poll_interval (3.0) before READY
        assert clock.sleep_total == pytest.approx(5.0, abs=0.11)

    def test_stale_ticket_skips_poll_delay(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(4))
            )
            status = respx.post(STATUS).mock(
                side_effect=[
                    httpx.Response(200, content=_status("processing")),
                    httpx.Response(200, content=_status("ready")),
                ]
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=30.0, poll_interval=3.0, poll_delay=2.0),
            )
            ticket = engine.submit(adapter, challenge)
            clock.advance(10.0)  # age > poll_interval -> stale
            engine.wait(adapter, ticket)
        assert status.call_count == 2
        assert clock.sleep_total == pytest.approx(3.0, abs=0.11)  # no poll_delay

    def test_wait_ref_skips_poll_delay(self, adapter: TimingAdapter) -> None:
        clock = FakeClock()
        with respx.mock:
            status = respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("ready"))
            )
            engine = make_engine(clock)
            engine.wait_ref(adapter, TaskRef("timing", 5), timeout=30.0)
        assert status.call_count == 1
        assert clock.sleep_calls == []  # immediate, no delay

    def test_poll_interval_cadence(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(6))
            )
            respx.post(STATUS).mock(
                side_effect=[
                    httpx.Response(200, content=_status("processing")),
                    httpx.Response(200, content=_status("processing")),
                    httpx.Response(200, content=_status("ready")),
                ]
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=30.0, poll_interval=2.0, poll_delay=0.0),
            )
            engine.solve(adapter, challenge)
        # two poll_interval sleeps before the third (READY) poll
        assert clock.sleep_total == pytest.approx(4.0, abs=0.11)


# -- cancellation / lifecycle --------------------------------------------


class TestCancellationLifecycle:
    def test_no_solution_raises(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(7))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("unsolvable"))
            )
            engine = make_engine(clock)
            with pytest.raises(NoSolutionError):
                engine.solve(adapter, challenge)

    def test_two_phase_submit_wait(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(8))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("ready"))
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=30.0, poll_interval=1.0, poll_delay=0.0),
            )
            ticket = engine.submit(adapter, challenge)
            result = engine.wait(adapter, ticket)
        assert result.task_id == 8
        assert clock.sleep_total == 0.0  # READY on first poll, no delay

    def test_instant_answer_fast_path(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        body = json.dumps({"errorId": 0, "taskId": 9, "status": "ready"}).encode()
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(return_value=httpx.Response(200, content=body))
            status = respx.post(STATUS)
            engine = make_engine(clock)
            result = engine.solve(adapter, challenge)
        assert result.task_id == 9
        assert status.call_count == 0
        assert clock.sleep_calls == []

    def test_use_after_close_raises(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(10))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("processing"))
            )
            engine = make_engine(
                clock,
                time=TimeConfig(total_timeout=30.0, poll_interval=0.2, poll_delay=0.0),
            )
            engine.close()
            with pytest.raises(ClientClosedError):
                engine.solve(adapter, challenge)

    @pytest.mark.asyncio
    async def test_async_cancellation_eventless(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(11))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("processing"))
            )
            engine = make_async_engine(
                clock,
                time=TimeConfig(
                    total_timeout=10000.0, poll_interval=0.01, poll_delay=0.0
                ),
            )
            task = asyncio.get_running_loop().create_task(
                engine.solve(adapter, challenge)
            )
            await asyncio.sleep(0.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    @pytest.mark.asyncio
    async def test_async_task_timeout(
        self, adapter: TimingAdapter, challenge: ImageChallenge
    ) -> None:
        clock = FakeClock()
        with respx.mock:
            respx.post(CREATE).mock(
                return_value=httpx.Response(200, content=_submit(12))
            )
            respx.post(STATUS).mock(
                return_value=httpx.Response(200, content=_status("processing"))
            )
            engine = make_async_engine(
                clock,
                time=TimeConfig(total_timeout=30.0, poll_interval=1.0, poll_delay=0.0),
            )
            with pytest.raises(TaskTimeoutError):
                await engine.solve(adapter, challenge)
        assert clock.sleep_total == 30.0
