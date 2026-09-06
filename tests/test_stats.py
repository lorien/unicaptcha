"""StatsCollector / UsageStats tests."""

from __future__ import annotations

import asyncio
import json
from datetime import timedelta

import httpx
import respx

from unicaptcha import (
    AsyncSolver,
    ImageChallenge,
    ProviderUsage,
    Solver,
    StatsCollector,
    UsageStats,
)
from unicaptcha.events import TaskEvent, TaskEventKind
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter
from unicaptcha.types import TimeConfig

URL = "https://example.com/login"
BASE = "https://api.2captcha.com"
CREATE = f"{BASE}/createTask"
POLL = f"{BASE}/getTaskResult"

FAST_TIME = TimeConfig(poll_delay=0.0, poll_interval=0.01, total_timeout=1.0)

_RECAPTCHA_HTML = (
    '<div class="g-recaptcha" data-sitekey="6Lc2wvkSAAAAAKGZfA8mF6J7kd5U3lGiPNvzY6j">'
    "</div>"
)


def _event(
    kind: TaskEventKind, provider: str = "twocaptcha", elapsed: float = 0.1
) -> TaskEvent:
    return TaskEvent(
        kind=kind,
        provider=provider,
        elapsed=timedelta(seconds=elapsed),
        attempt=1,
    )


class TestCollectorClassification:
    def test_terminal_kinds_count(self) -> None:
        collector = StatsCollector()
        collector.on_event(_event(TaskEventKind.RESULT_RECEIVED))
        collector.on_event(_event(TaskEventKind.SUBMIT_FAILED, elapsed=0.2))
        collector.on_event(_event(TaskEventKind.RESULT_FAILED, provider="cap"))
        collector.on_event(_event(TaskEventKind.PRE_FLIGHT_FAILED, provider="cap"))
        stats = collector.snapshot()
        assert stats.solved == 1
        assert stats.failed == 3
        assert stats.attempts == 4
        assert stats.elapsed == timedelta(seconds=0.5)
        assert stats.per_provider["twocaptcha"].solved == 1
        assert stats.per_provider["twocaptcha"].failed == 1
        assert stats.per_provider["cap"].solved == 0
        assert stats.per_provider["cap"].failed == 2

    def test_non_terminal_kinds_ignored(self) -> None:
        collector = StatsCollector()
        for kind in (
            TaskEventKind.SUBMIT_REQUESTED,
            TaskEventKind.SUBMIT_ACCEPTED,
            TaskEventKind.RESULT_REQUESTED,
        ):
            collector.on_event(_event(kind))
        assert collector.snapshot() == UsageStats(0, 0, timedelta(), {})

    def test_attempts_property(self) -> None:
        usage = ProviderUsage("p", solved=2, failed=3, elapsed=timedelta())
        assert usage.attempts == 5


def test_snapshot_is_immutable_copy() -> None:
    collector = StatsCollector()
    collector.on_event(_event(TaskEventKind.RESULT_RECEIVED))
    first = collector.snapshot()
    collector.on_event(_event(TaskEventKind.SUBMIT_FAILED))
    second = collector.snapshot()
    assert first.solved == 1 and second.solved == 1
    assert first.failed == 0 and second.failed == 1


def test_reset() -> None:
    collector = StatsCollector()
    collector.on_event(_event(TaskEventKind.RESULT_RECEIVED))
    collector.reset()
    assert collector.snapshot() == UsageStats(0, 0, timedelta(), {})


class TestEndToEnd:
    def _mock_solved(self) -> None:
        respx.post(CREATE).mock(
            return_value=httpx.Response(
                200,
                content=json.dumps({"errorId": 0, "taskId": 99}).encode(),
            )
        )
        respx.post(POLL).mock(
            return_value=httpx.Response(
                200,
                content=json.dumps(
                    {
                        "errorId": 0,
                        "status": "ready",
                        "solution": {"text": "hello"},
                    }
                ).encode(),
            )
        )

    @respx.mock
    def test_sync_solve_counts(self) -> None:
        self._mock_solved()
        collector = StatsCollector()
        with Solver(
            [TwoCaptchaAdapter("k")], time=FAST_TIME, on_event=collector.on_event
        ) as client:
            result = client.solve(ImageChallenge(b"hello"))
        assert result.solution.text == "hello"
        stats = collector.snapshot()
        assert stats.solved == 1
        assert stats.failed == 0
        assert stats.per_provider["twocaptcha"].solved == 1

    @respx.mock
    def test_async_solve_counts(self) -> None:
        self._mock_solved()
        collector = StatsCollector()

        async def run() -> None:
            async with AsyncSolver(
                [TwoCaptchaAdapter("k")], time=FAST_TIME, on_event=collector.on_event
            ) as client:
                await client.solve(ImageChallenge(b"hello"))

        asyncio.run(run())
        stats = collector.snapshot()
        assert stats.solved == 1
        assert stats.failed == 0

    @respx.mock
    def test_auto_solve_counts(self) -> None:
        self._mock_solved()
        collector = StatsCollector()
        with Solver(
            [TwoCaptchaAdapter("k")], time=FAST_TIME, on_event=collector.on_event
        ) as client:
            auto = client.auto_solve(_RECAPTCHA_HTML, URL)
        assert auto.detected.kind == "recaptcha-v2"
        assert collector.snapshot().solved == 1
