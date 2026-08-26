"""hCaptcha challenge kind base (ADR-0048, ADR-0064, ADR-0070)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.hcaptcha import HCaptchaSolution


@dataclass(frozen=True, slots=True)
class HCaptchaChallenge(BaseChallenge):
    """hCaptcha challenge (ADR-0066 call style)."""

    sitekey: str = field(kw_only=True)
    pageurl: str = field(kw_only=True)
    is_invisible: bool = field(kw_only=True, default=False)
    rqdata: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = HCaptchaSolution

    def __post_init__(self) -> None:
        if not self.sitekey:
            raise InvalidChallengeError(
                "HCaptchaChallenge.sitekey must be a non-empty string"
            )
        if not self.pageurl:
            raise InvalidChallengeError(
                "HCaptchaChallenge.pageurl must be a non-empty string"
            )


__all__ = ["HCaptchaChallenge"]
