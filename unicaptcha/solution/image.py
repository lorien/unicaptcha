"""Image solution kind base (ADR-0035)."""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha._internal.repr import truncate_token
from unicaptcha._internal.taxonomy import guard_abstract
from unicaptcha.solution.base import BaseSolution


@dataclass(frozen=True, slots=True)
class ImageSolution(BaseSolution):
    """Solved image captcha text. Abstract; construct provider subclasses."""

    text: str

    def __post_init__(self) -> None:
        guard_abstract(self, ImageSolution)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(text={truncate_token(self.text)!r})"

    __str__ = __repr__


__all__ = ["ImageSolution"]
