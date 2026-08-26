"""hCaptcha solution kind base (ADR-0035)."""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha._internal.repr import truncate_token
from unicaptcha._internal.taxonomy import guard_abstract
from unicaptcha.solution.base import BaseSolution


@dataclass(frozen=True, slots=True)
class HCaptchaSolution(BaseSolution):
    """Solved hCaptcha token. Abstract; construct provider subclasses."""

    token: str

    def __post_init__(self) -> None:
        guard_abstract(self, HCaptchaSolution)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(token={truncate_token(self.token)!r})"

    __str__ = __repr__


__all__ = ["HCaptchaSolution"]
