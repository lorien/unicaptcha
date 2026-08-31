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
from collections.abc import Mapping
from typing import Any, ClassVar, cast

from unicaptcha.adapter import JsonAdapterBase
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import (
    EmptySolutionError,
    ErrorKind,
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


class CapMonsterAdapter(JsonAdapterBase):
    """Adapter speaking CapMonster Cloud's createTask/getTaskResult API."""

    provider: ClassVar[str] = "capmonster"
    json_provider: ClassVar[str] = "capmonster"
    error_kinds: ClassVar[Mapping[str, ErrorKind]] = {
        "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
        "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
        "ERROR_IP_NOT_ALLOWED": ErrorKind.AUTHENTICATION,
        "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
        "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
        "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
    }
    unknown_task_codes: ClassVar[frozenset[str]] = frozenset(
        {"ERROR_TASK_ABSENT", "ERROR_WRONG_CAPTCHA_ID", "ERROR_TASK_NOT_FOUND"}
    )
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
                    "s": self._single_token("data_s", dict(ch.data_s))
                }
            if ch.api_domain is not None:
                task["apiDomain"] = ch.api_domain
            if ch.action is not None:
                task["pageAction"] = ch.action
            if ch.user_agent is not None:
                task["userAgent"] = ch.user_agent
            cookie_header = self._cookies(ch.cookies)
            if cookie_header is not None:
                task["cookies"] = cookie_header
            return task
        task = {
            "type": "RecaptchaV2Task",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.data_s:
            task["recaptchaDataSValue"] = self._single_token("data_s", dict(ch.data_s))
        if ch.invisible:
            task["isInvisible"] = True
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = self._cookies(ch.cookies)
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
        cookie_header = self._cookies(ch.cookies)
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
        cookie_header = self._cookies(ch.cookies)
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
        # Vendor-derived (fidelity.md, 2026-08-28): CapMonster's SDK model
        # requires `gt` unconditionally and its v4 example passes the
        # challenge id there; initParameters carries extras (riskType) only.
        task: dict[str, Any] = {
            "type": "GeeTestTask",
            "websiteURL": ch.pageurl,
            "gt": ch.captcha_id,
            "version": 4,
        }
        if ch.risk_type is not None:
            task["initParameters"] = {"riskType": ch.risk_type}
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

    # -- solution dispatch --------------------------------------------------

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


__all__ = ["CapMonsterAdapter"]
