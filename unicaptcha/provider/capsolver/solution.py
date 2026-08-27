"""Concrete Capsolver solutions (ADR-0035, ADR-0056).

Capsolver returns raw ``solution`` dicts; the SDK performs no
worker-context capture, so subclasses add no fields.
"""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.solution.recaptcha_v3 import RecaptchaV3Solution
from unicaptcha.solution.turnstile import TurnstileSolution


@dataclass(frozen=True, slots=True)
class CapsolverImageSolution(ImageSolution):
    """Solved image captcha text."""


@dataclass(frozen=True, slots=True)
class CapsolverRecaptchaV2Solution(RecaptchaV2Solution):
    """Solved reCAPTCHA v2 token."""


@dataclass(frozen=True, slots=True)
class CapsolverRecaptchaV3Solution(RecaptchaV3Solution):
    """Solved reCAPTCHA v3 token."""


@dataclass(frozen=True, slots=True)
class CapsolverHCaptchaSolution(HCaptchaSolution):
    """Solved hCaptcha token."""


@dataclass(frozen=True, slots=True)
class CapsolverFunCaptchaSolution(FunCaptchaSolution):
    """Solved Arkose Labs FunCaptcha token."""


@dataclass(frozen=True, slots=True)
class CapsolverGeeTestV3Solution(GeeTestV3Solution):
    """Solved GeeTest v3 three-part answer."""


@dataclass(frozen=True, slots=True)
class CapsolverGeeTestV4Solution(GeeTestV4Solution):
    """Solved GeeTest v4 five-part answer."""


@dataclass(frozen=True, slots=True)
class CapsolverTurnstileSolution(TurnstileSolution):
    """Solved Cloudflare Turnstile token."""


__all__ = [
    "CapsolverFunCaptchaSolution",
    "CapsolverGeeTestV3Solution",
    "CapsolverGeeTestV4Solution",
    "CapsolverHCaptchaSolution",
    "CapsolverImageSolution",
    "CapsolverRecaptchaV2Solution",
    "CapsolverRecaptchaV3Solution",
    "CapsolverTurnstileSolution",
]
