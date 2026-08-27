"""Concrete Capsolver challenges (ADR-0006, ADR-0076 Capsolver table).

Capsolver's official SDK is dict-driven (no task classes); field mapping
here follows the live docs (2026) and the SDK's ``SUPPORT_TASK_TYPE`` list.
Task-type strings are proxyless/proxy-conditional (``ProxyLess`` suffix)
except Turnstile's fixed ``AntiTurnstileTaskProxyLess`` and the
recognition ``ImageToTextTask``.
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
from unicaptcha.provider.capsolver.solution import CapsolverRecaptchaV3Solution
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.types import Proxy


@dataclass(frozen=True, slots=True)
class CapsolverImageChallenge(ImageChallenge):
    """OCR image task. Returns its result inline (instant, ADR-0075);
    proxyless — recognition tasks take no proxy."""

    module: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = ImageSolution


@dataclass(frozen=True, slots=True)
class CapsolverRecaptchaV2Challenge(RecaptchaV2Challenge):
    """reCAPTCHA v2. ``action`` maps to Capsolver's ``pageAction`` (the
    ``sa`` payload value). Enterprise is a separate task type."""

    action: str | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = RecaptchaV2Solution


@dataclass(frozen=True, slots=True)
class CapsolverRecaptchaV3Challenge(RecaptchaV3Challenge):
    """reCAPTCHA v3. Proxyless-only; Capsolver exposes no v3-enterprise
    task type, so ``is_enterprise`` is rejected."""

    solution_type: ClassVar[type[BaseSolution]] = CapsolverRecaptchaV3Solution

    def __post_init__(self) -> None:
        RecaptchaV3Challenge.__post_init__(self)
        if self.is_enterprise:
            raise InvalidChallengeError(
                "CapsolverRecaptchaV3Challenge: Capsolver supports no "
                "reCAPTCHA v3 enterprise task type"
            )


@dataclass(frozen=True, slots=True)
class CapsolverHCaptchaChallenge(HCaptchaChallenge):
    """hCaptcha. ``rqdata`` rides the wire ``rqdata`` field; enterprise is
    a separate task type. (Capsolver's docs nav omits hCaptcha — mapping
    follows the SDK + spec.)"""

    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = HCaptchaSolution


@dataclass(frozen=True, slots=True)
class CapsolverFunCaptchaChallenge(FunCaptchaChallenge):
    """Arkose Labs FunCaptcha; only ``public_key``→``websitePublicKey``."""

    proxy: Proxy | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = FunCaptchaSolution


@dataclass(frozen=True, slots=True)
class CapsolverGeeTestV3Challenge(GeeTestV3Challenge):
    """GeeTest v3 with optional API-server subdomain."""

    api_server: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV3Solution


@dataclass(frozen=True, slots=True)
class CapsolverGeeTestV4Challenge(GeeTestV4Challenge):
    """GeeTest v4 — supported by current Capsolver docs (``captchaId`` +
    ``riskType`` top-level; the ADR-0076 exclusion was SDK-stale)."""

    risk_type: str | None = field(kw_only=True, default=None)
    api_server: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV4Solution


@dataclass(frozen=True, slots=True)
class CapsolverTurnstileChallenge(TurnstileChallenge):
    """Cloudflare Turnstile. Capsolver uses the fixed proxyless
    ``AntiTurnstileTaskProxyLess`` and ignores ``userAgent``; only
    ``action``/``c_data`` are supported (``chl_page_data`` is not
    serialized)."""

    def __post_init__(self) -> None:
        TurnstileChallenge.__post_init__(self)
        if self.chl_page_data is not None:
            raise InvalidChallengeError(
                "CapsolverTurnstileChallenge: Capsolver's Turnstile task "
                "supports action/cdata only, not chl_page_data"
            )


__all__ = [
    "CapsolverFunCaptchaChallenge",
    "CapsolverGeeTestV3Challenge",
    "CapsolverGeeTestV4Challenge",
    "CapsolverHCaptchaChallenge",
    "CapsolverImageChallenge",
    "CapsolverRecaptchaV2Challenge",
    "CapsolverRecaptchaV3Challenge",
    "CapsolverTurnstileChallenge",
]
