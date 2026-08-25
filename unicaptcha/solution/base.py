"""Solution taxonomy root (ADR-0035, ADR-0056).

Abstract kind bases land with task 6; this module currently carries only the
public abstract root that the model types in ``unicaptcha.types`` depend on.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BaseSolution:
    """Public abstract root of the solution taxonomy.

    Never instantiated directly: ``__post_init__`` raises ``TypeError`` when
    the concrete type is this base (ADR-0035). Adapters construct provider
    subclasses (e.g. ``TwoCaptchaImageSolution``); custom-kind authors
    subclass this root.
    """

    def __post_init__(self) -> None:
        if type(self) is BaseSolution:
            raise TypeError(
                "BaseSolution is abstract and cannot be instantiated directly; "
                "construct a provider solution subclass."
            )


__all__ = ["BaseSolution"]
