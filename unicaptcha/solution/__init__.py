"""Abstract solution kind bases (ADR-0035, ADR-0056)."""

from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.image import ImageSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.solution.recaptcha_v3 import RecaptchaV3Solution
from unicaptcha.solution.text import TextSolution
from unicaptcha.solution.turnstile import TurnstileSolution

__all__ = [
    "BaseSolution",
    "FunCaptchaSolution",
    "GeeTestV3Solution",
    "GeeTestV4Solution",
    "HCaptchaSolution",
    "ImageSolution",
    "RecaptchaV2Solution",
    "RecaptchaV3Solution",
    "TextSolution",
    "TurnstileSolution",
]
