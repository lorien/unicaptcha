"""The public adapter SDK contract (ADR-0041, ADR-0053).

``BaseAdapter`` is the abstract base class every shipped and third-party
adapter implements; ``Endpoints`` declares the request paths an adapter
uses (ADR-0073). This module is part of the public surface and never
imports ``unicaptcha._internal``.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, ClassVar, cast

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import (
    EmptySolutionError,
    ErrorKind,
    InvalidChallengeError,
    InvalidConfigError,
    ProviderError,
    UnsupportedChallengeError,
    error_from_kind,
)
from unicaptcha.types import (
    ParsedTask,
    Proxy,
    SecretStr,
    SubmitAccepted,
    TaskRef,
    TaskStatus,
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


class JsonAdapterBase(BaseAdapter):
    """Shared implementation base for the JSON-family
    ``createTask``/``getTaskResult`` adapters (2Captcha, Anti-Captcha,
    CapMonster Cloud, Capsolver).

    Provides the response-parsing pipeline (decode -> error mapping ->
    submit/status/balance parsing) and the shared field/payload helpers;
    subclasses declare ``json_provider``, ``error_kinds``, and
    ``unknown_task_codes`` and supply the per-provider task builders
    (``_build_task``) and solution dispatch (``_solution_from``).

    Public so third-party JSON-family adapters can reuse it without
    touching ``unicaptcha._internal`` (ADR-0041 boundary).
    """

    # Placeholder declarations satisfy the ``BaseAdapter`` subclass
    # contract; concrete subclasses must set real values.
    provider: ClassVar[str] = "json"
    challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset()
    default_base_url: ClassVar[str] = ""

    #: Display label used in decode/parse error messages ("from <label>").
    json_provider: ClassVar[str]
    #: Provider ``errorCode`` -> ``ErrorKind``.
    error_kinds: ClassVar[Mapping[str, ErrorKind]]
    #: Codes meaning "task address unknown" -> ``TaskStatus.UNKNOWN``.
    unknown_task_codes: ClassVar[frozenset[str]]
    #: ADR-0072 affiliate id; ``None`` = not registered.
    project_soft_id: ClassVar[int | None] = None

    @abstractmethod
    def _build_task(self, challenge: BaseChallenge) -> dict[str, Any]:
        """Provider-specific challenge -> task mapping."""

    @abstractmethod
    def _solution_from(self, solution: dict[str, Any]) -> Any:
        """Provider-specific solution-shape dispatch."""

    # -- shared field helpers ----------------------------------------------

    def _decode(self, raw: bytes) -> dict[str, Any]:
        """Lenient JSON-object decode; failures chain into ``ProviderError``
        with the verbatim body preserved (ADR-0040)."""
        try:
            data = json.loads(raw.decode("utf-8", errors="replace").strip())
        except ValueError as exc:
            raise ProviderError(
                f"malformed JSON response from {self.json_provider}",
                raw_response=raw,
            ) from exc
        if not isinstance(data, dict):
            raise ProviderError(
                f"{self.json_provider} response is not a JSON object",
                raw_response=raw,
            )
        return cast(dict[str, Any], data)

    def _decimal(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ProviderError(f"invalid balance/cost value {value!r}") from exc

    def _cookies(self, cookies: Any) -> str | None:
        """Worker cookies serialize header-style: ``k1=v1; k2=v2``."""
        if not cookies:
            return None
        return "; ".join(f"{key}={value}" for key, value in cookies.items())

    def _single_token(self, field_name: str, mapping: dict[str, str]) -> str:
        """Collapse a one-entry mapping into the token string it wraps."""
        if len(mapping) != 1:
            raise InvalidChallengeError(
                f"{field_name} must contain exactly one entry to be "
                "sent as a string token"
            )
        return next(iter(mapping.values()))

    def _solution_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        solution = data.get("solution")
        if not isinstance(solution, dict) or not solution:
            raise EmptySolutionError(
                "task solved but the payload carries no solution fields"
            )
        return cast(dict[str, Any], solution)

    def _provider_code(self, data: dict[str, Any]) -> str:
        return str(data.get("errorCode") or "").upper()

    def _provider_message(self, data: dict[str, Any]) -> str:
        return str(data.get("errorDescription") or "")

    def _task_id(self, data: dict[str, Any]) -> int | str:
        value = data.get("taskId")
        if isinstance(value, bool):
            raise ProviderError(f"invalid taskId {value!r}")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise ProviderError(f"submit response lacks a usable taskId: {value!r}")

    def _soft_id(self, referral: bool | str) -> int | None:
        """Trinary referral resolution for integer ``softId`` fields
        (ADR-0072)."""
        if referral is True:
            return self.project_soft_id
        if referral is False:
            return None
        try:
            return int(referral)
        except ValueError as exc:
            raise InvalidConfigError(
                f"referral must be an integer id for {self.json_provider} "
                f"softId, got {referral!r}"
            ) from exc

    def _proxy_fields(self, proxy: Proxy | None) -> dict[str, Any]:
        """Serialize the five-field proxy block (hostnames allowed)."""
        if proxy is None:
            return {}
        fields: dict[str, Any] = {
            "proxyType": proxy.kind.value.lower(),
            "proxyAddress": proxy.host,
            "proxyPort": proxy.port,
        }
        if proxy.username is not None:
            fields["proxyLogin"] = proxy.username
        if proxy.password is not None:
            fields["proxyPassword"] = proxy.password
        return fields

    # -- shared pipeline ---------------------------------------------------

    def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
        task = self._build_task(challenge)
        payload: dict[str, Any] = {
            "clientKey": self._api_key.get_secret_value(),
            "task": task,
        }
        payload.update(self._extra_envelope(challenge))
        soft_id = self._soft_id(self._referral)
        if soft_id is not None:
            payload["softId"] = soft_id
        return payload

    def _extra_envelope(self, challenge: BaseChallenge) -> dict[str, Any]:
        """Provider-specific envelope-level fields (default: none)."""
        return {}

    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        data = self._decode(raw)
        if data.get("errorId"):
            kind, message = self.map_provider_error(raw)
            raise error_from_kind(kind, message, raw)
        task_id = self._task_id(data)
        if data.get("status") == "ready":
            solution = self._solution_dict(data)
            instant = ParsedTask(
                state=TaskStatus.READY,
                solution=self._solution_from(solution),
                cost=self._decimal(data.get("cost")),
                raw=raw,
            )
            return SubmitAccepted(task_id=task_id, instant_answer=instant)
        return SubmitAccepted(task_id=task_id)

    def parse_task_status(self, raw: bytes) -> ParsedTask:
        data = self._decode(raw)
        if data.get("errorId"):
            code = self._provider_code(data)
            message = self._provider_message(data)
            if code == "ERROR_CAPTCHA_UNSOLVABLE":
                return ParsedTask(
                    state=TaskStatus.NO_SOLUTION, solution=None, cost=None, raw=raw
                )
            if code in self.unknown_task_codes:
                return ParsedTask(
                    state=TaskStatus.UNKNOWN,
                    solution=None,
                    cost=None,
                    raw=raw,
                    detail=message,
                )
            _, mapped = self.map_provider_error(raw)
            return ParsedTask(
                state=TaskStatus.UNKNOWN,
                solution=None,
                cost=None,
                raw=raw,
                detail=mapped,
            )
        if data.get("status") == "ready":
            solution = self._solution_dict(data)
            return ParsedTask(
                state=TaskStatus.READY,
                solution=self._solution_from(solution),
                cost=self._decimal(data.get("cost")),
                raw=raw,
            )
        return ParsedTask(state=TaskStatus.PENDING, solution=None, cost=None, raw=raw)

    def parse_balance(self, raw: bytes) -> Decimal:
        data = self._decode(raw)
        if data.get("errorId"):
            kind, message = self.map_provider_error(raw)
            raise error_from_kind(kind, message, raw)
        balance = self._decimal(data.get("balance"))
        if balance is None:
            raise ProviderError(
                "balance response lacks a usable 'balance' field",
                raw_response=raw,
            )
        return balance

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        data = self._decode(raw)
        code = self._provider_code(data)
        kind = self.error_kinds.get(code, ErrorKind.PROVIDER)
        message = self._provider_message(data) or code or "unknown provider error"
        return kind, message


__all__ = ["BaseAdapter", "Endpoints", "JsonAdapterBase"]
