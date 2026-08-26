"""Map ``ErrorKind`` to the exception leaf (ADR-0009 1:1 invariant)."""

from __future__ import annotations

from collections.abc import Callable

from unicaptcha.errors import (
    AuthenticationError,
    ClientClosedError,
    EmptySolutionError,
    ErrorKind,
    InsufficientBalanceError,
    InvalidChallengeError,
    InvalidConfigError,
    NetworkError,
    NoSolutionError,
    ProviderError,
    RateLimitError,
    ServiceBusyError,
    TaskTimeoutError,
    UnicaptchaError,
    UnsupportedChallengeError,
)

_KIND_CLASS: dict[ErrorKind, Callable[..., UnicaptchaError]] = {
    ErrorKind.NETWORK: NetworkError,
    ErrorKind.AUTHENTICATION: AuthenticationError,
    ErrorKind.INSUFFICIENT_BALANCE: InsufficientBalanceError,
    ErrorKind.UNSUPPORTED_CHALLENGE: UnsupportedChallengeError,
    ErrorKind.INVALID_CHALLENGE: InvalidChallengeError,
    ErrorKind.TASK_TIMEOUT: TaskTimeoutError,
    ErrorKind.RATE_LIMIT: RateLimitError,
    ErrorKind.SERVICE_BUSY: ServiceBusyError,
    ErrorKind.NO_SOLUTION: NoSolutionError,
    ErrorKind.EMPTY_SOLUTION: EmptySolutionError,
    ErrorKind.CLIENT_CLOSED: ClientClosedError,
    ErrorKind.INVALID_CONFIG: InvalidConfigError,
    ErrorKind.PROVIDER: ProviderError,
}


def error_from_kind(
    kind: ErrorKind,
    message: str,
    raw_response: bytes = b"",
) -> UnicaptchaError:
    """Construct the exception leaf for an ``ErrorKind`` (provider mapping)."""
    if kind is ErrorKind.INVALID_CONFIG:
        return InvalidConfigError(message)
    cls = _KIND_CLASS.get(kind, ProviderError)
    return cls(message, raw_response=raw_response)


__all__ = ["error_from_kind"]
