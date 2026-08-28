"""The CapMonster Cloud adapter (``createTask``/``getTaskResult`` JSON API).

Pure translation unit (ADR-0041): challenge → request payload, response
bytes → typed objects, provider error codes → the library error hierarchy.
Field mapping per architecture §2 as verified against the official SDK
clone (`var/vendor/repo/capmonster-python`, task-13 cross-check). CapMonster is
proxyless-only (ADR-0012): no proxy serialization exists here, and the
report pairs stay default-off — CapMonster has no report API.
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
    InvalidConfigError,
    ProviderError,
    UnsupportedChallengeError,
)
from unicaptcha.provider.capmonster.challenge import (
    CapMonsterFunCaptchaChallenge,
    CapMonsterGeeTestV3Challenge,
    CapMonsterGeeTestV4Challenge,
    CapMonsterHCaptchaChallenge,
    CapMonsterImageChallenge,
    CapMonsterRecaptchaV2Challenge,
    CapMonsterRecaptchaV3Challenge,
    CapMonsterTurnstileChallenge,
)
from unicaptcha.provider.capmonster.solution import (
    CapMonsterGeeTestV3Solution,
    CapMonsterGeeTestV4Solution,
    CapMonsterImageSolution,
    CapMonsterRecaptchaV2Solution,
    CapMonsterRecaptchaV3Solution,
    CapMonsterTurnstileSolution,
)
from unicaptcha.types import ParsedTask, SubmitAccepted, TaskStatus

# ADR-0072: project affiliate id, registered at implementation time. No id
# yet — ``referral=True`` therefore embeds nothing until one is recorded.
_PROJECT_SOFT_ID: int | None = None

_ERROR_KINDS: dict[str, ErrorKind] = {
    "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
    "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
    "ERROR_IP_NOT_ALLOWED": ErrorKind.AUTHENTICATION,
    "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
    "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
    "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
}
_UNKNOWN_TASK_CODES = frozenset(
    {"ERROR_TASK_ABSENT", "ERROR_WRONG_CAPTCHA_ID", "ERROR_TASK_NOT_FOUND"}
)


def _decode(raw: bytes) -> dict[str, Any]:
    """Lenient JSON-object decode; failures chain into ``ProviderError``
    with the verbatim body preserved (ADR-0040)."""
    try:
        data = json.loads(raw.decode("utf-8", errors="replace").strip())
    except ValueError as exc:
        raise ProviderError(
            "malformed JSON response from capmonster", raw_response=raw
        ) from exc
    if not isinstance(data, dict):
        raise ProviderError(
            "capmonster response is not a JSON object", raw_response=raw
        )
    return cast(dict[str, Any], data)


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ProviderError(f"invalid balance/cost value {value!r}") from exc


def _cookies(cookies: Any) -> str | None:
    if not cookies:
        return None
    return "; ".join(f"{key}={value}" for key, value in cookies.items())


def _soft_id(referral: bool | str) -> int | None:
    """Trinary referral resolution for CapMonster's integer ``softId``
    (ADR-0072)."""
    if referral is True:
        return _PROJECT_SOFT_ID
    if referral is False:
        return None
    try:
        return int(referral)
    except ValueError as exc:
        raise InvalidConfigError(
            f"referral must be an integer id for capmonster softId, got {referral!r}"
        ) from exc


def _single_token(field_name: str, mapping: dict[str, str]) -> str:
    """Collapse a one-entry mapping into the token string it wraps."""
    if len(mapping) != 1:
        raise InvalidChallengeError(
            f"{field_name} must contain exactly one entry to be sent as a string token"
        )
    return next(iter(mapping.values()))


class CapMonsterAdapter(BaseAdapter):
    """Adapter speaking CapMonster Cloud's createTask/getTaskResult API."""

    provider: ClassVar[str] = "capmonster"
    challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset(
        {
            CapMonsterImageChallenge,
            CapMonsterRecaptchaV2Challenge,
            CapMonsterRecaptchaV3Challenge,
            CapMonsterHCaptchaChallenge,
            CapMonsterFunCaptchaChallenge,
            CapMonsterGeeTestV3Challenge,
            CapMonsterGeeTestV4Challenge,
            CapMonsterTurnstileChallenge,
        }
    )
    default_base_url: ClassVar[str] = "https://api.capmonster.cloud"

    # -- submit ----------------------------------------------------------

    def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
        task = self._build_task(challenge)
        payload: dict[str, Any] = {
            "clientKey": self._api_key.get_secret_value(),
            "task": task,
        }
        soft_id = _soft_id(self._referral)
        if soft_id is not None:
            payload["softId"] = soft_id
        return payload

    def _build_task(self, challenge: BaseChallenge) -> dict[str, Any]:
        if isinstance(challenge, CapMonsterImageChallenge):
            return self._image_task(challenge)
        if isinstance(challenge, CapMonsterRecaptchaV2Challenge):
            return self._recaptcha_v2_task(challenge)
        if isinstance(challenge, CapMonsterRecaptchaV3Challenge):
            return self._recaptcha_v3_task(challenge)
        if isinstance(challenge, CapMonsterHCaptchaChallenge):
            return self._hcaptcha_task(challenge)
        if isinstance(challenge, CapMonsterFunCaptchaChallenge):
            return self._funcaptcha_task(challenge)
        if isinstance(challenge, CapMonsterGeeTestV3Challenge):
            return self._geetest_v3_task(challenge)
        if isinstance(challenge, CapMonsterGeeTestV4Challenge):
            return self._geetest_v4_task(challenge)
        if isinstance(challenge, CapMonsterTurnstileChallenge):
            return self._turnstile_task(challenge)
        raise UnsupportedChallengeError(
            f"CapMonsterAdapter does not support {type(challenge).__name__}"
        )

    def _image_task(self, ch: CapMonsterImageChallenge) -> dict[str, Any]:
        # ImageChallenge normalized the value to bytes at construction.
        body = cast(bytes, ch.body)
        task: dict[str, Any] = {
            "type": "ImageToTextTask",
            "body": base64.b64encode(body).decode("ascii"),
        }
        if ch.module_name is not None:
            task["CapMonsterModule"] = ch.module_name
        if ch.threshold is not None:
            task["recognizingThreshold"] = ch.threshold
        if ch.case:
            task["Case"] = True
        if ch.numeric:
            task["numeric"] = ch.numeric
        if ch.math:
            task["math"] = True
        return task

    def _recaptcha_v2_task(self, ch: CapMonsterRecaptchaV2Challenge) -> dict[str, Any]:
        if ch.is_enterprise:
            task: dict[str, Any] = {
                "type": "RecaptchaV2EnterpriseTask",
                "websiteURL": ch.pageurl,
                "websiteKey": ch.sitekey,
            }
            if ch.data_s:
                task["enterprisePayload"] = {
                    "s": _single_token("data_s", dict(ch.data_s))
                }
            if ch.api_domain is not None:
                task["apiDomain"] = ch.api_domain
            if ch.action is not None:
                task["pageAction"] = ch.action
            if ch.user_agent is not None:
                task["userAgent"] = ch.user_agent
            cookie_header = _cookies(ch.cookies)
            if cookie_header is not None:
                task["cookies"] = cookie_header
            return task
        task = {
            "type": "RecaptchaV2Task",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.data_s:
            task["recaptchaDataSValue"] = _single_token("data_s", dict(ch.data_s))
        if ch.invisible:
            task["isInvisible"] = True
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = _cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        return task

    def _recaptcha_v3_task(self, ch: CapMonsterRecaptchaV3Challenge) -> dict[str, Any]:
        # Enterprise is a separate task type on CapMonster; both are
        # proxyless with no userAgent/cookies.
        task: dict[str, Any] = {
            "type": (
                "RecaptchaV3EnterpriseTask"
                if ch.is_enterprise
                else "RecaptchaV3TaskProxyless"
            ),
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.min_score is not None:
            task["minScore"] = ch.min_score
        if ch.action is not None:
            task["pageAction"] = ch.action
        return task

    def _hcaptcha_task(self, ch: CapMonsterHCaptchaChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": "HCaptchaTask",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.is_invisible:
            task["isInvisible"] = True
        if ch.rqdata is not None:
            task["data"] = ch.rqdata
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        if ch.fallback_to_actual_ua is not None:
            task["fallbackToActualUA"] = ch.fallback_to_actual_ua
        cookie_header = _cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        return task

    def _funcaptcha_task(self, ch: CapMonsterFunCaptchaChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": "FunCaptchaTask",
            "websiteURL": ch.pageurl,
            "websitePublicKey": ch.public_key,
        }
        if ch.service_url is not None:
            task["funcaptchaApiJSSubdomain"] = ch.service_url
        if ch.data is not None:
            task["data"] = ch.data
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = _cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        return task

    def _geetest_v3_task(self, ch: CapMonsterGeeTestV3Challenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": "GeeTestTask",
            "websiteURL": ch.pageurl,
            "gt": ch.gt_key,
            "challenge": ch.challenge,
            "version": 3,
        }
        if ch.api_server is not None:
            task["geetestApiServerSubdomain"] = ch.api_server
        if ch.geetest_lib is not None:
            task["geetestGetLib"] = ch.geetest_lib
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        return task

    def _geetest_v4_task(self, ch: CapMonsterGeeTestV4Challenge) -> dict[str, Any]:
        init_parameters: dict[str, str] = {"captcha_id": ch.captcha_id}
        if ch.risk_type is not None:
            init_parameters["riskType"] = ch.risk_type
        task: dict[str, Any] = {
            "type": "GeeTestTask",
            "websiteURL": ch.pageurl,
            "version": 4,
            "initParameters": init_parameters,
        }
        if ch.api_server is not None:
            task["geetestApiServerSubdomain"] = ch.api_server
        if ch.geetest_lib is not None:
            task["geetestGetLib"] = ch.geetest_lib
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        return task

    def _turnstile_task(self, ch: CapMonsterTurnstileChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": "TurnstileTask",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.action is not None:
            task["pageAction"] = ch.action
        if ch.c_data is not None:
            task["data"] = ch.c_data
        if ch.chl_page_data is not None:
            task["pageData"] = ch.chl_page_data
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        if ch.cloudflare_task_type is not None:
            task["cloudflareTaskType"] = ch.cloudflare_task_type
        if ch.html_page_base64 is not None:
            task["htmlPageBase64"] = ch.html_page_base64
        if ch.api_js_url is not None:
            task["apiJsUrl"] = ch.api_js_url
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
            if code == "ERROR_CAPTCHA_UNSOLVABLE":
                return ParsedTask(
                    state=TaskStatus.NO_SOLUTION, solution=None, cost=None, raw=raw
                )
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
        if data.get("status") == "ready":
            solution = _solution_dict(data)
            return ParsedTask(
                state=TaskStatus.READY,
                solution=self._solution_from(solution),
                cost=_decimal(data.get("cost")),
                raw=raw,
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
        if "captcha_output" in solution and "lot_number" in solution:
            return CapMonsterGeeTestV4Solution(
                captcha_id=str(solution.get("captcha_id", "")),
                lot_number=str(solution.get("lot_number", "")),
                pass_token=str(solution.get("pass_token", "")),
                gen_time=str(solution.get("gen_time", "")),
                captcha_output=str(solution.get("captcha_output", "")),
            )
        if {"challenge", "validate", "seccode"} <= set(solution):
            return CapMonsterGeeTestV3Solution(
                challenge=str(solution["challenge"]),
                validate=str(solution["validate"]),
                seccode=str(solution["seccode"]),
            )
        if "score" in solution:
            score = solution.get("score")
            return CapMonsterRecaptchaV3Solution(
                token=str(g_response or token or ""),
                score=float(score) if score is not None else None,
                action=(
                    str(solution["action"])
                    if solution.get("action") is not None
                    else None
                ),
            )
        if g_response:
            return CapMonsterRecaptchaV2Solution(str(g_response))
        if "text" in solution:
            return CapMonsterImageSolution(str(solution["text"]))
        if token:
            return CapMonsterTurnstileSolution(str(token))
        raise EmptySolutionError(
            f"unrecognized capmonster solution shape: keys={sorted(solution)}"
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


def _task_id(data: dict[str, Any]) -> int:
    value = data.get("taskId")
    if isinstance(value, bool):
        raise ProviderError(f"invalid taskId {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ProviderError(f"submit response lacks a usable taskId: {value!r}")


__all__ = ["CapMonsterAdapter"]
