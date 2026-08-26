"""FunCaptcha challenge kind base (ADR-0048, ADR-0064, ADR-0070)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.funcaptcha import FunCaptchaSolution


@dataclass(frozen=True, slots=True)
class FunCaptchaChallenge(BaseChallenge):
    """Arkose Labs FunCaptcha challenge (ADR-0066 call style)."""

    public_key: str = field(kw_only=True)
    pageurl: str = field(kw_only=True)
    solution_type: ClassVar[type[BaseSolution]] = FunCaptchaSolution

    def __post_init__(self) -> None:
        if not self.public_key:
            raise InvalidChallengeError(
                "FunCaptchaChallenge.public_key must be a non-empty string"
            )
        if not self.pageurl:
            raise InvalidChallengeError(
                "FunCaptchaChallenge.pageurl must be a non-empty string"
            )


__all__ = ["FunCaptchaChallenge"]
