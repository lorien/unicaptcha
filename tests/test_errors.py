import unicaptcha
from unicaptcha import (
    AuthenticationError,
    ClientClosedError,
    EmptySolutionError,
    ErrorKind,
    InsufficientBalanceError,
    InvalidChallengeError,
    InvalidConfigError,
    NetworkError,
    NoCaptchaDetectedError,
    NoSolutionError,
    ProviderError,
    RateLimitError,
    ServiceBusyError,
    TaskTimeoutError,
    UnicaptchaError,
    UnsupportedChallengeError,
)

_LEAF_KINDS = [
    (ErrorKind.NETWORK, NetworkError),
    (ErrorKind.AUTHENTICATION, AuthenticationError),
    (ErrorKind.INSUFFICIENT_BALANCE, InsufficientBalanceError),
    (ErrorKind.UNSUPPORTED_CHALLENGE, UnsupportedChallengeError),
    (ErrorKind.INVALID_CHALLENGE, InvalidChallengeError),
    (ErrorKind.TASK_TIMEOUT, TaskTimeoutError),
    (ErrorKind.RATE_LIMIT, RateLimitError),
    (ErrorKind.SERVICE_BUSY, ServiceBusyError),
    (ErrorKind.NO_SOLUTION, NoSolutionError),
    (ErrorKind.EMPTY_SOLUTION, EmptySolutionError),
    (ErrorKind.CLIENT_CLOSED, ClientClosedError),
    (ErrorKind.INVALID_CONFIG, InvalidConfigError),
    (ErrorKind.NO_CAPTCHA_DETECTED, NoCaptchaDetectedError),
    (ErrorKind.PROVIDER, ProviderError),
]


class TestErrorKind:
    def test_values(self) -> None:
        assert len(ErrorKind) == 14
        assert {e.value for e in ErrorKind} == {
            "NETWORK",
            "AUTHENTICATION",
            "INSUFFICIENT_BALANCE",
            "UNSUPPORTED_CHALLENGE",
            "INVALID_CHALLENGE",
            "TASK_TIMEOUT",
            "RATE_LIMIT",
            "SERVICE_BUSY",
            "NO_SOLUTION",
            "EMPTY_SOLUTION",
            "CLIENT_CLOSED",
            "INVALID_CONFIG",
            "NO_CAPTCHA_DETECTED",
            "PROVIDER",
        }


class TestUnicaptchaError:
    def test_kind_and_raw_response(self) -> None:
        e = UnicaptchaError("boom", kind=ErrorKind.PROVIDER, raw_response=b"raw")
        assert e.kind is ErrorKind.PROVIDER
        assert e.raw_response == b"raw"
        assert str(e) == "boom"

    def test_raw_response_defaults_empty(self) -> None:
        assert UnicaptchaError("x", kind=ErrorKind.NETWORK).raw_response == b""


class TestHierarchy:
    def test_one_to_one_kind_mapping(self) -> None:
        # ADR-0009 1:1 invariant: class minus Error == SCREAMING_SNAKE kind.
        for kind, cls in _LEAF_KINDS:
            assert cls("boom").kind is kind

    def test_every_leaf_is_a_unicaptcha_error(self) -> None:
        for _, cls in _LEAF_KINDS:
            assert issubclass(cls, UnicaptchaError)

    def test_empty_solution_is_a_provider_error(self) -> None:
        assert issubclass(EmptySolutionError, ProviderError)

    def test_message(self) -> None:
        for _, cls in _LEAF_KINDS:
            assert str(cls("boom")) == "boom"


class TestRawResponse:
    def test_passthrough(self) -> None:
        assert ProviderError("x", raw_response=b"body").raw_response == b"body"
        assert NetworkError("x", raw_response=b"body").raw_response == b"body"
        assert NoSolutionError("x", raw_response=b"body").raw_response == b"body"
        assert EmptySolutionError("x", raw_response=b"body").raw_response == b"body"

    def test_invalid_config_takes_message_only(self) -> None:
        assert InvalidConfigError("bad").raw_response == b""


class TestAbsentClasses:
    def test_no_solve_cancelled_error(self) -> None:
        assert not hasattr(unicaptcha.errors, "SolveCancelledError")

    def test_no_unknown_task_error(self) -> None:
        assert not hasattr(unicaptcha.errors, "UnknownTaskError")


class TestRootExports:
    def test_all_error_classes_exported(self) -> None:
        for _, cls in _LEAF_KINDS:
            assert cls.__name__ in unicaptcha.__all__
            assert hasattr(unicaptcha, cls.__name__)
