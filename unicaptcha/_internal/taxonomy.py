"""Shared abstract-base construction guard (ADR-0035, ADR-0056).

Solution bases reject direct construction: ``type(obj) is cls`` is the
``__post_init__`` check that makes a base a contract rather than a
constructible type. Provider subclasses always construct.
"""

from __future__ import annotations


def guard_abstract(obj: object, cls: type[object]) -> None:
    """Raise ``TypeError`` if ``obj`` is exactly an instance of ``cls``."""
    if type(obj) is cls:
        raise TypeError(
            f"{cls.__name__} is abstract and cannot be instantiated directly; "
            "construct a concrete subclass."
        )


__all__ = ["guard_abstract"]
