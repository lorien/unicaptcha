"""Reference third-party adapter (ADR-0046).

``MyServiceAdapter`` implements the public adapter SDK contract exactly as
an external author would: **public imports only, never
``unicaptcha._internal``** (CI-enforced by
``test_reference_adapter.py::test_reference_adapter_never_imports_internal``).
It registers into a real ``Solver``/``AsyncSolver`` and solves scripted
challenges through the full engine in the tests; it doubles as living
documentation for "authoring a custom provider".
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar

from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.challenge.image import ImageChallenge
from unicaptcha.challenge.recaptcha_v2 import RecaptchaV2Challenge
from unicaptcha.errors import (
    AuthenticationError,
    ErrorKind,
    InvalidChallengeError,
    ProviderError,
    RateLimitError,
    ServiceBusyError,
)
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.types import (
    ParsedTask,
    SubmitAccepted,
    TaskRef,
    TaskStatus,
    TimeConfig,
)


@dataclass(frozen=True, slots=True)
class MyServiceImageSolution(ImageSolution):
    """Solved image captcha text from the reference provider."""


@dataclass(frozen=True, slots=True)
class MyServiceRecaptchaV2Solution(RecaptchaV2Solution):
    """Solved reCAPTCHA v2 token from the reference provider."""


@dataclass(frozen=True, slots=True)
class MyServiceImageChallenge(ImageChallenge):
    """Image challenge for the reference provider."""

    solution_type: ClassVar[type[BaseSolution]] = MyServiceImageSolution


@dataclass(frozen=True, slots=True)
class MyServiceRecaptchaV2Challenge(RecaptchaV2Challenge):
    """reCAPTCHA v2 challenge for the reference provider."""

    solution_type: ClassVar[type[BaseSolution]] = MyServiceRecaptchaV2Solution


class MyServiceAdapter(BaseAdapter):
    """A minimal-but-complete third-party adapter speaking the JSON-family
    ``createTask``/``getTaskResult`` protocol (ADR-0001 shape family).

    Written to show every contract hook an external adapter may touch:
    payload building, 4-state status parsing, the submit-ready fast path,
    balance, report pairs, and per-kind timing defaults. Network is mocked
    at the transport level (respx) in tests — this adapter is pure.
    """

    provider: ClassVar[str] = "myservice"
    challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset(
        {MyServiceImageChallenge, MyServiceRecaptchaV2Challenge}
    )
    default_base_url: ClassVar[str] = "https://myservice.example"
    default_task_config: ClassVar[dict[type[BaseChallenge], TimeConfig]] = {
        MyServiceImageChallenge: TimeConfig(
            total_timeout=30.0, poll_interval=2.0, poll_delay=0.0
        ),
        MyServiceRecaptchaV2Challenge: TimeConfig(
            total_timeout=120.0, poll_interval=5.0, poll_delay=0.0
        ),
    }

    # -- submit ----------------------------------------------------------

    def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
        if isinstance(challenge, MyServiceImageChallenge):
            task: dict[str, Any] = {
                "type": "ImageToTextTask",
                "body": base64.b64encode(challenge.body).decode("ascii"),
            }
        elif isinstance(challenge, MyServiceRecaptchaV2Challenge):
            task = {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": challenge.pageurl,
                "websiteKey": challenge.sitekey,
            }
        else:
            raise InvalidChallengeError(
                f"MyServiceAdapter does not support {type(challenge).__name__}"
            )
        payload: dict[str, Any] = {
            "clientKey": self._api_key.get_secret_value(),
            "task": task,
        }
        if isinstance(self._referral, str):
            payload["softId"] = int(self._referral)
        return payload

    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        data = json.loads(raw)
        if data.get("errorId"):
            self._raise_mapped(raw)
        task_id = int(data["taskId"])
        if data.get("status") == "ready":
            return SubmitAccepted(
                task_id=task_id,
                instant_answer=ParsedTask(
                    state=TaskStatus.READY,
                    solution=MyServiceImageSolution("instant"),
                    cost=Decimal(str(data.get("cost") or "0.0001")),
                    raw=raw,
                ),
            )
        return SubmitAccepted(task_id=task_id)

    # -- status / balance / errors -----------------------------------------

    def parse_task_status(self, raw: bytes) -> ParsedTask:
        data = json.loads(raw)
        if data.get("errorId"):
            if data.get("errorCode") == "ERROR_CAPTCHA_UNSOLVABLE":
                return ParsedTask(
                    state=TaskStatus.NO_SOLUTION, solution=None, cost=None, raw=raw
                )
            self._raise_mapped(raw)
        status = data.get("status")
        if status == "ready":
            solution_data = data["solution"]
            if "gRecaptchaResponse" in solution_data:
                solution: BaseSolution = MyServiceRecaptchaV2Solution(
                    solution_data["gRecaptchaResponse"]
                )
            elif "text" in solution_data:
                solution = MyServiceImageSolution(solution_data["text"])
            else:
                solution = MyServiceImageSolution(str(solution_data["token"]))
            return ParsedTask(
                state=TaskStatus.READY,
                solution=solution,
                cost=Decimal(str(data.get("cost") or "0.0001")),
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
        data = json.loads(raw)
        if data.get("errorId"):
            self._raise_mapped(raw)
        return Decimal(str(data["balance"]))

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        data = json.loads(raw)
        code = data.get("errorCode", "")
        message = data.get("errorDescription") or code or "provider error"
        kind = {
            "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
            "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
            "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
        }.get(code, ErrorKind.PROVIDER)
        return kind, message

    # -- report pairs (ADR-0068) ------------------------------------------

    def report_bad_supported(self, challenge_type: type[BaseChallenge]) -> bool:
        return True

    def build_report_bad(self, task: TaskRef) -> dict[str, Any]:
        return {"clientKey": self._api_key.get_secret_value(), "taskId": task.task_id}

    def parse_report_bad(self, raw: bytes) -> bool:
        data = json.loads(raw)
        if data.get("errorId"):
            self._raise_mapped(raw)
        return data.get("status") == "success"

    def report_good_supported(self, challenge_type: type[BaseChallenge]) -> bool:
        return True

    def build_report_good(self, task: TaskRef) -> dict[str, Any]:
        return {"clientKey": self._api_key.get_secret_value(), "taskId": task.task_id}

    def parse_report_good(self, raw: bytes) -> bool:
        return self.parse_report_bad(raw)

    # -- private -----------------------------------------------------------

    def _raise_mapped(self, raw: bytes) -> None:
        kind, message = self.map_provider_error(raw)
        cls = {
            ErrorKind.AUTHENTICATION: AuthenticationError,
            ErrorKind.RATE_LIMIT: RateLimitError,
            ErrorKind.SERVICE_BUSY: ServiceBusyError,
        }.get(kind, ProviderError)
        raise cls(message, raw_response=raw)


__all__ = [
    "MyServiceAdapter",
    "MyServiceImageChallenge",
    "MyServiceImageSolution",
    "MyServiceRecaptchaV2Challenge",
    "MyServiceRecaptchaV2Solution",
]
