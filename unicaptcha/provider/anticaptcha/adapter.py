"""The Anti-Captcha adapter (``createTask``/``getTaskResult`` JSON API).

Pure translation unit (ADR-0041): challenge → request payload, response
bytes → typed objects, provider error codes → the library error hierarchy.
Field mapping per architecture §2 as verified against the official SDK
clone (`var/repo/anticaptcha-python`, task-12 cross-check).

Proxy rule (ADR-0076 / ADR-0012): Anti-Captcha accepts IP addresses only;
this adapter validates the literal pre-flight and raises
``InvalidChallengeError`` for hostnames — engine-side hostname→IP
resolution is deferred (deferred.md item 22 follow-up).

Report pairs stay default-off: Anti-Captcha's report endpoints are
per-kind (reportIncorrectImageCaptcha / reportIncorrectRecaptcha /
reportCorrectRecaptcha / reportIncorrectHcaptcha) while ``TaskRef``
carries no kind context.
"""

from __future__ import annotations

import base64
import ipaddress
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
from unicaptcha.provider.anticaptcha.challenge import (
    AntiCaptchaFunCaptchaChallenge,
    AntiCaptchaGeeTestV3Challenge,
    AntiCaptchaGeeTestV4Challenge,
    AntiCaptchaHCaptchaChallenge,
    AntiCaptchaImageChallenge,
    AntiCaptchaRecaptchaV2Challenge,
    AntiCaptchaRecaptchaV3Challenge,
    AntiCaptchaTextChallenge,
    AntiCaptchaTurnstileChallenge,
)
from unicaptcha.provider.anticaptcha.solution import (
    AntiCaptchaGeeTestV3Solution,
    AntiCaptchaGeeTestV4Solution,
    AntiCaptchaHCaptchaSolution,
    AntiCaptchaImageSolution,
    AntiCaptchaRecaptchaV2Solution,
    AntiCaptchaRecaptchaV3Solution,
)
from unicaptcha.types import ParsedTask, Proxy, SubmitAccepted, TaskStatus

# ADR-0072: project affiliate id, registered at implementation time. No id
# yet — ``referral=True`` therefore embeds nothing until one is recorded.
_PROJECT_SOFT_ID: int | None = None

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
    {"ERROR_TASK_ABSENT", "ERROR_WRONG_CAPTCHA_ID", "ERROR_TASK_NOT_FOUND"}
)


def _decode(raw: bytes) -> dict[str, Any]:
    """Lenient JSON-object decode; failures chain into ``ProviderError``
    with the verbatim body preserved (ADR-0040)."""
    try:
        data = json.loads(raw.decode("utf-8", errors="replace").strip())
    except ValueError as exc:
        raise ProviderError(
            "malformed JSON response from anti-captcha", raw_response=raw
        ) from exc
    if not isinstance(data, dict):
        raise ProviderError(
            "anti-captcha response is not a JSON object", raw_response=raw
        )
    return cast(dict[str, Any], data)


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ProviderError(f"invalid balance/cost value {value!r}") from exc


def _proxy_fields(proxy: Proxy | None, challenge_name: str) -> dict[str, Any]:
    """Serialize the five-field proxy block. Anti-Captcha accepts IP
    addresses only (ADR-0076); hostnames are rejected here — pure code,
    no DNS resolution."""
    if proxy is None:
        return {}
    try:
        ipaddress.ip_address(proxy.host)
    except ValueError as exc:
        raise InvalidChallengeError(
            f"{challenge_name}: anti-captcha accepts proxy IP addresses "
            f"only, got hostname {proxy.host!r}"
        ) from exc
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


def _soft_id(referral: bool | str) -> int | None:
    """Trinary referral resolution for Anti-Captcha's integer ``softId``
    (ADR-0072)."""
    if referral is True:
        return _PROJECT_SOFT_ID
    if referral is False:
        return None
    try:
        return int(referral)
    except ValueError as exc:
        raise InvalidConfigError(
            f"referral must be an integer id for anti-captcha softId, got {referral!r}"
        ) from exc


def _single_token(field_name: str, mapping: dict[str, str]) -> str:
    """Collapse a one-entry mapping into the token string it wraps."""
    if len(mapping) != 1:
        raise InvalidChallengeError(
            f"{field_name} must contain exactly one entry to be sent as a string token"
        )
    return next(iter(mapping.values()))


class AntiCaptchaAdapter(BaseAdapter):
    """Adapter speaking Anti-Captcha's createTask/getTaskResult API."""

    provider: ClassVar[str] = "anti-captcha"
    challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset(
        {
            AntiCaptchaImageChallenge,
            AntiCaptchaTextChallenge,
            AntiCaptchaRecaptchaV2Challenge,
            AntiCaptchaRecaptchaV3Challenge,
            AntiCaptchaHCaptchaChallenge,
            AntiCaptchaFunCaptchaChallenge,
            AntiCaptchaGeeTestV3Challenge,
            AntiCaptchaGeeTestV4Challenge,
            AntiCaptchaTurnstileChallenge,
        }
    )
    default_base_url: ClassVar[str] = "https://api.anti-captcha.com"

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
        if isinstance(challenge, AntiCaptchaImageChallenge):
            return self._image_task(challenge)
        if isinstance(challenge, AntiCaptchaTextChallenge):
            return self._text_task(challenge)
        if isinstance(challenge, AntiCaptchaRecaptchaV2Challenge):
            return self._recaptcha_v2_task(challenge)
        if isinstance(challenge, AntiCaptchaRecaptchaV3Challenge):
            return self._recaptcha_v3_task(challenge)
        if isinstance(challenge, AntiCaptchaHCaptchaChallenge):
            return self._hcaptcha_task(challenge)
        if isinstance(challenge, AntiCaptchaFunCaptchaChallenge):
            return self._funcaptcha_task(challenge)
        if isinstance(challenge, AntiCaptchaGeeTestV3Challenge):
            return self._geetest_v3_task(challenge)
        if isinstance(challenge, AntiCaptchaGeeTestV4Challenge):
            return self._geetest_v4_task(challenge)
        if isinstance(challenge, AntiCaptchaTurnstileChallenge):
            return self._turnstile_task(challenge)
        raise UnsupportedChallengeError(
            f"AntiCaptchaAdapter does not support {type(challenge).__name__}"
        )

    def _image_task(self, ch: AntiCaptchaImageChallenge) -> dict[str, Any]:
        # ImageChallenge normalized the value to bytes at construction.
        body = cast(bytes, ch.body)
        task: dict[str, Any] = {
            "type": "ImageToTextTask",
            "body": base64.b64encode(body).decode("ascii"),
        }
        if ch.phrase:
            task["phrase"] = True
        if ch.case:
            task["case"] = True
        if ch.numeric:
            task["numeric"] = ch.numeric
        if ch.math:
            task["math"] = True
        if ch.min_len is not None:
            task["minLength"] = ch.min_len
        if ch.max_len is not None:
            task["maxLength"] = ch.max_len
        if ch.comment is not None:
            task["comment"] = ch.comment
        if ch.language_pool is not None:
            task["languagePool"] = ch.language_pool
        return task

    def _text_task(self, ch: AntiCaptchaTextChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {"type": "TextCaptchaTask", "comment": ch.text}
        if ch.lang is not None:
            task["lang"] = ch.lang
        return task

    def _recaptcha_v2_task(self, ch: AntiCaptchaRecaptchaV2Challenge) -> dict[str, Any]:
        if ch.is_enterprise:
            task: dict[str, Any] = {
                "type": (
                    "RecaptchaV2EnterpriseTask"
                    if ch.proxy is not None
                    else "RecaptchaV2EnterpriseTaskProxyless"
                ),
                "websiteURL": ch.pageurl,
                "websiteKey": ch.sitekey,
            }
            enterprise_payload: dict[str, str] = dict(ch.data_s) if ch.data_s else {}
            if enterprise_payload:
                task["enterprisePayload"] = enterprise_payload
            if ch.user_agent is not None:
                task["userAgent"] = ch.user_agent
            cookie_header = _cookies(ch.cookies)
            if cookie_header is not None:
                task["cookies"] = cookie_header
            task.update(_proxy_fields(ch.proxy, type(ch).__name__))
            return task
        base = "RecaptchaV2Task" if ch.proxy is not None else "RecaptchaV2TaskProxyless"
        task = {
            "type": base,
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.stoken is not None:
            task["websiteSToken"] = ch.stoken
        if ch.data_s:
            task["recaptchaDataSValue"] = _single_token("data_s", dict(ch.data_s))
        if ch.invisible:
            task["isInvisible"] = True
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = _cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        task.update(_proxy_fields(ch.proxy, type(ch).__name__))
        return task

    def _recaptcha_v3_task(self, ch: AntiCaptchaRecaptchaV3Challenge) -> dict[str, Any]:
        # Anti-Captcha documents RecaptchaV3TaskProxyless only; enterprise
        # rides isEnterprise inside the same type. No userAgent/cookies.
        task: dict[str, Any] = {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.min_score is not None:
            task["minScore"] = ch.min_score
        if ch.action is not None:
            task["pageAction"] = ch.action
        if ch.is_enterprise:
            task["isEnterprise"] = True
        return task

    def _hcaptcha_task(self, ch: AntiCaptchaHCaptchaChallenge) -> dict[str, Any]:
        # userAgent rides even on proxyless tasks (official SDK behavior).
        task: dict[str, Any] = {
            "type": "HCaptchaTask" if ch.proxy is not None else "HCaptchaTaskProxyless",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        if ch.rqdata is not None:
            task["enterprisePayload"] = {"rqdata": ch.rqdata}
        if ch.is_invisible:
            task["isInvisible"] = True
        cookie_header = _cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        task.update(_proxy_fields(ch.proxy, type(ch).__name__))
        return task

    def _funcaptcha_task(self, ch: AntiCaptchaFunCaptchaChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": (
                "FunCaptchaTask" if ch.proxy is not None else "FunCaptchaTaskProxyless"
            ),
            "websiteURL": ch.pageurl,
            "funcaptchaApiJSSubdomain": ch.service_url or "",
            "data": ch.data or "",
            "websitePublicKey": ch.public_key,
        }
        task = {key: value for key, value in task.items() if value != ""}
        if ch.proxy is not None and ch.user_agent is not None:
            # UA rides proxy-on tasks only for FunCaptcha (SDK behavior).
            task["userAgent"] = ch.user_agent
        task.update(_proxy_fields(ch.proxy, type(ch).__name__))
        return task

    def _geetest_v3_task(self, ch: AntiCaptchaGeeTestV3Challenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": "GeeTestTask" if ch.proxy is not None else "GeeTestTaskProxyless",
            "websiteURL": ch.pageurl,
            "gt": ch.gt_key,
            "challenge": ch.challenge,
        }
        if ch.api_server is not None:
            task["geetestApiServerSubdomain"] = ch.api_server
        if ch.geetest_lib is not None:
            task["geetestGetLib"] = ch.geetest_lib
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        task.update(_proxy_fields(ch.proxy, type(ch).__name__))
        return task

    def _geetest_v4_task(self, ch: AntiCaptchaGeeTestV4Challenge) -> dict[str, Any]:
        init_parameters: dict[str, str] = {}
        if ch.risk_type is not None:
            init_parameters["riskType"] = ch.risk_type
        task: dict[str, Any] = {
            "type": "GeeTestTask" if ch.proxy is not None else "GeeTestTaskProxyless",
            "websiteURL": ch.pageurl,
            "gt": ch.captcha_id,
            "version": 4,
        }
        if init_parameters:
            task["initParameters"] = init_parameters
        if ch.api_server is not None:
            task["geetestApiServerSubdomain"] = ch.api_server
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        task.update(_proxy_fields(ch.proxy, type(ch).__name__))
        return task

    def _turnstile_task(self, ch: AntiCaptchaTurnstileChallenge) -> dict[str, Any]:
        # CamelCase wire names on Anti-Captcha (lowercase `data`/`pagedata`
        # is 2Captcha-only). isInvisible rides proxy-on tasks when set.
        task: dict[str, Any] = {
            "type": (
                "TurnstileTask" if ch.proxy is not None else "TurnstileTaskProxyless"
            ),
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.action is not None:
            task["action"] = ch.action
        if ch.c_data is not None:
            task["cData"] = ch.c_data
        if ch.chl_page_data is not None:
            task["chlPageData"] = ch.chl_page_data
        task.update(_proxy_fields(ch.proxy, type(ch).__name__))
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
        user_agent = _optional_str(solution.get("userAgent"))
        resp_key = _optional_str(solution.get("respKey"))
        if "captcha_output" in solution and "lot_number" in solution:
            return AntiCaptchaGeeTestV4Solution(
                captcha_id=str(solution.get("captcha_id", "")),
                lot_number=str(solution.get("lot_number", "")),
                pass_token=str(solution.get("pass_token", "")),
                gen_time=str(solution.get("gen_time", "")),
                captcha_output=str(solution.get("captcha_output", "")),
            )
        if {"challenge", "validate", "seccode"} <= set(solution):
            return AntiCaptchaGeeTestV3Solution(
                challenge=str(solution["challenge"]),
                validate=str(solution["validate"]),
                seccode=str(solution["seccode"]),
            )
        if "score" in solution:
            score = solution.get("score")
            return AntiCaptchaRecaptchaV3Solution(
                token=str(g_response or token or ""),
                score=float(score) if score is not None else None,
                action=(
                    str(solution["action"])
                    if solution.get("action") is not None
                    else None
                ),
            )
        if g_response:
            return AntiCaptchaRecaptchaV2Solution(
                str(g_response), user_agent=user_agent, resp_key=resp_key
            )
        if "text" in solution:
            return AntiCaptchaImageSolution(str(solution["text"]))
        if token:
            return AntiCaptchaHCaptchaSolution(
                str(token), user_agent=user_agent, resp_key=resp_key
            )
        raise EmptySolutionError(
            f"unrecognized anti-captcha solution shape: keys={sorted(solution)}"
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


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = ["AntiCaptchaAdapter"]
