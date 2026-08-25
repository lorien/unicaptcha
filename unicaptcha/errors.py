"""Exception hierarchy and error kinds.

Full hierarchy lands in task 3; this module currently carries the base,
the public ``ErrorKind`` enum (ADR-0009) and ``InvalidConfigError``, which
the model/config types in ``unicaptcha.types`` already depend on.
"""

from __future__ import annotations

from enum import Enum


class ErrorKind(Enum):
    """Classification of library errors (ADR-0009, as amended)."""

    NETWORK = "NETWORK"
    AUTHENTICATION = "AUTHENTICATION"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    UNSUPPORTED_CHALLENGE = "UNSUPPORTED_CHALLENGE"
    INVALID_CHALLENGE = "INVALID_CHALLENGE"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    SERVICE_BUSY = "SERVICE_BUSY"
    NO_SOLUTION = "NO_SOLUTION"
    EMPTY_SOLUTION = "EMPTY_SOLUTION"
    CLIENT_CLOSED = "CLIENT_CLOSED"
    INVALID_CONFIG = "INVALID_CONFIG"
    PROVIDER = "PROVIDER"


class UnicaptchaError(Exception):
    """Base of the library error hierarchy.

    Carries the error ``kind`` and the verbatim provider response body
    (``raw_response``) when one exists.
    """

    kind: ErrorKind
    raw_response: bytes

    def __init__(
        self,
        message: str,
        *,
        kind: ErrorKind,
        raw_response: bytes = b"",
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.raw_response = raw_response


class InvalidConfigError(UnicaptchaError):
    """A configuration value was explicitly set to an invalid value.

    ``None`` is always valid ("unspecified", ADR-0043); only explicit bad
    values raise (ADR-0042).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, kind=ErrorKind.INVALID_CONFIG)


__all__ = ["ErrorKind", "InvalidConfigError", "UnicaptchaError"]
