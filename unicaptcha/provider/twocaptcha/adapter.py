"""The 2Captcha adapter (modern JSON API, ``createTask``/``getTaskResult``).

Pure translation unit (ADR-0041): challenge → request payload, response
bytes → typed objects, provider error codes → the library error hierarchy.
Field mapping follows architecture §2 as amended by live API verification
(``minLength``/``maxLength`` wire names; GeeTest v4 via ``version`` +
``initParameters``; reports on ``/reportCorrect``/``/reportIncorrect``).
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
    error_from_kind,
)
from unicaptcha.provider.twocaptcha.challenge import (
    TwoCaptchaFunCaptchaChallenge,
    TwoCaptchaGeeTestV3Challenge,
    TwoCaptchaGeeTestV4Challenge,
    TwoCaptchaHCaptchaChallenge,
    TwoCaptchaImageChallenge,
    TwoCaptchaRecaptchaV2Challenge,
    TwoCaptchaRecaptchaV3Challenge,
    TwoCaptchaTextChallenge,
    TwoCaptchaTurnstileChallenge,
)
from unicaptcha.provider.twocaptcha.solution import (
    TwoCaptchaGeeTestV3Solution,
    TwoCaptchaGeeTestV4Solution,
    TwoCaptchaHCaptchaSolution,
    TwoCaptchaImageSolution,
    TwoCaptchaRecaptchaV2Solution,
    TwoCaptchaRecaptchaV3Solution,
)
from unicaptcha.types import TaskRef


class TwoCaptchaAdapter(JsonAdapterBase):
    """Adapter speaking 2Captcha's modern JSON API."""

    provider: ClassVar[str] = "twocaptcha"
    json_provider: ClassVar[str] = "2captcha"
    error_kinds: ClassVar[Mapping[str, ErrorKind]] = {
        "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
        "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
        "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
        "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
        "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
    }
    unknown_task_codes: ClassVar[frozenset[str]] = frozenset(
        {"ERROR_TASK_NOT_FOUND", "ERROR_TASK_ABSENT", "ERROR_WRONG_TASK_ID"}
    )
    challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset(
        {
            TwoCaptchaImageChallenge,
            TwoCaptchaTextChallenge,
            TwoCaptchaRecaptchaV2Challenge,
            TwoCaptchaRecaptchaV3Challenge,
            TwoCaptchaHCaptchaChallenge,
            TwoCaptchaFunCaptchaChallenge,
            TwoCaptchaGeeTestV3Challenge,
            TwoCaptchaGeeTestV4Challenge,
            TwoCaptchaTurnstileChallenge,
        }
    )
    default_base_url: ClassVar[str] = "https://api.2captcha.com"

    # -- submit ----------------------------------------------------------

    def _extra_envelope(self, challenge: BaseChallenge) -> dict[str, Any]:
        # Envelope-level worker-pool hint (2Captcha-only field).
        language_pool = getattr(challenge, "language_pool", None)
        if language_pool is None:
            return {}
        return {"languagePool": language_pool}

    def _build_task(self, challenge: BaseChallenge) -> dict[str, Any]:
        for task_type in (TwoCaptchaImageChallenge,):
            if isinstance(challenge, task_type):
                return self._image_task(challenge)
        if isinstance(challenge, TwoCaptchaTextChallenge):
            return self._text_task(challenge)
        if isinstance(challenge, TwoCaptchaRecaptchaV2Challenge):
            return self._recaptcha_v2_task(challenge)
        if isinstance(challenge, TwoCaptchaRecaptchaV3Challenge):
            return self._recaptcha_v3_task(challenge)
        if isinstance(challenge, TwoCaptchaHCaptchaChallenge):
            return self._hcaptcha_task(challenge)
        if isinstance(challenge, TwoCaptchaFunCaptchaChallenge):
            return self._funcaptcha_task(challenge)
        if isinstance(challenge, TwoCaptchaGeeTestV3Challenge):
            return self._geetest_v3_task(challenge)
        if isinstance(challenge, TwoCaptchaGeeTestV4Challenge):
            return self._geetest_v4_task(challenge)
        if isinstance(challenge, TwoCaptchaTurnstileChallenge):
            return self._turnstile_task(challenge)
        raise UnsupportedChallengeError(
            f"TwoCaptchaAdapter does not support {type(challenge).__name__}"
        )

    def _image_task(self, ch: TwoCaptchaImageChallenge) -> dict[str, Any]:
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
        return task

    def _text_task(self, ch: TwoCaptchaTextChallenge) -> dict[str, Any]:
        return {"type": "TextCaptchaTask", "comment": ch.text}

    def _recaptcha_v2_task(self, ch: TwoCaptchaRecaptchaV2Challenge) -> dict[str, Any]:
        base = "RecaptchaV2EnterpriseTask" if ch.is_enterprise else "RecaptchaV2Task"
        task: dict[str, Any] = {
            "type": base if ch.proxy is not None else base + "Proxyless",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.is_enterprise:
            enterprise_payload: dict[str, str] = dict(ch.data_s) if ch.data_s else {}
            if enterprise_payload:
                task["enterprisePayload"] = enterprise_payload
        elif ch.data_s:
            task["recaptchaDataSValue"] = self._single_token("data_s", dict(ch.data_s))
        if ch.invisible:
            task["isInvisible"] = True
        if ch.api_domain is not None:
            task["apiDomain"] = ch.api_domain
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = self._cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        task.update(self._proxy_fields(ch.proxy))
        return task

    def _recaptcha_v3_task(self, ch: TwoCaptchaRecaptchaV3Challenge) -> dict[str, Any]:
        # 2Captcha documents RecaptchaV3TaskProxyless only — v3 is
        # proxyless-only, and carries no userAgent/cookies fields.
        task: dict[str, Any] = {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.action is not None:
            task["pageAction"] = ch.action
        if ch.min_score is not None:
            task["minScore"] = ch.min_score
        if ch.is_enterprise:
            task["isEnterprise"] = True
        if ch.api_domain is not None:
            task["apiDomain"] = ch.api_domain
        return task

    def _hcaptcha_task(self, ch: TwoCaptchaHCaptchaChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": "HCaptchaTask" if ch.proxy is not None else "HCaptchaTaskProxyless",
            "websiteURL": ch.pageurl,
            "websiteKey": ch.sitekey,
        }
        if ch.is_invisible:
            task["isInvisible"] = True
        if ch.rqdata is not None:
            task["enterprisePayload"] = {"rqdata": ch.rqdata}
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        cookie_header = self._cookies(ch.cookies)
        if cookie_header is not None:
            task["cookies"] = cookie_header
        task.update(self._proxy_fields(ch.proxy))
        return task

    def _funcaptcha_task(self, ch: TwoCaptchaFunCaptchaChallenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": (
                "FunCaptchaTask" if ch.proxy is not None else "FunCaptchaTaskProxyless"
            ),
            "websiteURL": ch.pageurl,
            "websitePublicKey": ch.public_key,
        }
        if ch.data is not None:
            task["data"] = ch.data
        if ch.service_url is not None:
            task["funcaptchaApiJSSubdomain"] = ch.service_url
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        task.update(self._proxy_fields(ch.proxy))
        return task

    def _geetest_v3_task(self, ch: TwoCaptchaGeeTestV3Challenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": "GeeTestTask" if ch.proxy is not None else "GeeTestTaskProxyless",
            "websiteURL": ch.pageurl,
            "gt": ch.gt_key,
            "challenge": ch.challenge,
        }
        if ch.api_server is not None:
            task["geetestApiServerSubdomain"] = ch.api_server
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        task.update(self._proxy_fields(ch.proxy))
        return task

    def _geetest_v4_task(self, ch: TwoCaptchaGeeTestV4Challenge) -> dict[str, Any]:
        task: dict[str, Any] = {
            "type": "GeeTestTask" if ch.proxy is not None else "GeeTestTaskProxyless",
            "websiteURL": ch.pageurl,
            "version": 4,
            "initParameters": {"captcha_id": ch.captcha_id},
        }
        if ch.risk_type is not None:
            task["risk_type"] = ch.risk_type
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        task.update(self._proxy_fields(ch.proxy))
        return task

    def _turnstile_task(self, ch: TwoCaptchaTurnstileChallenge) -> dict[str, Any]:
        # Wire names are lowercase per the live docs: `data` (cData value)
        # and `pagedata` (chlPageData value).
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
            task["data"] = ch.c_data
        if ch.chl_page_data is not None:
            task["pagedata"] = ch.chl_page_data
        if ch.user_agent is not None:
            task["userAgent"] = ch.user_agent
        task.update(self._proxy_fields(ch.proxy))
        return task

    # -- report pairs (ADR-0068; modern /reportCorrect|reportIncorrect) ----

    def report_bad_supported(self, challenge_type: type[BaseChallenge]) -> bool:
        return True

    def build_report_bad(self, task: TaskRef) -> dict[str, Any]:
        return {
            "clientKey": self._api_key.get_secret_value(),
            "taskId": task.task_id,
        }

    def parse_report_bad(self, raw: bytes) -> bool:
        return self._parse_report(raw)

    def report_good_supported(self, challenge_type: type[BaseChallenge]) -> bool:
        return True

    def build_report_good(self, task: TaskRef) -> dict[str, Any]:
        return {
            "clientKey": self._api_key.get_secret_value(),
            "taskId": task.task_id,
        }

    def parse_report_good(self, raw: bytes) -> bool:
        return self._parse_report(raw)

    # -- private helpers ---------------------------------------------------

    def _parse_report(self, raw: bytes) -> bool:
        data = self._decode(raw)
        if data.get("errorId"):
            kind, message = self.map_provider_error(raw)
            raise error_from_kind(kind, message, raw)
        return data.get("status") == "success"

    def _solution_from(self, solution: dict[str, Any]) -> Any:
        g_response = solution.get("gRecaptchaResponse")
        token = solution.get("token")
        if "captcha_output" in solution and "lot_number" in solution:
            return TwoCaptchaGeeTestV4Solution(
                captcha_id=str(solution.get("captcha_id", "")),
                lot_number=str(solution.get("lot_number", "")),
                pass_token=str(solution.get("pass_token", "")),
                gen_time=str(solution.get("gen_time", "")),
                captcha_output=str(solution.get("captcha_output", "")),
            )
        if {"challenge", "validate", "seccode"} <= set(solution):
            return TwoCaptchaGeeTestV3Solution(
                challenge=str(solution["challenge"]),
                validate=str(solution["validate"]),
                seccode=str(solution["seccode"]),
            )
        if "score" in solution:
            score = solution.get("score")
            return TwoCaptchaRecaptchaV3Solution(
                token=str(g_response or token or ""),
                score=float(score) if score is not None else None,
                action=(
                    str(solution["action"])
                    if solution.get("action") is not None
                    else None
                ),
            )
        if g_response and token:
            # Live-verified (fidelity pass 2026-08-28): the v3 solution
            # shape is gRecaptchaResponse + token WITHOUT a score field;
            # v2 responses carry gRecaptchaResponse only.
            return TwoCaptchaRecaptchaV3Solution(
                token=str(g_response), score=None, action=None
            )
        if g_response:
            return TwoCaptchaRecaptchaV2Solution(str(g_response))
        if "text" in solution:
            return TwoCaptchaImageSolution(str(solution["text"]))
        if token:
            return TwoCaptchaHCaptchaSolution(str(token))
        raise EmptySolutionError(
            f"unrecognized 2captcha solution shape: keys={sorted(solution)}"
        )


__all__ = ["TwoCaptchaAdapter"]
