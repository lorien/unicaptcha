from unicaptcha._internal.repr import stub_bytes, truncate_token


class TestStubBytes:
    def test_stub(self) -> None:
        assert stub_bytes(b"hello") == "<5 bytes>"
        assert stub_bytes(b"") == "<0 bytes>"


class TestTruncateToken:
    def test_long_token(self) -> None:
        assert truncate_token("0123456789abcd") == "***abcd"

    def test_short_token(self) -> None:
        assert truncate_token("abc") == "***abc"

    def test_empty(self) -> None:
        assert truncate_token("") == "***"
