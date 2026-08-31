"""The Anti-Captcha adapter (``createTask``/``getTaskResult`` JSON API).

Pure translation unit (ADR-0041): challenge → request payload, response
bytes → typed objects, provider error codes → the library error hierarchy.
Field mapping per architecture §2 as verified against the official SDK
clone (`var/vendor/repo/anticaptcha-python`, task-12 cross-check).

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
from collections.abc import Mapping
from typing import Any, ClassVar, cast

from unicaptcha.adapter import JsonAdapterBase
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import (
    EmptySolutionError,
    ErrorKind,
    InvalidChallengeError,
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
from unicaptcha.types import Proxy


class AntiCaptchaAdapter(JsonAdapterBase):
    """Adapter speaking Anti-Captcha's createTask/getTaskResult API."""

    provider: ClassVar[str] = "anti-captcha"
    json_provider: ClassVar[str] = "anti-captcha"
    error_kinds: ClassVar[Mapping[str, ErrorKind]] = {
        "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
        "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
        "ERROR_IP_NOT_ALLOWED": ErrorKind.AUTHENTICATION,
        "ERROR_IP_BANNED": ErrorKind.AUTHENTICATION,
        "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
        "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
        "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
    }
    unknown_task_codes: ClassVar[frozenset[str]] = frozenset(
        {"ERROR_TASK_ABSENT", "ERROR_WRONG_CAPTCHA_ID", "ERROR_TASK_NOT_FOUND"}
    )
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

    def _proxy_fields(self, proxy: Proxy | None) -> dict[str, Any]:
        """Serialize the five-field proxy block. Anti-Captcha accepts IP
        addresses only (ADR-0076); hostnames are rejected here — pure code,
        no DNS resolution."""
        if proxy is None:
            return {}
        try:
            ipaddress.ip_address(proxy.host)
        except ValueError as exc:
            raise InvalidChallengeError(
                f"anti-captcha accepts proxy IP addresses only, "
                f"got hostname {proxy.host!r}"
            ) from exc
        return super()._proxy_fields(proxy)

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
            cookie_header = self._cookies(ch.cookies)
            if cookie_header is not None:
                task["cookies"] = cookie_header
            task.update(self._proxy_fields(ch.proxy))
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
            task["recaptchaDataSValue"] = self._single_token("data_s", dict(ch.data_s))
        if ch.invisible:
            task["isInvisible"] = True
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = self._cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        task.update(self._proxy_fields(ch.proxy))
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
        cookie_header = self._cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        task.update(self._proxy_fields(ch.proxy))
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
        task.update(self._proxy_fields(ch.proxy))
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
        task.update(self._proxy_fields(ch.proxy))
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
        task.update(self._proxy_fields(ch.proxy))
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
        task.update(self._proxy_fields(ch.proxy))
        return task

    # -- solution dispatch --------------------------------------------------

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


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = ["AntiCaptchaAdapter"]
