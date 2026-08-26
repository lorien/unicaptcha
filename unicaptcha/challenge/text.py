"""Text challenge kind base (ADR-0048, ADR-0064)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.text import TextSolution


@dataclass(frozen=True, slots=True)
class TextChallenge(BaseChallenge):
    """A text captcha question."""

    text: str
    solution_type: ClassVar[type[BaseSolution]] = TextSolution

    def __post_init__(self) -> None:
        if not self.text:
            raise InvalidChallengeError("TextChallenge.text must be a non-empty string")


__all__ = ["TextChallenge"]
