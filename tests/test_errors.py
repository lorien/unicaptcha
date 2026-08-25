from unicaptcha import ErrorKind, InvalidConfigError, UnicaptchaError


class TestErrorKind:
    def test_values(self) -> None:
        assert len(ErrorKind) == 13
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


class TestInvalidConfigError:
    def test_kind(self) -> None:
        e = InvalidConfigError("bad value")
        assert isinstance(e, UnicaptchaError)
        assert e.kind is ErrorKind.INVALID_CONFIG
        assert str(e) == "bad value"
