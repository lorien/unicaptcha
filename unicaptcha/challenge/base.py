"""Challenge taxonomy root (ADR-0048).

``BaseChallenge`` is the public abstract root, open for custom kinds; the
nine kind bases are instantiable (ADR-0064) and carry the universal fields
plus the challenge->solution type link.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BaseChallenge:
    """Public abstract root of the challenge taxonomy.

    Never instantiated directly; custom-kind authors subclass this root
    (ADR-0048). The kind bases are instantiable and carry universal fields.
    """

    def __post_init__(self) -> None:
        if type(self) is BaseChallenge:
            raise TypeError(
                "BaseChallenge is abstract and cannot be instantiated directly; "
                "construct a kind base or a provider challenge subclass."
            )


__all__ = ["BaseChallenge"]
