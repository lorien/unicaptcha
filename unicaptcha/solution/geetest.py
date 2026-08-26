"""GeeTest v3/v4 solution kind bases (ADR-0035, ADR-0070)."""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha._internal.repr import truncate_token
from unicaptcha._internal.taxonomy import guard_abstract
from unicaptcha.solution.base import BaseSolution


@dataclass(frozen=True, slots=True)
class GeeTestV3Solution(BaseSolution):
    """Solved GeeTest v3 three-part answer. Abstract; provider subclasses."""

    challenge: str
    validate: str
    seccode: str

    def __post_init__(self) -> None:
        guard_abstract(self, GeeTestV3Solution)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(challenge={truncate_token(self.challenge)!r}, "
            f"validate={truncate_token(self.validate)!r}, "
            f"seccode={truncate_token(self.seccode)!r})"
        )

    __str__ = __repr__


@dataclass(frozen=True, slots=True)
class GeeTestV4Solution(BaseSolution):
    """Solved GeeTest v4 five-part answer. Abstract; provider subclasses."""

    captcha_id: str
    lot_number: str
    pass_token: str
    gen_time: str
    captcha_output: str

    def __post_init__(self) -> None:
        guard_abstract(self, GeeTestV4Solution)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(captcha_id={truncate_token(self.captcha_id)!r}, "
            f"lot_number={truncate_token(self.lot_number)!r}, "
            f"pass_token={truncate_token(self.pass_token)!r}, "
            f"gen_time={truncate_token(self.gen_time)!r}, "
            f"captcha_output={truncate_token(self.captcha_output)!r})"
        )

    __str__ = __repr__


__all__ = ["GeeTestV3Solution", "GeeTestV4Solution"]
