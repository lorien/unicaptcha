"""Concrete CapMonster challenges (ADR-0006, ADR-0076 CapMonster table).

CapMonster is **proxyless-only** (ADR-0012): no challenge carries a proxy
field anywhere. Task types are single names (no proxyless/proxy split)
except reCAPTCHA v3's separate ``RecaptchaV3EnterpriseTask``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar

from unicaptcha.challenge.funcaptcha import FunCaptchaChallenge
from unicaptcha.challenge.geetest import GeeTestV3Challenge, GeeTestV4Challenge
from unicaptcha.challenge.hcaptcha import HCaptchaChallenge
from unicaptcha.challenge.image import ImageChallenge
from unicaptcha.challenge.recaptcha_v2 import RecaptchaV2Challenge
from unicaptcha.challenge.recaptcha_v3 import RecaptchaV3Challenge
from unicaptcha.challenge.turnstile import TurnstileChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.provider.capmonster.solution import CapMonsterRecaptchaV3Solution
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.solution.turnstile import TurnstileSolution

# Official SDK TextModules (17 values).
_CAPMONSTER_MODULES = frozenset(
    {
        "amazon",
        "botdetect",
        "facebook",
        "gmx",
        "google",
        "hotmail",
        "mailru",
        "ok",
        "oknew",
        "ramblerrus",
        "solvemedia",
        "steam",
        "vk",
        "yandex",
        "yandexnew",
        "yandexwave",
        "universal",
    }
)


@dataclass(frozen=True, slots=True)
class CapMonsterImageChallenge(ImageChallenge):
    """Image captcha with CapMonster's recognition-module hints.

    ``numeric`` accepts only 0/1 on CapMonster (unlike 2Captcha/Anti-Captcha
    where it ranges 0-4).
    """

    module_name: str | None = field(kw_only=True, default=None)
    threshold: int | None = field(kw_only=True, default=None)
    case: bool = field(kw_only=True, default=False)
    numeric: int = field(kw_only=True, default=0)
    math: bool = field(kw_only=True, default=False)
    solution_type: ClassVar[type[BaseSolution]] = ImageSolution

    def __post_init__(self) -> None:
        # Explicit parent call: frozen+slots dataclass recreation breaks
        # zero-arg ``super()`` binding.
        ImageChallenge.__post_init__(self)
        if self.module_name is not None and self.module_name not in _CAPMONSTER_MODULES:
            raise InvalidChallengeError(
                "CapMonsterImageChallenge.module_name must be one of "
                f"{sorted(_CAPMONSTER_MODULES)}"
            )
        if self.threshold is not None and not 0 <= self.threshold <= 100:
            raise InvalidChallengeError(
                "CapMonsterImageChallenge.threshold must be within 0..100"
            )
        if self.numeric not in (0, 1):
            raise InvalidChallengeError(
                "CapMonsterImageChallenge.numeric must be 0 or 1"
            )


@dataclass(frozen=True, slots=True)
class CapMonsterRecaptchaV2Challenge(RecaptchaV2Challenge):
    """reCAPTCHA v2 with CapMonster's enterprise task type and action."""

    action: str | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = RecaptchaV2Solution


@dataclass(frozen=True, slots=True)
class CapMonsterRecaptchaV3Challenge(RecaptchaV3Challenge):
    """reCAPTCHA v3. Proxyless-only; min_score validated 0.1-0.9.
    Enterprise is a separate task type on CapMonster."""

    solution_type: ClassVar[type[BaseSolution]] = CapMonsterRecaptchaV3Solution

    def __post_init__(self) -> None:
        RecaptchaV3Challenge.__post_init__(self)
        if self.min_score is not None and not 0.1 <= self.min_score <= 0.9:
            raise InvalidChallengeError(
                "CapMonsterRecaptchaV3Challenge.min_score must be within 0.1..0.9"
            )


@dataclass(frozen=True, slots=True)
class CapMonsterHCaptchaChallenge(HCaptchaChallenge):
    """hCaptcha; rqdata rides the wire ``data`` field, plus a
    fallback-UA flag."""

    fallback_to_actual_ua: bool | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = HCaptchaSolution


@dataclass(frozen=True, slots=True)
class CapMonsterFunCaptchaChallenge(FunCaptchaChallenge):
    """Arkose Labs FunCaptcha extras (data blob + subdomain)."""

    data: str | None = field(kw_only=True, default=None)
    service_url: str | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = FunCaptchaSolution


@dataclass(frozen=True, slots=True)
class CapMonsterGeeTestV3Challenge(GeeTestV3Challenge):
    """GeeTest v3 with optional API-server subdomain and get-lib script."""

    api_server: str | None = field(kw_only=True, default=None)
    geetest_lib: str | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV3Solution


@dataclass(frozen=True, slots=True)
class CapMonsterGeeTestV4Challenge(GeeTestV4Challenge):
    """GeeTest v4: the captcha id rides ``initParameters.captcha_id``
    (no ``gt`` per the pinned spec); ``risk_type`` rides
    ``initParameters.riskType``."""

    risk_type: str | None = field(kw_only=True, default=None)
    api_server: str | None = field(kw_only=True, default=None)
    geetest_lib: str | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV4Solution


@dataclass(frozen=True, slots=True)
class CapMonsterTurnstileChallenge(TurnstileChallenge):
    """Cloudflare Turnstile. v1 supports ``cloudflare_task_type="token"``
    only: ``cf_clearance``/``wait_room`` need a proxy, impossible under
    the proxyless rule (ADR-0076)."""

    cloudflare_task_type: str | None = field(kw_only=True, default=None)
    html_page_base64: str | None = field(kw_only=True, default=None)
    api_js_url: str | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = TurnstileSolution

    def __post_init__(self) -> None:
        TurnstileChallenge.__post_init__(self)
        if (
            self.cloudflare_task_type is not None
            and self.cloudflare_task_type != "token"
        ):
            raise InvalidChallengeError(
                "CapMonsterTurnstileChallenge.cloudflare_task_type supports "
                f"'token' only in v1, got {self.cloudflare_task_type!r}"
            )


__all__ = [
    "CapMonsterFunCaptchaChallenge",
    "CapMonsterGeeTestV3Challenge",
    "CapMonsterGeeTestV4Challenge",
    "CapMonsterHCaptchaChallenge",
    "CapMonsterImageChallenge",
    "CapMonsterRecaptchaV2Challenge",
    "CapMonsterRecaptchaV3Challenge",
    "CapMonsterTurnstileChallenge",
]
