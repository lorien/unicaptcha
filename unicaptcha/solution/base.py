"""Solution taxonomy root (ADR-0035, ADR-0056)."""

from __future__ import annotations

from dataclasses import dataclass

from unicaptcha._internal.taxonomy import guard_abstract


@dataclass(frozen=True, slots=True)
class BaseSolution:
    """Public abstract root of the solution taxonomy.

    Never instantiated directly; adapters construct provider subclasses
    (e.g. ``TwoCaptchaImageSolution``); custom-kind authors subclass this
    root.
    """

    def __post_init__(self) -> None:
        guard_abstract(self, BaseSolution)


__all__ = ["BaseSolution"]
