"""Universal async/sync interface to multiple anti-captcha services."""

from unicaptcha._version import __version__
from unicaptcha.errors import ErrorKind, InvalidConfigError, UnicaptchaError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.types import (
    NetworkConfig,
    ParsedTask,
    Proxy,
    ProxyKind,
    RetryConfig,
    SecretStr,
    SubmitAccepted,
    TaskRef,
    TaskResult,
    TaskStatus,
    TaskStatusResult,
    TaskTicket,
    TimeConfig,
)

__all__ = [
    "BaseSolution",
    "ErrorKind",
    "InvalidConfigError",
    "NetworkConfig",
    "ParsedTask",
    "Proxy",
    "ProxyKind",
    "RetryConfig",
    "SecretStr",
    "SubmitAccepted",
    "TaskRef",
    "TaskResult",
    "TaskStatus",
    "TaskStatusResult",
    "TaskTicket",
    "TimeConfig",
    "UnicaptchaError",
    "__version__",
]
