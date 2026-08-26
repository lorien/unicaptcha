import functools
import logging
from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from unicaptcha import ErrorKind, InvalidConfigError, TaskEvent, TaskEventKind
from unicaptcha._internal.handlers import check_sync_handler, emit_async, emit_sync

_TERMINAL_ERROR_KINDS = {
    TaskEventKind.PRE_FLIGHT_FAILED: frozenset(
        {
            None,
            ErrorKind.INVALID_CHALLENGE,
            ErrorKind.UNSUPPORTED_CHALLENGE,
            ErrorKind.INVALID_CONFIG,
            ErrorKind.CLIENT_CLOSED,
        }
    ),
    TaskEventKind.SUBMIT_FAILED: frozenset(
        {
            ErrorKind.NETWORK,
            ErrorKind.RATE_LIMIT,
            ErrorKind.SERVICE_BUSY,
            ErrorKind.AUTHENTICATION,
            ErrorKind.INSUFFICIENT_BALANCE,
            ErrorKind.PROVIDER,
            ErrorKind.CLIENT_CLOSED,
        }
    ),
    TaskEventKind.RESULT_FAILED: frozenset(
        {
            ErrorKind.NO_SOLUTION,
            ErrorKind.EMPTY_SOLUTION,
            ErrorKind.TASK_TIMEOUT,
            ErrorKind.PROVIDER,
            ErrorKind.CLIENT_CLOSED,
        }
    ),
}

_NON_FAILURE_KINDS = (
    TaskEventKind.SUBMIT_REQUESTED,
    TaskEventKind.SUBMIT_ACCEPTED,
    TaskEventKind.RESULT_REQUESTED,
    TaskEventKind.RESULT_RECEIVED,
)


def _event(**overrides: object) -> TaskEvent:
    values: dict[str, object] = {
        "kind": TaskEventKind.SUBMIT_REQUESTED,
        "provider": "twocaptcha",
        "elapsed": timedelta(seconds=1),
        "attempt": 1,
    }
    values.update(overrides)
    return TaskEvent(**values)  # type: ignore[arg-type]


class _Awaitable:
    """Object with __await__ for the awaitable-discard path (avoids the
    asyncio never-awaited RuntimeWarning of a real coroutine)."""

    def __await__(self) -> object:
        yield from ()
        return None


class TestTaskEventKind:
    def test_values_and_order(self) -> None:
        assert [k.value for k in TaskEventKind] == [
            "PRE_FLIGHT_FAILED",
            "SUBMIT_REQUESTED",
            "SUBMIT_ACCEPTED",
            "SUBMIT_FAILED",
            "RESULT_REQUESTED",
            "RESULT_RECEIVED",
            "RESULT_FAILED",
        ]


class TestTaskEvent:
    def test_fields_and_defaults(self) -> None:
        e = _event()
        assert e.kind is TaskEventKind.SUBMIT_REQUESTED
        assert e.task_id is None
        assert e.detail is None
        assert e.error_kind is None

    def test_full_fields(self) -> None:
        e = _event(
            kind=TaskEventKind.RESULT_FAILED,
            task_id=42,
            detail="provider anomaly",
            error_kind=ErrorKind.PROVIDER,
            attempt=3,
        )
        assert e.task_id == 42
        assert e.error_kind is ErrorKind.PROVIDER
        assert e.attempt == 3

    def test_frozen(self) -> None:
        e = _event()
        with pytest.raises(FrozenInstanceError):
            e.task_id = 1  # type: ignore[misc]


class TestErrorKindMatrix:
    def test_matrix_covers_exactly_the_terminal_failure_kinds(self) -> None:
        assert set(_TERMINAL_ERROR_KINDS) == {
            TaskEventKind.PRE_FLIGHT_FAILED,
            TaskEventKind.SUBMIT_FAILED,
            TaskEventKind.RESULT_FAILED,
        }

    def test_non_failure_kinds_carry_no_error_kind(self) -> None:
        for kind in _NON_FAILURE_KINDS:
            assert _event(kind=kind).error_kind is None


class TestCheckSyncHandler:
    def test_plain_handler_accepted(self) -> None:
        check_sync_handler(lambda e: None, what="Solver()")

    def test_none_accepted(self) -> None:
        check_sync_handler(None, what="Solver()")

    def test_coroutine_function_rejected(self) -> None:
        async def handler(event: TaskEvent) -> None:
            return None

        with pytest.raises(InvalidConfigError):
            check_sync_handler(handler, what="Solver()")

    def test_partial_wrapped_coroutine_function_rejected(self) -> None:
        async def handler(event: TaskEvent, *, extra: str) -> None:
            return None

        with pytest.raises(InvalidConfigError):
            check_sync_handler(functools.partial(handler, extra="x"), what="Solver()")


class TestEmitSync:
    def test_calls_handler(self) -> None:
        seen: list[TaskEvent] = []
        emit_sync(seen.append, _event())
        assert len(seen) == 1

    def test_none_noop(self) -> None:
        emit_sync(None, _event())

    def test_awaitable_result_discarded_with_warning(self, caplog: object) -> None:
        def pathological(event: TaskEvent) -> object:
            return _Awaitable()

        with caplog.at_level(logging.WARNING, logger="unicaptcha"):
            emit_sync(pathological, _event())
        assert "awaitable" in caplog.text  # type: ignore[attr-defined]

    def test_handler_error_propagates(self) -> None:
        def handler(event: TaskEvent) -> None:
            raise ValueError("boom")

        with pytest.raises(ValueError):
            emit_sync(handler, _event())


class TestEmitAsync:
    @pytest.mark.asyncio
    async def test_awaits_awaitable_handler(self) -> None:
        seen: list[TaskEvent] = []

        async def handler(event: TaskEvent) -> None:
            seen.append(event)

        await emit_async(handler, _event())
        assert len(seen) == 1

    @pytest.mark.asyncio
    async def test_calls_plain_handler(self) -> None:
        seen: list[TaskEvent] = []

        def handler(event: TaskEvent) -> None:
            seen.append(event)

        await emit_async(handler, _event())
        assert len(seen) == 1

    @pytest.mark.asyncio
    async def test_none_noop(self) -> None:
        await emit_async(None, _event())

    @pytest.mark.asyncio
    async def test_handler_error_propagates(self) -> None:
        async def handler(event: TaskEvent) -> None:
            raise ValueError("boom")

        with pytest.raises(ValueError):
            await emit_async(handler, _event())
