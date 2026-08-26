"""reCAPTCHA v2 challenge kind base (ADR-0048, ADR-0064, ADR-0070)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution


@dataclass(frozen=True, slots=True)
class RecaptchaV2Challenge(BaseChallenge):
    """reCAPTCHA v2 (checkbox/invisible) captcha (ADR-0066 call style)."""

    sitekey: str = field(kw_only=True)
    pageurl: str = field(kw_only=True)
    invisible: bool = field(kw_only=True, default=False)
    is_enterprise: bool = field(kw_only=True, default=False)
    data_s: Mapping[str, str] | None = field(kw_only=True, default=None)
    api_domain: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = RecaptchaV2Solution

    def __post_init__(self) -> None:
        if not self.sitekey:
            raise InvalidChallengeError(
                "RecaptchaV2Challenge.sitekey must be a non-empty string"
            )
        if not self.pageurl:
            raise InvalidChallengeError(
                "RecaptchaV2Challenge.pageurl must be a non-empty string"
            )


__all__ = ["RecaptchaV2Challenge"]
