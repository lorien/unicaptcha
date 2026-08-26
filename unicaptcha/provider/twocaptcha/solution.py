"""Concrete 2Captcha solutions (ADR-0035, ADR-0056).

Every solve returns a concrete subclass; the kind bases stay
non-instantiable. Subclasses add no fields — 2Captcha's answer shapes map
onto the universal fields exactly (architecture §3).
"""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.solution.recaptcha_v3 import RecaptchaV3Solution
from unicaptcha.solution.text import TextSolution
from unicaptcha.solution.turnstile import TurnstileSolution


@dataclass(frozen=True, slots=True)
class TwoCaptchaImageSolution(ImageSolution):
    """Solved image captcha text."""


@dataclass(frozen=True, slots=True)
class TwoCaptchaTextSolution(TextSolution):
    """Solved question-captcha answer text."""


@dataclass(frozen=True, slots=True)
class TwoCaptchaRecaptchaV2Solution(RecaptchaV2Solution):
    """Solved reCAPTCHA v2 token."""


@dataclass(frozen=True, slots=True)
class TwoCaptchaRecaptchaV3Solution(RecaptchaV3Solution):
    """Solved reCAPTCHA v3 token with score/action when reported."""


@dataclass(frozen=True, slots=True)
class TwoCaptchaHCaptchaSolution(HCaptchaSolution):
    """Solved hCaptcha token."""


@dataclass(frozen=True, slots=True)
class TwoCaptchaFunCaptchaSolution(FunCaptchaSolution):
    """Solved Arkose Labs FunCaptcha token."""


@dataclass(frozen=True, slots=True)
class TwoCaptchaGeeTestV3Solution(GeeTestV3Solution):
    """Solved GeeTest v3 three-part answer."""


@dataclass(frozen=True, slots=True)
class TwoCaptchaGeeTestV4Solution(GeeTestV4Solution):
    """Solved GeeTest v4 five-part answer."""


@dataclass(frozen=True, slots=True)
class TwoCaptchaTurnstileSolution(TurnstileSolution):
    """Solved Cloudflare Turnstile token."""


__all__ = [
    "TwoCaptchaFunCaptchaSolution",
    "TwoCaptchaGeeTestV3Solution",
    "TwoCaptchaGeeTestV4Solution",
    "TwoCaptchaHCaptchaSolution",
    "TwoCaptchaImageSolution",
    "TwoCaptchaRecaptchaV2Solution",
    "TwoCaptchaRecaptchaV3Solution",
    "TwoCaptchaTextSolution",
    "TwoCaptchaTurnstileSolution",
]
