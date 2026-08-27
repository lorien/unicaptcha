"""Concrete Anti-Captcha challenges (ADR-0006, ADR-0076 Anti-Captcha table).

Universal kind-base fields are inherited; the classes below add only the
provider-specific keyword-only extras serialized into ``createTask``
payloads by :mod:`unicaptcha.provider.anticaptcha.adapter`. Task types are
proxyless/proxy-conditional per the official SDK's class pairs.
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
from unicaptcha.provider.anticaptcha.solution import AntiCaptchaRecaptchaV3Solution
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.solution.text import TextSolution
from unicaptcha.solution.turnstile import TurnstileSolution
from unicaptcha.types import Proxy

_V3_SCORES = (0.5, 0.7, 0.9)


@dataclass(frozen=True, slots=True)
class AntiCaptchaImageChallenge(ImageChallenge):
    """Image captcha with Anti-Captcha's solving hints and worker pool."""

    phrase: bool = field(kw_only=True, default=False)
    case: bool = field(kw_only=True, default=False)
    numeric: int = field(kw_only=True, default=0)
    math: bool = field(kw_only=True, default=False)
    min_len: int | None = field(kw_only=True, default=None)
    max_len: int | None = field(kw_only=True, default=None)
    comment: str | None = field(kw_only=True, default=None)
    language_pool: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = ImageSolution

    def __post_init__(self) -> None:
        # Explicit parent call: frozen+slots dataclass recreation breaks
        # zero-arg ``super()`` binding.
        ImageChallenge.__post_init__(self)
        if not 0 <= self.numeric <= 4:
            raise InvalidChallengeError(
                "AntiCaptchaImageChallenge.numeric must be within 0..4"
            )
        if self.min_len is not None and self.min_len < 0:
            raise InvalidChallengeError(
                "AntiCaptchaImageChallenge.min_len must be non-negative"
            )
        if self.max_len is not None and self.max_len < 0:
            raise InvalidChallengeError(
                "AntiCaptchaImageChallenge.max_len must be non-negative"
            )


@dataclass(frozen=True, slots=True)
class AntiCaptchaTextChallenge(TextChallenge):
    """Question captcha; the API's TextCaptchaTask (absent from the
    official SDK — ``lang`` mapping verified at implementation time)."""

    lang: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = TextSolution


@dataclass(frozen=True, slots=True)
class AntiCaptchaRecaptchaV2Challenge(RecaptchaV2Challenge):
    """reCAPTCHA v2 with Anti-Captcha's stoken/data-s extras.

    Enterprise tasks drop websiteSToken/recaptchaDataSValue/isInvisible on
    the wire; ``data_s`` rides ``enterprisePayload`` there instead.
    """

    stoken: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = RecaptchaV2Solution


@dataclass(frozen=True, slots=True)
class AntiCaptchaRecaptchaV3Challenge(RecaptchaV3Challenge):
    """reCAPTCHA v3. Proxyless-only on Anti-Captcha; the wire task carries
    no userAgent/cookies fields."""

    solution_type: ClassVar[type[BaseSolution]] = AntiCaptchaRecaptchaV3Solution

    def __post_init__(self) -> None:
        RecaptchaV3Challenge.__post_init__(self)
        if self.min_score is not None and self.min_score not in _V3_SCORES:
            raise InvalidChallengeError(
                "AntiCaptchaRecaptchaV3Challenge.min_score must be one of "
                f"{', '.join(str(s) for s in _V3_SCORES)}"
            )


@dataclass(frozen=True, slots=True)
class AntiCaptchaHCaptchaChallenge(HCaptchaChallenge):
    """hCaptcha with optional enterprise payload and worker context
    (userAgent rides even proxyless)."""

    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    cookies: Mapping[str, str] | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = HCaptchaSolution


@dataclass(frozen=True, slots=True)
class AntiCaptchaFunCaptchaChallenge(FunCaptchaChallenge):
    """Arkose Labs FunCaptcha extras (ADR-0076: data blob + subdomain)."""

    data: str | None = field(kw_only=True, default=None)
    service_url: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = FunCaptchaSolution


@dataclass(frozen=True, slots=True)
class AntiCaptchaGeeTestV3Challenge(GeeTestV3Challenge):
    """GeeTest v3 with optional API-server subdomain and get-lib script."""

    api_server: str | None = field(kw_only=True, default=None)
    geetest_lib: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV3Solution


@dataclass(frozen=True, slots=True)
class AntiCaptchaGeeTestV4Challenge(GeeTestV4Challenge):
    """GeeTest v4: the captcha id rides ``gt``; ``risk_type`` lives in
    ``initParameters`` per the official SDK."""

    risk_type: str | None = field(kw_only=True, default=None)
    api_server: str | None = field(kw_only=True, default=None)
    proxy: Proxy | None = field(kw_only=True, default=None)
    user_agent: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV4Solution


@dataclass(frozen=True, slots=True)
class AntiCaptchaTurnstileChallenge(TurnstileChallenge):
    """Cloudflare Turnstile. The SDK sends ``isInvisible`` on proxy-on
    tasks only; no universal field exists for it, so it stays unset."""

    proxy: Proxy | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = TurnstileSolution


__all__ = [
    "AntiCaptchaFunCaptchaChallenge",
    "AntiCaptchaGeeTestV3Challenge",
    "AntiCaptchaGeeTestV4Challenge",
    "AntiCaptchaHCaptchaChallenge",
    "AntiCaptchaImageChallenge",
    "AntiCaptchaRecaptchaV2Challenge",
    "AntiCaptchaRecaptchaV3Challenge",
    "AntiCaptchaTextChallenge",
    "AntiCaptchaTurnstileChallenge",
]
