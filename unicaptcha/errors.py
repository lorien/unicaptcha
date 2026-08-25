"""Exception hierarchy and error kinds (ADR-0009, as amended).

Every class maps 1:1 to an ``ErrorKind`` value (class minus ``Error``,
SCREAMING_SNAKE). ``ProviderError`` is the unclassified catch-all and hosts
the one nested leaf, ``EmptySolutionError`` (ADR-0040).

Behavioral discipline enforced at call sites (not in these classes):

- Wrapped causes always chain: ``raise ... from cause``.
- Wrong-provider routing raises ``TypeError`` pre-flight, no network
  (ADR-0045); there is no dedicated exception for it.
- No ``SolveCancelledError`` (ADR-0016) and no ``UnknownTaskError``
  (ADR-0050) — by construction.
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


class NetworkError(UnicaptchaError):
    """Transport-level failure (DNS, refused, TLS, timeout)."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(message, kind=ErrorKind.NETWORK, raw_response=raw_response)


class AuthenticationError(UnicaptchaError):
    """The provider rejected the API key."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(
            message, kind=ErrorKind.AUTHENTICATION, raw_response=raw_response
        )


class InsufficientBalanceError(UnicaptchaError):
    """The provider reported insufficient balance."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(
            message,
            kind=ErrorKind.INSUFFICIENT_BALANCE,
            raw_response=raw_response,
        )


class UnsupportedChallengeError(UnicaptchaError):
    """The provider does not support this operation for this captcha kind.

    Raised for server-side task-type rejections and client-side pre-flight
    coverage gaps alike (ADR-0057). Never for wrong-provider routing
    (``TypeError``) or unknown task ids (``TaskStatus.UNKNOWN``).
    """

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(
            message,
            kind=ErrorKind.UNSUPPORTED_CHALLENGE,
            raw_response=raw_response,
        )


class InvalidChallengeError(UnicaptchaError):
    """A challenge was invalid client-side (validation failure)."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(
            message, kind=ErrorKind.INVALID_CHALLENGE, raw_response=raw_response
        )


class TaskTimeoutError(UnicaptchaError):
    """The solve/wait budget was exhausted (ADR-0010)."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(
            message, kind=ErrorKind.TASK_TIMEOUT, raw_response=raw_response
        )


class RateLimitError(UnicaptchaError):
    """Rate limiting exhausted the retry policy (ADR-0059)."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(message, kind=ErrorKind.RATE_LIMIT, raw_response=raw_response)


class ServiceBusyError(UnicaptchaError):
    """Provider capacity: no workers free (ADR-0059 amendment)."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(
            message, kind=ErrorKind.SERVICE_BUSY, raw_response=raw_response
        )


class NoSolutionError(UnicaptchaError):
    """Workers could not solve the captcha; no auto-resubmit (ADR-0029)."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(message, kind=ErrorKind.NO_SOLUTION, raw_response=raw_response)


class InvalidConfigError(UnicaptchaError):
    """A configuration value was explicitly set to an invalid value.

    ``None`` is always valid ("unspecified", ADR-0043); only explicit bad
    values raise (ADR-0042).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, kind=ErrorKind.INVALID_CONFIG)


class ClientClosedError(UnicaptchaError):
    """An operation was attempted on a closed client (ADR-0033)."""

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(
            message, kind=ErrorKind.CLIENT_CLOSED, raw_response=raw_response
        )


class ProviderError(UnicaptchaError):
    """Unclassified provider error.

    Also raised for malformed responses (HTTP 200, unparseable or
    wrong-shape body) with the parse failure chained as ``__cause__`` and
    ``raw_response`` preserved (ADR-0040, ADR-0058).
    """

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        super().__init__(message, kind=ErrorKind.PROVIDER, raw_response=raw_response)


class EmptySolutionError(ProviderError):
    """A "solved" response whose solution payload was empty (ADR-0040).

    Subclass of ``ProviderError`` with its own kind: empty answers are
    typically transient worker failures and may be retried/rerouted,
    unlike generic garbage.
    """

    def __init__(self, message: str, *, raw_response: bytes = b"") -> None:
        UnicaptchaError.__init__(
            self,
            message,
            kind=ErrorKind.EMPTY_SOLUTION,
            raw_response=raw_response,
        )


__all__ = [
    "AuthenticationError",
    "ClientClosedError",
    "EmptySolutionError",
    "ErrorKind",
    "InsufficientBalanceError",
    "InvalidChallengeError",
    "InvalidConfigError",
    "NetworkError",
    "NoSolutionError",
    "ProviderError",
    "RateLimitError",
    "ServiceBusyError",
    "TaskTimeoutError",
    "UnicaptchaError",
    "UnsupportedChallengeError",
]
