"""reCAPTCHA v3 solution kind base (ADR-0035)."""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha._internal.repr import truncate_token
from unicaptcha._internal.taxonomy import guard_abstract
from unicaptcha.solution.base import BaseSolution


@dataclass(frozen=True, slots=True)
class RecaptchaV3Solution(BaseSolution):
    """Solved reCAPTCHA v3 token with score/action.

    Abstract; construct provider subclasses.
    """

    token: str
    score: float | None = None
    action: str | None = None

    def __post_init__(self) -> None:
        guard_abstract(self, RecaptchaV3Solution)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(token={truncate_token(self.token)!r}, "
            f"score={self.score!r}, action={self.action!r})"
        )

    __str__ = __repr__


__all__ = ["RecaptchaV3Solution"]
