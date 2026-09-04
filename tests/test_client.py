"""Solver / AsyncSolver tests: registration, dispatch, operations."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

import httpx
import pytest
import respx
from _fake import FakeSolution

from unicaptcha import (
    AsyncSolver,
    ClientClosedError,
    ImageChallenge,
    Proxy,
    RecaptchaV2Challenge,
    RetryConfig,
    Solver,
    TaskEventKind,
    TaskRef,
    TaskStatus,
    TimeConfig,
    UnsupportedChallengeError,
)
from unicaptcha._internal import routing
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import ErrorKind, InvalidConfigError
from unicaptcha.types import ParsedTask, SubmitAccepted

FAST_TIME = TimeConfig(poll_delay=0.0, poll_interval=0.01, total_timeout=0.5)
FAST_RETRY = RetryConfig(max_attempts=3, backoff_base=0.001, backoff_cap=0.001)


def _body(data: dict[str, Any]) -> bytes:
    return json.dumps(data).encode()


# -- concrete challenges + adapters ---------------------------------------


class AlphaChallenge(ImageChallenge):
    pass


class BetaChallenge(ImageChallenge):
    pass


class LoneChallenge(ImageChallenge):
    pass


class EchoAdapter(BaseAdapter):
    """JSON-family test adapter driven by respx response sequences."""

    provider = "scripted"
    challenges: frozenset[type[BaseChallenge]] = frozenset()
    default_base_url = "https://scripted.example"

    def build_payload(self, challenge: BaseChallenge) -> dict[str, object]:
        payload: dict[str, object] = {
            "clientKey": self._api_key.get_secret_value(),
            "kind": type(challenge).__name__,
        }
        sitekey = getattr(challenge, "sitekey", None)
        if sitekey is not None:
            payload["sitekey"] = sitekey
        proxy = getattr(challenge, "proxy", None)
        if proxy is not None:
            payload["via"] = f"{proxy.host}:{proxy.port}"
        task_id = getattr(challenge, "task_ref", None)
        if task_id is not None:
            payload["ref"] = str(task_id)
        return payload

    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        data = json.loads(raw)
        instant = None
        if data.get("status") == "ready":
            instant = ParsedTask(
                state=TaskStatus.READY,
                solution=FakeSolution(),
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
                solution=FakeSolution(),
                cost=Decimal("0.001"),
                raw=raw,
            )
        if status == "unsolvable":
            return ParsedTask(
                state=TaskStatus.NO_SOLUTION, solution=None, cost=None, raw=raw
            )
        return ParsedTask(state=TaskStatus.PENDING, solution=None, cost=None, raw=raw)

    def parse_balance(self, raw: bytes) -> Decimal:
        return Decimal(str(json.loads(raw)["balance"]))

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        code = json.loads(raw).get("errorCode", "")
        return ErrorKind.PROVIDER, code


class AlphaAdapter(EchoAdapter):
    provider = "alpha"
    challenges: frozenset[type[BaseChallenge]] = frozenset({AlphaChallenge})
    default_base_url = "https://alpha.example"


class BetaAdapter(EchoAdapter):
    provider = "beta"
    challenges: frozenset[type[BaseChallenge]] = frozenset({BetaChallenge})
    default_base_url = "https://beta.example"


@pytest.fixture
def solver() -> Solver:
    return Solver(
        [AlphaAdapter("k1"), BetaAdapter("k2")],
        time=FAST_TIME,
        retry=FAST_RETRY,
    )


@pytest.fixture
def async_solver() -> AsyncSolver:
    return AsyncSolver(
        [AlphaAdapter("k1"), BetaAdapter("k2")],
        time=FAST_TIME,
        retry=FAST_RETRY,
    )


class TestRegistration:
    def test_non_adapter_rejected(self) -> None:
        with pytest.raises(TypeError):
            Solver(["not-an-adapter"])  # type: ignore[list-item]

    def test_duplicate_provider_rejected(self) -> None:
        with pytest.raises(ValueError, match="registered twice"):
            Solver([AlphaAdapter("a"), AlphaAdapter("b")])

    def test_empty_adapters_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            Solver([])

    def test_sync_coroutine_handler_rejected(self) -> None:
        async def handler(event: object) -> None:
            return None

        with pytest.raises(InvalidConfigError):
            Solver([AlphaAdapter("a")], on_event=handler)  # type: ignore[arg-type]

    def test_default_registry_limit_is_1000_and_none_unbounded(self) -> None:
        # Indirect visibility: solves + abandonment survive far past cap only
        # when explicitly unbounded. Here we just ensure the default path
        # constructs (covered functionally elsewhere); signature check:
        import inspect

        sig = inspect.signature(Solver.__init__)
        assert sig.parameters["abandoned_registry_limit"].default == 1000


class TestDispatch:
    def test_concrete_class_dispatch(self, solver: Solver) -> None:
        with respx.mock:
            respx.post(f"{AlphaAdapter.default_base_url}/createTask").mock(
                return_value=httpx.Response(200, content=_submit_body(1))
            )
            respx.post(f"{AlphaAdapter.default_base_url}/getTaskResult").mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            result = solver.solve(AlphaChallenge(b"x"))
        assert result.provider == "alpha"

    def test_kind_base_with_provider_name(self, solver: Solver) -> None:
        with respx.mock:
            respx.post(f"{BetaAdapter.default_base_url}/createTask").mock(
                return_value=httpx.Response(200, content=_submit_body(2))
            )
            respx.post(f"{BetaAdapter.default_base_url}/getTaskResult").mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            result = solver.solve(ImageChallenge(b"q"), provider="beta")
        assert result.provider == "beta"

    def test_unknown_provider_name_type_error(self, solver: Solver) -> None:
        events = []
        with pytest.raises(TypeError, match="'nope'"):
            solver.solve(ImageChallenge(b"q"), provider="nope", on_event=events.append)
        kinds = [(e.kind, e.provider, e.error_kind) for e in events]
        assert kinds == [
            (
                TaskEventKind.PRE_FLIGHT_FAILED,
                "nope",
                None,
            )
        ]

    def test_mismatched_provider_names_both_parties(self, solver: Solver) -> None:
        events = []
        with pytest.raises(TypeError) as excinfo:
            solver.solve(AlphaChallenge(b"x"), provider="beta", on_event=events.append)
        assert "'alpha'" in str(excinfo.value)
        assert "'beta'" in str(excinfo.value)
        assert events[0].provider == "alpha"

    def test_unmatched_concrete_challenge_no_event(self, solver: Solver) -> None:
        events = []
        with pytest.raises(TypeError):
            solver.solve(LoneChallenge(b"x"), on_event=events.append)
        assert events == []

    def test_random_pick_pinned(
        self, solver: Solver, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(routing, "uniform_choice", lambda cands: cands[-1])
        with respx.mock:
            respx.post(f"{BetaAdapter.default_base_url}/createTask").mock(
                return_value=httpx.Response(200, content=_submit_body(3))
            )
            respx.post(f"{BetaAdapter.default_base_url}/getTaskResult").mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            result = solver.solve(ImageChallenge(b"q"))
        assert result.provider == "beta"

    def test_upcast_carries_universal_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: list[dict[str, object]] = []

        class SubRecV2(RecaptchaV2Challenge):
            pass

        class UpcastAdapter(EchoAdapter):
            provider = "up"
            challenges: frozenset[type[BaseChallenge]] = frozenset({SubRecV2})
            default_base_url = "https://up.example"

        original = EchoAdapter.build_payload

        def capturing(self: BaseAdapter, challenge: BaseChallenge) -> dict[str, object]:
            payload = original(self, challenge)
            captured.append(payload)
            return payload

        monkeypatch.setattr(EchoAdapter, "build_payload", capturing)
        solver = Solver([UpcastAdapter("k")], time=FAST_TIME, retry=FAST_RETRY)
        with respx.mock:
            respx.post(f"{UpcastAdapter.default_base_url}/createTask").mock(
                return_value=httpx.Response(200, content=_submit_body(4))
            )
            respx.post(f"{UpcastAdapter.default_base_url}/getTaskResult").mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            result = solver.solve(RecaptchaV2Challenge(sitekey="SK", pageurl="PU"))
        assert captured and captured[0]["sitekey"] == "SK"
        # upcast happened: the concrete subclass was constructed
        assert captured[0]["kind"] == "SubRecV2"
        assert isinstance(result.solution, FakeSolution)

    def test_client_default_proxy_ignored_when_field_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen_proxy: list[object] = []

        def capturing(self: EchoAdapter, challenge: BaseChallenge) -> dict[str, object]:
            seen_proxy.append(getattr(challenge, "proxy", None))
            return {"clientKey": "k"}

        monkeypatch.setattr(EchoAdapter, "build_payload", capturing)
        solver = Solver(
            [AlphaAdapter("k")],
            proxy=Proxy(host="127.0.0.1", port=9),
            time=FAST_TIME,
            retry=FAST_RETRY,
        )
        with respx.mock:
            respx.post(f"{AlphaAdapter.default_base_url}/createTask").mock(
                return_value=httpx.Response(200, content=_submit_body(7))
            )
            respx.post(f"{AlphaAdapter.default_base_url}/getTaskResult").mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            solver.solve(AlphaChallenge(b"z"))
        assert seen_proxy == [None]


def _submit_body(task_id: int) -> bytes:
    return json.dumps({"errorId": 0, "taskId": task_id}).encode()


def _status_body(status: str) -> bytes:
    return json.dumps({"errorId": 0, "status": status}).encode()


def _mock_happy(base_url: str, task_id: int = 1) -> None:
    respx.post(f"{base_url}/createTask").mock(
        return_value=httpx.Response(200, content=_submit_body(task_id))
    )
    respx.post(f"{base_url}/getTaskResult").mock(
        return_value=httpx.Response(200, content=_status_body("ready"))
    )


class TestPreFlightEmission:
    def test_unsupported_kind_with_provider_emits_event(self) -> None:
        events = []
        with respx.mock, pytest.raises(UnsupportedChallengeError):
            make_solver().solve(
                RecaptchaV2Challenge(sitekey="s", pageurl="p"),
                provider="alpha",
                on_event=events.append,
            )
        assert len(events) == 1
        assert events[0].kind is TaskEventKind.PRE_FLIGHT_FAILED
        assert events[0].provider == "alpha"
        assert events[0].error_kind is ErrorKind.UNSUPPORTED_CHALLENGE


class TestProxyDefault:
    def test_ignored_with_warning_when_field_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        seen: list[object] = []
        original = EchoAdapter.build_payload

        def capturing(self: EchoAdapter, challenge: BaseChallenge) -> dict[str, object]:
            seen.append(getattr(challenge, "proxy", None))
            return original(self, challenge)

        monkeypatch.setattr(EchoAdapter, "build_payload", capturing)
        solver = Solver(
            [AlphaAdapter("k")],
            proxy=Proxy(host="10.0.0.1", port=8080),
            time=FAST_TIME,
            retry=FAST_RETRY,
        )
        with respx.mock, caplog.at_level(logging.WARNING, logger="unicaptcha"):
            _mock_happy(f"{AlphaAdapter.default_base_url}", 8)
            solver.solve(AlphaChallenge(b"z"))
        assert seen == [None]
        assert any("default proxy ignored" in r.message for r in caplog.records)


def make_solver() -> Solver:
    return Solver(
        [AlphaAdapter("k1"), BetaAdapter("k2")], time=FAST_TIME, retry=FAST_RETRY
    )


class TestSyncLifecycle:
    def test_context_manager_closes(self) -> None:
        with Solver([AlphaAdapter("a")]) as solver:
            assert not solver._closed
        assert solver._closed
        with pytest.raises(ClientClosedError):
            solver.get_balance("alpha")

    def test_get_abandoned_tasks_readable_after_close(self) -> None:
        solver = Solver([AlphaAdapter("a")])
        solver.close()
        assert solver.get_abandoned_tasks() == ()


class TestAsyncTier:
    @pytest.mark.asyncio
    async def test_solve_and_wait_two_phase(self) -> None:
        async_solver = AsyncSolver(
            [AlphaAdapter("k")], time=FAST_TIME, retry=FAST_RETRY
        )
        challenge = AlphaChallenge(b"q")
        with respx.mock:
            respx.post(f"{AlphaAdapter.default_base_url}/createTask").mock(
                return_value=httpx.Response(200, content=_submit_body(71))
            )
            respx.post(f"{AlphaAdapter.default_base_url}/getTaskResult").mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            ticket = await async_solver.submit(challenge)
            result = await async_solver.wait(ticket)
        assert result.task_id == 71

    @pytest.mark.asyncio
    async def test_wait_ref_ready(self) -> None:
        ref = TaskRef("alpha", 72)
        async_solver = AsyncSolver(
            [AlphaAdapter("k")], time=FAST_TIME, retry=FAST_RETRY
        )
        with respx.mock:
            respx.post(f"{AlphaAdapter.default_base_url}/getTaskResult").mock(
                return_value=httpx.Response(200, content=_status_body("ready"))
            )
            status = await async_solver.wait_ref(ref, timeout=0.5)
        assert status.status is TaskStatus.READY

    @pytest.mark.asyncio
    async def test_report_bad_default_unsupported(self) -> None:
        ref = TaskRef("alpha", 73)
        async_solver = AsyncSolver([AlphaAdapter("k")])
        with pytest.raises(UnsupportedChallengeError):
            await async_solver.report_bad_result(ref)

    @pytest.mark.asyncio
    async def test_aclose_then_use_raises(self) -> None:
        async_solver = AsyncSolver([AlphaAdapter("k")])
        await async_solver.aclose()
        await async_solver.aclose()
        with pytest.raises(ClientClosedError):
            await async_solver.solve(ImageChallenge(b"x"))

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        async with AsyncSolver([AlphaAdapter("k")]) as solver:
            assert not solver._closed
        assert solver._closed
