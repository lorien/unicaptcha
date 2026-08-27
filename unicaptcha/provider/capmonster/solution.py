"""Concrete CapMonster solutions (ADR-0035, ADR-0056).

CapMonster returns raw ``solution`` dicts with no worker-context extras
(the SDK performs no userAgent/respKey capture), so subclasses add no
fields.
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
class CapMonsterImageSolution(ImageSolution):
    """Solved image captcha text."""


@dataclass(frozen=True, slots=True)
class CapMonsterRecaptchaV2Solution(RecaptchaV2Solution):
    """Solved reCAPTCHA v2 token."""


@dataclass(frozen=True, slots=True)
class CapMonsterRecaptchaV3Solution(RecaptchaV3Solution):
    """Solved reCAPTCHA v3 token."""


@dataclass(frozen=True, slots=True)
class CapMonsterHCaptchaSolution(HCaptchaSolution):
    """Solved hCaptcha token."""


@dataclass(frozen=True, slots=True)
class CapMonsterFunCaptchaSolution(FunCaptchaSolution):
    """Solved Arkose Labs FunCaptcha token."""


@dataclass(frozen=True, slots=True)
class CapMonsterGeeTestV3Solution(GeeTestV3Solution):
    """Solved GeeTest v3 three-part answer."""


@dataclass(frozen=True, slots=True)
class CapMonsterGeeTestV4Solution(GeeTestV4Solution):
    """Solved GeeTest v4 five-part answer."""


@dataclass(frozen=True, slots=True)
class CapMonsterTurnstileSolution(TurnstileSolution):
    """Solved Cloudflare Turnstile token."""


__all__ = [
    "CapMonsterFunCaptchaSolution",
    "CapMonsterGeeTestV3Solution",
    "CapMonsterGeeTestV4Solution",
    "CapMonsterHCaptchaSolution",
    "CapMonsterImageSolution",
    "CapMonsterRecaptchaV2Solution",
    "CapMonsterRecaptchaV3Solution",
    "CapMonsterTurnstileSolution",
]
