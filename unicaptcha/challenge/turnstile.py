"""Cloudflare Turnstile challenge kind base (ADR-0074)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.turnstile import TurnstileSolution


@dataclass(frozen=True, slots=True)
class TurnstileChallenge(BaseChallenge):
    """Cloudflare Turnstile challenge (ADR-0066 call style)."""

    sitekey: str = field(kw_only=True)
    pageurl: str = field(kw_only=True)
    action: str | None = field(kw_only=True, default=None)
    c_data: str | None = field(kw_only=True, default=None)
    chl_page_data: str | None = field(kw_only=True, default=None)
    solution_type: ClassVar[type[BaseSolution]] = TurnstileSolution

    def __post_init__(self) -> None:
        if not self.sitekey:
            raise InvalidChallengeError(
                "TurnstileChallenge.sitekey must be a non-empty string"
            )
        if not self.pageurl:
            raise InvalidChallengeError(
                "TurnstileChallenge.pageurl must be a non-empty string"
            )


__all__ = ["TurnstileChallenge"]
