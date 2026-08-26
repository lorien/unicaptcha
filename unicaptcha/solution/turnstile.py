"""Turnstile solution kind base (ADR-0035, ADR-0074)."""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha._internal.repr import truncate_token
from unicaptcha._internal.taxonomy import guard_abstract
from unicaptcha.solution.base import BaseSolution


@dataclass(frozen=True, slots=True)
class TurnstileSolution(BaseSolution):
    """Solved Cloudflare Turnstile token. Abstract; provider subclasses."""

    token: str

    def __post_init__(self) -> None:
        guard_abstract(self, TurnstileSolution)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(token={truncate_token(self.token)!r})"

    __str__ = __repr__


__all__ = ["TurnstileSolution"]
