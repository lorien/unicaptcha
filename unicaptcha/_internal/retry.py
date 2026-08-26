"""Submit-phase retry classification (ADR-0011, ADR-0059)."""

from __future__ import annotations

import httpx

from unicaptcha.errors import NetworkError


def classify_submit_status(status: int) -> str:
    """Classify an HTTP status for the submit phase.

    Returns one of ``retry`` (500/503), ``retry_rate_limit`` (429),
    ``fail_fast`` (502/504), ``provider`` (non-200 error body), ``ok`` (200).
    """
    if status == 429:
        return "retry_rate_limit"
    if status in (500, 503):
        return "retry"
    if status in (502, 504):
        return "fail_fast"
    return "ok" if status == 200 else "provider"


def is_presend(exc: NetworkError) -> bool:
    """Whether a ``NetworkError`` is a provably-safe pre-send fault.

    Pre-send (``httpx.ConnectError`` / ``ConnectTimeout``) is retryable;
    after-send failures (read timeout, reset) are ambiguous and fail fast
    (ADR-0011). The transport chains the httpx exception as ``__cause__``.
    """
    return isinstance(exc.__cause__, (httpx.ConnectError, httpx.ConnectTimeout))


__all__ = ["classify_submit_status", "is_presend"]
