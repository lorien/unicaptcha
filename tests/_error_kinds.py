"""Shared error-kind tables for tests.

Adapter tests and event tests draw from these instead of re-declaring
inline mappings, so adapter ``error_kinds`` and the events layer cannot
drift apart. Not collected by pytest (filename not test_*).
"""

from collections.abc import Mapping

from unicaptcha import ErrorKind, TaskEventKind

#: Expected provider ``errorCode`` -> ``ErrorKind`` tables, mirroring each
#: shipped adapter's ``error_kinds`` ClassVar.
PROVIDER_ERROR_KINDS: Mapping[str, Mapping[str, ErrorKind]] = {
    "twocaptcha": {
        "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
        "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
        "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
        "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
        "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
    },
    "anti-captcha": {
        "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
        "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
        "ERROR_IP_NOT_ALLOWED": ErrorKind.AUTHENTICATION,
        "ERROR_IP_BANNED": ErrorKind.AUTHENTICATION,
        "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
        "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
        "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
    },
    "capmonster": {
        "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
        "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
        "ERROR_IP_NOT_ALLOWED": ErrorKind.AUTHENTICATION,
        "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
        "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
        "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
    },
    "capsolver": {
        "ERROR_KEY_DOES_NOT_EXIST": ErrorKind.AUTHENTICATION,
        "ERROR_WRONG_USER_KEY": ErrorKind.AUTHENTICATION,
        "ERROR_IP_NOT_ALLOWED": ErrorKind.AUTHENTICATION,
        "ERROR_IP_BANNED": ErrorKind.AUTHENTICATION,
        "ERROR_ZERO_BALANCE": ErrorKind.INSUFFICIENT_BALANCE,
        "ERROR_NO_SLOT_AVAILABLE": ErrorKind.SERVICE_BUSY,
        "ERROR_TOO_MANY_REQUESTS": ErrorKind.RATE_LIMIT,
    },
}

#: Valid ``ErrorKind`` values per terminal failure event kind.
TERMINAL_ERROR_KINDS: Mapping[TaskEventKind, frozenset[ErrorKind]] = {
    TaskEventKind.PRE_FLIGHT_FAILED: frozenset(
        {
            None,
            ErrorKind.INVALID_CHALLENGE,
            ErrorKind.UNSUPPORTED_CHALLENGE,
            ErrorKind.INVALID_CONFIG,
            ErrorKind.CLIENT_CLOSED,
        }
    ),
    TaskEventKind.SUBMIT_FAILED: frozenset(
        {
            ErrorKind.NETWORK,
            ErrorKind.RATE_LIMIT,
            ErrorKind.SERVICE_BUSY,
            ErrorKind.AUTHENTICATION,
            ErrorKind.INSUFFICIENT_BALANCE,
            ErrorKind.PROVIDER,
            ErrorKind.CLIENT_CLOSED,
        }
    ),
    TaskEventKind.RESULT_FAILED: frozenset(
        {
            ErrorKind.NO_SOLUTION,
            ErrorKind.EMPTY_SOLUTION,
            ErrorKind.TASK_TIMEOUT,
            ErrorKind.PROVIDER,
            ErrorKind.CLIENT_CLOSED,
        }
    ),
}
