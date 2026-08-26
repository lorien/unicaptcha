"""Full-jitter exponential backoff (ADR-0011)."""

from __future__ import annotations

import random


def backoff_sleep(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """Full-jitter backoff: ``uniform(0, min(cap, base * 2**attempt))``.

    ``attempt`` is the zero-based retry index of the attempt that *will* be
    retried (i.e. the number of failures so far).
    """
    ceiling = min(cap, base * (2**attempt))
    return random.uniform(0.0, ceiling)


__all__ = ["backoff_sleep"]
