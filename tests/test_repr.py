from unicaptcha._internal.repr import stub_bytes, truncate_token
from unicaptcha.provider.anticaptcha import AntiCaptchaRecaptchaV2Solution
from unicaptcha.provider.capmonster import CapMonsterRecaptchaV2Solution
from unicaptcha.provider.capsolver import CapsolverRecaptchaV2Solution
from unicaptcha.provider.twocaptcha import (
    TwoCaptchaGeeTestV3Solution,
    TwoCaptchaImageSolution,
    TwoCaptchaRecaptchaV2Solution,
)


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


class TestProviderSolutionRepr:
    """Provider solution subclasses must inherit the kind base's truncating
    repr (``repr=False``), never leak the token (ADR-0034)."""

    def test_token_solutions_truncate(self) -> None:
        for cls in (
            TwoCaptchaRecaptchaV2Solution,
            AntiCaptchaRecaptchaV2Solution,
            CapMonsterRecaptchaV2Solution,
            CapsolverRecaptchaV2Solution,
        ):
            rendered = repr(cls("0123456789abcdef"))
            assert "***cdef" in rendered
            assert "0123456789abcdef" not in rendered

    def test_geetest_v3_truncates_each_field(self) -> None:
        sol = TwoCaptchaGeeTestV3Solution(
            challenge="0123456789abcdef",
            validate="0123456789ghijkl",
            seccode="0123456789mnopqr",
        )
        assert "***cdef" in repr(sol)
        assert "***ijkl" in repr(sol)
        assert "0123456789abcdef" not in repr(sol)

    def test_image_text_truncate(self) -> None:
        rendered = repr(TwoCaptchaImageSolution("0123456789abcdef"))
        assert "***cdef" in rendered
        assert "0123456789abcdef" not in rendered
