"""The public adapter SDK contract (ADR-0041, ADR-0053).

``BaseAdapter`` is the abstract base class every shipped and third-party
adapter implements; ``Endpoints`` declares the request paths an adapter
uses (ADR-0073). This module is part of the public surface and never
imports ``unicaptcha._internal``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import ErrorKind, UnsupportedChallengeError
from unicaptcha.types import (
    ParsedTask,
    SecretStr,
    SubmitAccepted,
    TaskRef,
    TimeConfig,
)


@dataclass(frozen=True, slots=True)
class Endpoints:
    """Operation-keyed request paths (ADR-0073).

    All fields are required: an adapter either inherits the JSON-family
    default on ``BaseAdapter.endpoints`` or declares a complete set — no
    per-field merging.
    """

    submit: str
    get_task_status: str
    get_balance: str
    report_good_result: str
    report_bad_result: str


class BaseAdapter(ABC):
    """The adapter SDK contract.

    Adapters are pure translators: they build request payloads, parse
    provider responses, and map provider errors into the library hierarchy.
    Required declarations (``provider``, ``challenges``, ``default_base_url``)
    are enforced at subclass creation.

    The concrete constructor wraps a plain ``str`` api_key into
    ``SecretStr`` (ADR-0063), defaults ``base_url`` to
    ``default_base_url``, and stores the trinary ``referral`` flag
    (ADR-0072) — the base embeds nothing; shipped adapters serialize their
    provider's affiliate field.
    """

    provider: ClassVar[str]
    challenges: ClassVar[frozenset[type[BaseChallenge]]]
    default_base_url: ClassVar[str]
    endpoints: ClassVar[Endpoints] = Endpoints(
        submit="/createTask",
        get_task_status="/getTaskResult",
        get_balance="/getBalance",
        report_good_result="/reportCorrect",
        report_bad_result="/reportIncorrect",
    )
    default_task_config: ClassVar[Mapping[type[BaseChallenge], TimeConfig] | None] = (
        None
    )

    __slots__ = ("_api_key", "_referral", "base_url")

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for name in ("provider", "challenges", "default_base_url"):
            if not hasattr(cls, name):
                raise TypeError(
                    f"{cls.__name__} must declare class attribute {name!r} "
                    "(adapter SDK contract, ADR-0053)"
                )

    def __init__(
        self,
        api_key: SecretStr | str,
        base_url: str | None = None,
        *,
        referral: bool | str = True,
    ) -> None:
        self._api_key = (
            api_key if isinstance(api_key, SecretStr) else SecretStr(api_key)
        )
        self.base_url = base_url or self.default_base_url
        self._referral = referral

    def __repr__(self) -> str:
        return f"{type(self).__name__}(api_key=***)"

    __str__ = __repr__

    @abstractmethod
    def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
        """Build the provider request body for a challenge."""
        ...

    @abstractmethod
    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        """Parse a ``createTask`` response (ADR-0075)."""
        ...

    @abstractmethod
    def parse_task_status(self, raw: bytes) -> ParsedTask:
        """Parse a ``getTaskResult`` response into a four-state
        ``ParsedTask`` (ADR-0058)."""
        ...

    @abstractmethod
    def parse_balance(self, raw: bytes) -> Decimal:
        """Parse a balance response into an exact ``Decimal`` (USD)."""
        ...

    def build_task_status(self, task_id: int | str) -> dict[str, Any]:
        """Build a ``getTaskResult`` request body (JSON-family default,
        ADR-0001). Overridable by adapters for divergent protocols."""
        return {
            "clientKey": self._api_key.get_secret_value(),
            "taskId": task_id,
        }

    def build_balance(self) -> dict[str, Any]:
        """Build a ``getBalance`` request body (JSON-family default,
        ADR-0001). Overridable by adapters for divergent protocols."""
        return {"clientKey": self._api_key.get_secret_value()}

    @abstractmethod
    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        """Map a provider error body to ``(ErrorKind, message)``."""
        ...

    def report_bad_supported(self, challenge_type: type[BaseChallenge]) -> bool:
        """Whether the provider accepts bad reports for this kind."""
        return False

    def build_report_bad(self, task: TaskRef) -> dict[str, Any]:
        raise UnsupportedChallengeError(
            f"{type(self).__name__} does not support report_bad_result"
        )

    def parse_report_bad(self, raw: bytes) -> bool:
        raise UnsupportedChallengeError(
            f"{type(self).__name__} does not support report_bad_result"
        )

    def report_good_supported(self, challenge_type: type[BaseChallenge]) -> bool:
        """Whether the provider accepts good reports for this kind
        (ADR-0068)."""
        return False

    def build_report_good(self, task: TaskRef) -> dict[str, Any]:
        raise UnsupportedChallengeError(
            f"{type(self).__name__} does not support report_good_result"
        )

    def parse_report_good(self, raw: bytes) -> bool:
        raise UnsupportedChallengeError(
            f"{type(self).__name__} does not support report_good_result"
        )


__all__ = ["BaseAdapter", "Endpoints"]
