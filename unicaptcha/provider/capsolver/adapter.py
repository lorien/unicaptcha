"""The Capsolver adapter (``createTask``/``getTaskResult`` JSON API).

Pure translation unit (ADR-0041): challenge → request payload, response
bytes → typed objects, provider error codes → the library error hierarchy.
Field mapping per the live Capsolver docs (2026) and the official SDK's
``SUPPORT_TASK_TYPE`` (task-14 cross-check).

Capsolver specifics:
- ``taskId`` is a UUID string — ``_task_id`` returns ``int | str``.
- Proxy accepts the structured 5-field block (hostnames OK, no IP-only
  rule) or a concatenated string; we use the 5-field block.
- Recognition tasks (ImageToText) answer inline — the submit-ready fast
  path (ADR-0075) is the normal path for them.
- ``getTaskResult`` may answer ``status: "failed"`` → ``NO_SOLUTION``.
- No affiliate-id field exists in Capsolver's API; ``referral`` is
  accepted for parity (ADR-0072) but embeds nothing.
"""

from __future__ import annotations

import base64
import json
from decimal import Decimal, InvalidOperation
from typing import Any, ClassVar, cast

from unicaptcha._internal.errors import error_from_kind
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import (
    EmptySolutionError,
    ErrorKind,
    InvalidChallengeError,
    ProviderError,
    UnsupportedChallengeError,
)
from unicaptcha.provider.capsolver.challenge import (
    CapsolverFunCaptchaChallenge,
    CapsolverGeeTestV3Challenge,
    CapsolverGeeTestV4Challenge,
    CapsolverHCaptchaChallenge,
    CapsolverImageChallenge,
    CapsolverRecaptchaV2Challenge,
    CapsolverRecaptchaV3Challenge,
    CapsolverTurnstileChallenge,
)
from unicaptcha.provider.capsolver.solution import (
    CapsolverFunCaptchaSolution,
    CapsolverGeeTestV3Solution,
    CapsolverGeeTestV4Solution,
    CapsolverHCaptchaSolution,
    CapsolverImageSolution,
    CapsolverRecaptchaV2Solution,
    CapsolverRecaptchaV3Solution,
    CapsolverTurnstileSolution,
)
from unicaptcha.types import ParsedTask, Proxy, SubmitAccepted, TaskStatus

_ERROR_KINDS: dict[str, ErrorKind] = {
    "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
    "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
    "ERROR_IP_NOT_ALLOWED": ErrorKind.AUTHENTICATION,
    "ERROR_IP_BANNED": ErrorKind.AUTHENTICATION,
    "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
    "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
    "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
}
_UNKNOWN_TASK_CODES = frozenset(
    {"ERROR_TASK_ABSENT", "ERROR_WRONG_TASK_ID", "ERROR_TASK_NOT_FOUND"}
)


def _decode(raw: bytes) -> dict[str, Any]:
    """Lenient JSON-object decode; failures chain into ``ProviderError``
    with the verbatim body preserved (ADR-0040)."""
    try:
        data = json.loads(raw.decode("utf-8", errors="replace").strip())
    except ValueError as exc:
        raise ProviderError(
            "malformed JSON response from capsolver", raw_response=raw
        ) from exc
    if not isinstance(data, dict):
        raise ProviderError("capsolver response is not a JSON object", raw_response=raw)
    return cast(dict[str, Any], data)


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ProviderError(f"invalid balance/cost value {value!r}") from exc


def _proxy_fields(proxy: Proxy | None) -> dict[str, Any]:
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


def _cookies(cookies: Any) -> str | None:
    if not cookies:
        return None
    return "; ".join(f"{key}={value}" for key, value in cookies.items())


def _single_token(field_name: str, mapping: dict[str, str]) -> str:
    """Collapse a one-entry mapping into the token string it wraps."""
    if len(mapping) != 1:
        raise InvalidChallengeError(
            f"{field_name} must contain exactly one entry to be sent as a string token"
        )
    return next(iter(mapping.values()))


def _task_id(data: dict[str, Any]) -> int | str:
    """Capsolver ``taskId`` is a UUID string; numeric strings normalize to
    int for ergonomic parity with the other providers."""
    value = data.get("taskId")
    if isinstance(value, bool):
        raise ProviderError(f"invalid taskId {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.isdigit():
            return int(value)
        if value:
            return value
    raise ProviderError(f"submit response lacks a usable taskId: {value!r}")


class CapsolverAdapter(BaseAdapter):
    """Adapter speaking Capsolver's createTask/getTaskResult API."""

    provider: ClassVar[str] = "capsolver"
    challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset(
        {
            CapsolverImageChallenge,
            CapsolverRecaptchaV2Challenge,
            CapsolverRecaptchaV3Challenge,
            CapsolverHCaptchaChallenge,
            CapsolverFunCaptchaChallenge,
            CapsolverGeeTestV3Challenge,
            CapsolverGeeTestV4Challenge,
            CapsolverTurnstileChallenge,
        }
    )
    default_base_url: ClassVar[str] = "https://api.capsolver.com"

    # -- submit ----------------------------------------------------------

    def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
        task = self._build_task(challenge)
        return {
            "clientKey": self._api_key.get_secret_value(),
            "task": task,
        }

    def _build_task(self, challenge: BaseChallenge) -> dict[str, Any]:
        if isinstance(challenge, CapsolverImageChallenge):
            return self._image_task(challenge)
        if isinstance(challenge, CapsolverRecaptchaV2Challenge):
            return self._recaptcha_v2_task(challenge)
        if isinstance(challenge, CapsolverRecaptchaV3Challenge):
            return self._recaptcha_v3_task(challenge)
        if isinstance(challenge, CapsolverHCaptchaChallenge):
            return self._hcaptcha_task(challenge)
        if isinstance(challenge, CapsolverFunCaptchaChallenge):
            return self._funcaptcha_task(challenge)
        if isinstance(challenge, CapsolverGeeTestV3Challenge):
            return self._geetest_v3_task(challenge)
        if isinstance(challenge, CapsolverGeeTestV4Challenge):
            return self._geetest_v4_task(challenge)
        if isinstance(challenge, CapsolverTurnstileChallenge):
            return self._turnstile_task(challenge)
        raise UnsupportedChallengeError(
            f"CapsolverAdapter does not support {type(challenge).__name__}"
        )

    def _image_task(self, ch: CapsolverImageChallenge) -> dict[str, Any]:
        body = cast(bytes, ch.body)  # normalized at construction
        task: dict[str, Any] = {
            "type": "ImageToTextTask",
            "body": base64.b64encode(body).decode("ascii"),
        }
        if ch.module is not None:
            task["module"] = ch.module
        return task

    def _recaptcha_v2_task(self, ch: CapsolverRecaptchaV2Challenge) -> dict[str, Any]:
        if ch.is_enterprise:
            task: dict[str, Any] = {
                "type": (
                    "ReCaptchaV2EnterpriseTask"
                    if ch.proxy is not None
                    else "ReCaptchaV2EnterpriseTaskProxyLess"
                ),
                "websiteURL": ch.pageurl,
                "websiteKey": ch.sitekey,
            }
            if ch.data_s:
                task["enterprisePayload"] = {
                    "s": _single_token("data_s", dict(ch.data_s))
                }
        else:
            task = {
                "type": (
                    "ReCaptchaV2Task"
                    if ch.proxy is not None
                    else "ReCaptchaV2TaskProxyLess"
                ),
                "websiteURL": ch.pageurl,
                "websiteKey": ch.sitekey,
            }
            if ch.data_s:
                task["recaptchaDataSValue"] = _single_token("data_s", dict(ch.data_s))
            if ch.invisible:
                task["isInvisible"] = True
        if ch.action is not None:
            task["pageAction"] = ch.action
        if ch.api_domain is not None:
            task["apiDomain"] = ch.api_domain
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = _cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        task.update(_proxy_fields(ch.proxy))
        return task

    def _recaptcha_v3_task(self, ch: CapsolverRecaptchaV3Challenge) -> dict[str, Any]:
        # Proxyless-only; is_enterprise rejected at construction.
        task: dict[str, Any] = {
            "type": "ReCaptchaV3TaskProxyLess",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.action is not None:
            task["pageAction"] = ch.action
        if ch.min_score is not None:
            task["minScore"] = ch.min_score
        return task

    def _hcaptcha_task(self, ch: CapsolverHCaptchaChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": (
                "HCaptchaTask" if ch.proxy is not None else "HCaptchaTaskProxyLess"
            ),
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.is_invisible:
            task["isInvisible"] = True
        if ch.rqdata is not None:
            task["rqdata"] = ch.rqdata
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = _cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        task.update(_proxy_fields(ch.proxy))
        return task

    def _funcaptcha_task(self, ch: CapsolverFunCaptchaChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": (
                "FunCaptchaTask" if ch.proxy is not None else "FunCaptchaTaskProxyLess"
            ),
            "websiteURL": ch.pageurl,
            "websitePublicKey": ch.public_key,
        }
        task.update(_proxy_fields(ch.proxy))
        return task

    def _geetest_v3_task(self, ch: CapsolverGeeTestV3Challenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": ("GeeTestTask" if ch.proxy is not None else "GeeTestTaskProxyLess"),
            "websiteURL": ch.pageurl,
            "gt": ch.gt_key,
            "challenge": ch.challenge,
        }
        if ch.api_server is not None:
            task["geetestApiServerSubdomain"] = ch.api_server
        task.update(_proxy_fields(ch.proxy))
        return task

    def _geetest_v4_task(self, ch: CapsolverGeeTestV4Challenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": ("GeeTestTask" if ch.proxy is not None else "GeeTestTaskProxyLess"),
            "websiteURL": ch.pageurl,
            "captchaId": ch.captcha_id,
        }
        if ch.risk_type is not None:
            task["riskType"] = ch.risk_type
        if ch.api_server is not None:
            task["geetestApiServerSubdomain"] = ch.api_server
        task.update(_proxy_fields(ch.proxy))
        return task

    def _turnstile_task(self, ch: CapsolverTurnstileChallenge) -> dict[str, Any]:
        # Fixed proxyless type; userAgent ignored by the provider.
        task: dict[str, Any] = {
            "type": "AntiTurnstileTaskProxyLess",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        metadata: dict[str, str] = {}
        if ch.action is not None:
            metadata["action"] = ch.action
        if ch.c_data is not None:
            metadata["cdata"] = ch.c_data
        if metadata:
            task["metadata"] = metadata
        return task

    # -- response parsing --------------------------------------------------

    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        data = _decode(raw)
        if data.get("errorId"):
            kind, message = self.map_provider_error(raw)
            raise error_from_kind(kind, message, raw)
        task_id = _task_id(data)
        if data.get("status") == "ready":
            solution = _solution_dict(data)
            instant = ParsedTask(
                state=TaskStatus.READY,
                solution=self._solution_from(solution),
                cost=_decimal(data.get("cost")),
                raw=raw,
            )
            return SubmitAccepted(task_id=task_id, instant_answer=instant)
        return SubmitAccepted(task_id=task_id)

    def parse_task_status(self, raw: bytes) -> ParsedTask:
        data = _decode(raw)
        if data.get("errorId"):
            code = _provider_code(data)
            message = _provider_message(data)
            if code in _UNKNOWN_TASK_CODES:
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
        status = data.get("status")
        if status == "ready":
            solution = _solution_dict(data)
            return ParsedTask(
                state=TaskStatus.READY,
                solution=self._solution_from(solution),
                cost=_decimal(data.get("cost")),
                raw=raw,
            )
        if status == "failed":
            return ParsedTask(
                state=TaskStatus.NO_SOLUTION, solution=None, cost=None, raw=raw
            )
        return ParsedTask(state=TaskStatus.PENDING, solution=None, cost=None, raw=raw)

    def parse_balance(self, raw: bytes) -> Decimal:
        data = _decode(raw)
        if data.get("errorId"):
            kind, message = self.map_provider_error(raw)
            raise error_from_kind(kind, message, raw)
        balance = _decimal(data.get("balance"))
        if balance is None:
            raise ProviderError(
                "balance response lacks a usable 'balance' field",
                raw_response=raw,
            )
        return balance

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        data = _decode(raw)
        code = _provider_code(data)
        kind = _ERROR_KINDS.get(code, ErrorKind.PROVIDER)
        message = _provider_message(data) or code or "unknown provider error"
        return kind, message

    def _solution_from(self, solution: dict[str, Any]) -> Any:
        g_response = solution.get("gRecaptchaResponse")
        token = solution.get("token")
        kind = str(solution.get("type") or "").lower()
        if "captcha_output" in solution and "lot_number" in solution:
            return CapsolverGeeTestV4Solution(
                captcha_id=str(solution.get("captcha_id", "")),
                lot_number=str(solution.get("lot_number", "")),
                pass_token=str(solution.get("pass_token", "")),
                gen_time=str(solution.get("gen_time", "")),
                captcha_output=str(solution.get("captcha_output", "")),
            )
        if {"challenge", "validate", "seccode"} <= set(solution):
            return CapsolverGeeTestV3Solution(
                challenge=str(solution["challenge"]),
                validate=str(solution["validate"]),
                seccode=str(solution["seccode"]),
            )
        if "score" in solution:
            score = solution.get("score")
            return CapsolverRecaptchaV3Solution(
                token=str(g_response or token or ""),
                score=float(score) if score is not None else None,
                action=(
                    str(solution["action"])
                    if solution.get("action") is not None
                    else None
                ),
            )
        if g_response:
            return CapsolverRecaptchaV2Solution(str(g_response))
        if "text" in solution:
            return CapsolverImageSolution(str(solution["text"]))
        if token:
            if kind == "turnstile":
                return CapsolverTurnstileSolution(str(token))
            if kind in ("funcaptcha", "arkoselabs"):
                return CapsolverFunCaptchaSolution(str(token))
            if kind in ("hcaptcha",):
                return CapsolverHCaptchaSolution(str(token))
            # Ambiguous bare token (hCaptcha-shaped fallback).
            return CapsolverHCaptchaSolution(str(token))
        raise EmptySolutionError(
            f"unrecognized capsolver solution shape: keys={sorted(solution)}"
        )


def _solution_dict(data: dict[str, Any]) -> dict[str, Any]:
    solution = data.get("solution")
    if not isinstance(solution, dict) or not solution:
        raise EmptySolutionError(
            "task solved but the payload carries no solution fields"
        )
    return cast(dict[str, Any], solution)


def _provider_code(data: dict[str, Any]) -> str:
    return str(data.get("errorCode") or "").upper()


def _provider_message(data: dict[str, Any]) -> str:
    return str(data.get("errorDescription") or "")


__all__ = ["CapsolverAdapter"]
