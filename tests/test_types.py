from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from _fake import FakeSolution

from unicaptcha import TaskRef, TaskResult, TaskStatus, TaskStatusResult
from unicaptcha.types import ParsedTask, SubmitAccepted, TaskTicket


def _result(*, raw: bytes = b'{"status":"ready"}') -> TaskResult[FakeSolution]:
    return TaskResult(
        solution=FakeSolution(),
        task_id=12345,
        cost=Decimal("0.00095"),
        raw=raw,
        provider="twocaptcha",
        created_at=datetime(2026, 8, 26, 12, 0, 0, tzinfo=UTC),
        elapsed=timedelta(seconds=8.5),
    )


class TestTaskRef:
    def test_constructible_and_frozen(self) -> None:
        ref = TaskRef("twocaptcha", 12345)
        assert ref.provider == "twocaptcha"
        assert ref.task_id == 12345
        with pytest.raises(FrozenInstanceError):
            ref.task_id = 1  # type: ignore[misc]

    def test_equality(self) -> None:
        assert TaskRef("twocaptcha", 1) == TaskRef("twocaptcha", 1)
        assert TaskRef("twocaptcha", 1) != TaskRef("anticaptcha", 1)


class TestTaskResult:
    def test_fields_and_task_ref(self) -> None:
        r = _result()
        assert r.solution == FakeSolution()
        assert r.task_id == 12345
        assert r.cost == Decimal("0.00095")
        assert r.raw == b'{"status":"ready"}'
        assert r.provider == "twocaptcha"
        assert r.created_at.tzinfo is not None
        assert r.task_ref == TaskRef("twocaptcha", 12345)

    def test_repr_stubs_bytes(self) -> None:
        r = _result()
        assert "<18 bytes>" in repr(r)
        assert r.raw.decode() not in repr(r)

    def test_str_mirrors_repr(self) -> None:
        assert str(_result()) == repr(_result())


class TestTaskStatusResult:
    def test_fields(self) -> None:
        s = TaskStatusResult(
            task_id=12345,
            provider="twocaptcha",
            status=TaskStatus.PENDING,
            solution=None,
            cost=None,
            raw=b'{"status":"processing"}',
        )
        assert s.status is TaskStatus.PENDING
        assert s.solution is None

    def test_ready_carries_solution(self) -> None:
        s = TaskStatusResult(
            task_id=1,
            provider="twocaptcha",
            status=TaskStatus.READY,
            solution=FakeSolution(),
            cost=Decimal("0.001"),
            raw=b'{"status":"ready"}',
        )
        assert isinstance(s.solution, FakeSolution)

    def test_enum_values(self) -> None:
        assert [e.value for e in TaskStatus] == [
            "PENDING",
            "READY",
            "NO_SOLUTION",
            "UNKNOWN",
        ]

    def test_repr_stubs_bytes(self) -> None:
        s = TaskStatusResult(
            task_id=1,
            provider="twocaptcha",
            status=TaskStatus.UNKNOWN,
            solution=None,
            cost=None,
            raw=b'{"error":"not found"}',
        )
        assert "<21 bytes>" in repr(s)
        assert "not found" not in repr(s)


class TestTaskTicket:
    def test_fields_and_defaults(self) -> None:
        ref = TaskRef("capsolver", 7)
        t = TaskTicket(
            task_ref=ref,
            submitted_at=datetime(2026, 8, 26, 12, 0, 0, tzinfo=UTC),
        )
        assert t.task_ref == ref
        assert t.instant_answer is None
        assert t.time is None

    def test_instant_answer(self) -> None:
        parsed = ParsedTask(
            state=TaskStatus.READY,
            solution=FakeSolution(),
            cost=Decimal("0.001"),
            raw=b'{"status":"ready"}',
        )
        t = TaskTicket(
            task_ref=TaskRef("capsolver", 7),
            submitted_at=datetime(2026, 8, 26, 12, 0, 0, tzinfo=UTC),
            instant_answer=parsed,
        )
        assert t.instant_answer is parsed


class TestParsedTaskAndSubmitAccepted:
    def test_parsed_task_fields_and_repr(self) -> None:
        p = ParsedTask(
            state=TaskStatus.READY,
            solution=FakeSolution(),
            cost=None,
            raw=b"body",
        )
        assert p.detail is None
        assert "<4 bytes>" in repr(p)
        assert "body" not in repr(p)

    def test_submit_accepted_defaults(self) -> None:
        s = SubmitAccepted(task_id=42)
        assert s.instant_answer is None

    def test_submit_accepted_with_instant_answer(self) -> None:
        p = ParsedTask(
            state=TaskStatus.READY,
            solution=FakeSolution(),
            cost=Decimal("0.001"),
            raw=b"body",
        )
        s = SubmitAccepted(task_id=42, instant_answer=p)
        assert s.instant_answer is p
