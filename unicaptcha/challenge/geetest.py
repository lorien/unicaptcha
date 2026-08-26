"""GeeTest v3/v4 challenge kind bases (ADR-0048, ADR-0064, ADR-0070)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution


@dataclass(frozen=True, slots=True)
class GeeTestV3Challenge(BaseChallenge):
    """GeeTest v3 (slider/puzzle) challenge (ADR-0066 call style)."""

    gt_key: str = field(kw_only=True)
    challenge: str = field(kw_only=True)
    pageurl: str = field(kw_only=True)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV3Solution

    def __post_init__(self) -> None:
        for name in ("gt_key", "challenge", "pageurl"):
            if not getattr(self, name):
                raise InvalidChallengeError(
                    f"GeeTestV3Challenge.{name} must be a non-empty string"
                )


@dataclass(frozen=True, slots=True)
class GeeTestV4Challenge(BaseChallenge):
    """GeeTest v4 captcha (ADR-0066 call style)."""

    captcha_id: str = field(kw_only=True)
    pageurl: str = field(kw_only=True)
    solution_type: ClassVar[type[BaseSolution]] = GeeTestV4Solution

    def __post_init__(self) -> None:
        if not self.captcha_id:
            raise InvalidChallengeError(
                "GeeTestV4Challenge.captcha_id must be a non-empty string"
            )
        if not self.pageurl:
            raise InvalidChallengeError(
                "GeeTestV4Challenge.pageurl must be a non-empty string"
            )


__all__ = ["GeeTestV3Challenge", "GeeTestV4Challenge"]
