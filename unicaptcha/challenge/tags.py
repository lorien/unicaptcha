"""Challenge-kind tags: the single public source of truth for kind names.

``KIND_TAGS`` maps each kind base to its stable tag string (used by
``unicaptcha.detect`` signals and the client capability introspection
API, e.g. ``Solver.supports("hcaptcha")``); ``TAG_KINDS`` is the reverse
lookup. Nine kinds, in stable definition order.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.challenge.funcaptcha import FunCaptchaChallenge
from unicaptcha.challenge.geetest import GeeTestV3Challenge, GeeTestV4Challenge
from unicaptcha.challenge.hcaptcha import HCaptchaChallenge
from unicaptcha.challenge.image import ImageChallenge
from unicaptcha.challenge.recaptcha_v2 import RecaptchaV2Challenge
from unicaptcha.challenge.recaptcha_v3 import RecaptchaV3Challenge
from unicaptcha.challenge.text import TextChallenge
from unicaptcha.challenge.turnstile import TurnstileChallenge

KIND_TAGS: Final[Mapping[type[BaseChallenge], str]] = MappingProxyType(
    {
        ImageChallenge: "image",
        TextChallenge: "text",
        RecaptchaV2Challenge: "recaptcha-v2",
        RecaptchaV3Challenge: "recaptcha-v3",
        HCaptchaChallenge: "hcaptcha",
        FunCaptchaChallenge: "funcaptcha",
        GeeTestV3Challenge: "geetest-v3",
        GeeTestV4Challenge: "geetest-v4",
        TurnstileChallenge: "turnstile",
    }
)

TAG_KINDS: Final[Mapping[str, type[BaseChallenge]]] = MappingProxyType(
    {tag: kind for kind, tag in KIND_TAGS.items()}
)

__all__ = ["KIND_TAGS", "TAG_KINDS"]
