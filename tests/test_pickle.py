import pickle
from datetime import UTC, datetime
from decimal import Decimal

from _fake import FakeSolution

from unicaptcha import (
    TaskRef,
    TaskResult,
    TaskStatus,
    TaskStatusResult,
    TaskTicket,
)


class TestPickleRoundTrips:
    def test_taskref(self) -> None:
        ref = TaskRef("twocaptcha", 12345)
        assert pickle.loads(pickle.dumps(ref)) == ref

    def test_ticket(self) -> None:
        t = TaskTicket(
            task_ref=TaskRef("twocaptcha", 12345),
            submitted_at=datetime(2026, 8, 26, 12, 0, 0, tzinfo=UTC),
        )
        restored = pickle.loads(pickle.dumps(t))
        assert restored == t
        assert restored.task_ref == t.task_ref

    def test_result(self) -> None:
        r = TaskResult(
            solution=FakeSolution(),
            task_id=1,
            cost=Decimal("0.001"),
            raw=b"body",
            provider="twocaptcha",
            created_at=datetime(2026, 8, 26, 12, 0, 0, tzinfo=UTC),
            elapsed=datetime(2026, 8, 26, 12, 0, 8, tzinfo=UTC)
            - datetime(2026, 8, 26, 12, 0, 0, tzinfo=UTC),
        )
        restored = pickle.loads(pickle.dumps(r))
        assert restored == r

    def test_status_result(self) -> None:
        s = TaskStatusResult(
            task_id=1,
            provider="twocaptcha",
            status=TaskStatus.PENDING,
            solution=None,
            cost=None,
            raw=b"body",
        )
        assert pickle.loads(pickle.dumps(s)) == s
