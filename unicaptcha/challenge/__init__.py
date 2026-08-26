"""Abstract challenge kind bases (ADR-0048, ADR-0064)."""

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.challenge.funcaptcha import FunCaptchaChallenge
from unicaptcha.challenge.geetest import GeeTestV3Challenge, GeeTestV4Challenge
from unicaptcha.challenge.hcaptcha import HCaptchaChallenge
from unicaptcha.challenge.image import ImageChallenge
from unicaptcha.challenge.recaptcha_v2 import RecaptchaV2Challenge
from unicaptcha.challenge.recaptcha_v3 import RecaptchaV3Challenge
from unicaptcha.challenge.text import TextChallenge
from unicaptcha.challenge.turnstile import TurnstileChallenge

__all__ = [
    "BaseChallenge",
    "FunCaptchaChallenge",
    "GeeTestV3Challenge",
    "GeeTestV4Challenge",
    "HCaptchaChallenge",
    "ImageChallenge",
    "RecaptchaV2Challenge",
    "RecaptchaV3Challenge",
    "TextChallenge",
    "TurnstileChallenge",
]
