"""Shared test fakes. Not collected by pytest (filename not test_*)."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar

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
