"""Concrete Anti-Captcha solutions (ADR-0035, ADR-0056).

Every solve returns a concrete subclass; the kind bases stay
non-instantiable. Token kinds that Anti-Captcha answers with worker
context carry optional ``user_agent``/``resp_key`` extras (the SDK
captures ``solution["userAgent"]`` and, for reCAPTCHA v2/hCaptcha,
``solution["respKey"]``).
"""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha._internal.repr import truncate_token
from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.solution.recaptcha_v3 import RecaptchaV3Solution
from unicaptcha.solution.text import TextSolution
from unicaptcha.solution.turnstile import TurnstileSolution


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaImageSolution(ImageSolution):
    """Solved image captcha text."""


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaTextSolution(TextSolution):
    """Solved question-captcha answer text."""


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaRecaptchaV2Solution(RecaptchaV2Solution):
    """Solved reCAPTCHA v2 token with worker context.

    ``user_agent`` mirrors the response's ``userAgent`` (tokens can be
    UA-bound); ``resp_key`` carries the response's ``respKey`` when the
    provider returns one.
    """

    user_agent: str | None = None
    resp_key: str | None = None

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(token={truncate_token(self.token)!r}, "
            f"user_agent={self.user_agent!r}, resp_key={self.resp_key!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaRecaptchaV3Solution(RecaptchaV3Solution):
    """Solved reCAPTCHA v3 token."""


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaHCaptchaSolution(HCaptchaSolution):
    """Solved hCaptcha token with worker context."""

    user_agent: str | None = None
    resp_key: str | None = None

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(token={truncate_token(self.token)!r}, "
            f"user_agent={self.user_agent!r}, resp_key={self.resp_key!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaFunCaptchaSolution(FunCaptchaSolution):
    """Solved Arkose Labs FunCaptcha token."""


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaGeeTestV3Solution(GeeTestV3Solution):
    """Solved GeeTest v3 three-part answer."""


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaGeeTestV4Solution(GeeTestV4Solution):
    """Solved GeeTest v4 five-part answer."""


@dataclass(frozen=True, slots=True, repr=False)
class AntiCaptchaTurnstileSolution(TurnstileSolution):
    """Solved Cloudflare Turnstile token."""


__all__ = [
    "AntiCaptchaFunCaptchaSolution",
    "AntiCaptchaGeeTestV3Solution",
    "AntiCaptchaGeeTestV4Solution",
    "AntiCaptchaHCaptchaSolution",
    "AntiCaptchaImageSolution",
    "AntiCaptchaRecaptchaV2Solution",
    "AntiCaptchaRecaptchaV3Solution",
    "AntiCaptchaTextSolution",
    "AntiCaptchaTurnstileSolution",
]
