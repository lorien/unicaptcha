"""Concrete 2Captcha challenges (ADR-0006, ADR-0076 2Captcha table).

Universal kind-base fields are inherited; the classes below add only the
provider-specific keyword-only extras serialized into ``createTask``
payloads by :mod:`unicaptcha.provider.twocaptcha.adapter`.
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
from unicaptcha.challenge.text import TextChallenge
from unicaptcha.challenge.turnstile import TurnstileChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.solution.recaptcha_v3 import RecaptchaV3Solution
from unicaptcha.solution.text import TextSolution
from unicaptcha.solution.turnstile import TurnstileSolution
from unicaptcha.types import Proxy


@dataclass(frozen=True, slots=True)
class TwoCaptchaImageChallenge(ImageChallenge):
    """Image captcha with 2Captcha's solving hints (ADR-0076)."""

    phrase: bool = field(kw_only=True, default=False)
    case: bool = field(kw_only=True, default=False)
    numeric: int = field(kw_only=True, default=0)
    math: bool = field(kw_only=True, default=False)
    min_len: int | None = field(kw_only=True, default=None)
    max_len: int | None = field(kw_only=True, default=None)
    lang: str | None = field(kw_only=True, default=None)
    comment: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = ImageSolution

    def __post_init__(self) -> None:
        # Explicit parent call: frozen+slots dataclass recreation breaks
        # zero-arg ``super()`` binding.
        ImageChallenge.__post_init__(self)
        if not 0 <= self.numeric <= 4:
            raise InvalidChallengeError(
                "TwoCaptchaImageChallenge.numeric must be within 0..4"
            )
        if self.min_len is not None and self.min_len < 0:
            raise InvalidChallengeError(
                "TwoCaptchaImageChallenge.min_len must be non-negative"
            )
        if self.max_len is not None and self.max_len < 0:
            raise InvalidChallengeError(
                "TwoCaptchaImageChallenge.max_len must be non-negative"
            )


@dataclass(frozen=True, slots=True)
class TwoCaptchaTextChallenge(TextChallenge):
    """Question captcha; 2Captcha maps ``lang`` onto its text task."""

    lang: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = TextSolution


@dataclass(frozen=True, slots=True)
class TwoCaptchaRecaptchaV2Challenge(RecaptchaV2Challenge):
    """reCAPTCHA v2 (optionally enterprise) with worker context."""

    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = RecaptchaV2Solution


@dataclass(frozen=True, slots=True)
class TwoCaptchaRecaptchaV3Challenge(RecaptchaV3Challenge):
    """reCAPTCHA v3 (proxy variant available on 2Captcha)."""

    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = RecaptchaV3Solution


@dataclass(frozen=True, slots=True)
class TwoCaptchaHCaptchaChallenge(HCaptchaChallenge):
    """hCaptcha with optional enterprise payload and worker context."""

    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = HCaptchaSolution


@dataclass(frozen=True, slots=True)
class TwoCaptchaFunCaptchaChallenge(FunCaptchaChallenge):
    """Arkose Labs FunCaptcha extras (ADR-0076: data blob + subdomain)."""

    data: str | None = field(kw_only=True, default=None)
    service_url: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = FunCaptchaSolution


@dataclass(frozen=True, slots=True)
class TwoCaptchaGeeTestV3Challenge(GeeTestV3Challenge):
    """GeeTest v3 with optional API-server subdomain."""

    api_server: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV3Solution


@dataclass(frozen=True, slots=True)
class TwoCaptchaGeeTestV4Challenge(GeeTestV4Challenge):
    """GeeTest v4 (``risk_type`` rides top-level, per 2Captcha docs)."""

    risk_type: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV4Solution


@dataclass(frozen=True, slots=True)
class TwoCaptchaTurnstileChallenge(TurnstileChallenge):
    """Cloudflare Turnstile with 2Captcha's worker context."""

    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = TurnstileSolution


__all__ = [
    "TwoCaptchaFunCaptchaChallenge",
    "TwoCaptchaGeeTestV3Challenge",
    "TwoCaptchaGeeTestV4Challenge",
    "TwoCaptchaHCaptchaChallenge",
    "TwoCaptchaImageChallenge",
    "TwoCaptchaRecaptchaV2Challenge",
    "TwoCaptchaRecaptchaV3Challenge",
    "TwoCaptchaTextChallenge",
    "TwoCaptchaTurnstileChallenge",
]
