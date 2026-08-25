"""Field-wise None-merge for the config types (ADR-0043).

Pure helper used by the engine at solve time to resolve the chain
``per-call explicit value -> client-level explicit value -> per-kind
default table`` (task 9). A per-call config inherits unset (``None``)
fields from the client config; it never discards them.
"""

from __future__ import annotations

from dataclasses import fields, replace
from typing import TypeVar

from unicaptcha.types import NetworkConfig, RetryConfig, TimeConfig

_C = TypeVar("_C", TimeConfig, NetworkConfig, RetryConfig)


def merge_configs(base: _C, override: _C) -> _C:
    """Return a new config with every non-``None`` field of ``override``
    taken over the corresponding field of ``base``. ``base`` is not
    mutated."""
    changes = {
        f.name: getattr(override, f.name)
        for f in fields(override)
        if getattr(override, f.name) is not None
    }
    return replace(base, **changes)


__all__ = ["merge_configs"]
