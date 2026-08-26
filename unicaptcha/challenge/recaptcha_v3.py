"""reCAPTCHA v3 challenge kind base (ADR-0048, ADR-0064, ADR-0070)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.recaptcha_v3 import RecaptchaV3Solution


@dataclass(frozen=True, slots=True)
class RecaptchaV3Challenge(BaseChallenge):
    """reCAPTCHA v3 score-based captcha (ADR-0066 call style)."""

    sitekey: str = field(kw_only=True)
    pageurl: str = field(kw_only=True)
    action: str | None = field(kw_only=True, default=None)
    min_score: float | None = field(kw_only=True, default=None)
    is_enterprise: bool = field(kw_only=True, default=False)
    data_s: Mapping[str, str] | None = field(kw_only=True, default=None)
    api_domain: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = RecaptchaV3Solution

    def __post_init__(self) -> None:
        if not self.sitekey:
            raise InvalidChallengeError(
                "RecaptchaV3Challenge.sitekey must be a non-empty string"
            )
        if not self.pageurl:
            raise InvalidChallengeError(
                "RecaptchaV3Challenge.pageurl must be a non-empty string"
            )


__all__ = ["RecaptchaV3Challenge"]
