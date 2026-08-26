import pytest
from _fake import FakeSolution

from unicaptcha import (
    BaseSolution,
    FunCaptchaSolution,
    GeeTestV3Solution,
    GeeTestV4Solution,
    HCaptchaSolution,
    ImageSolution,
    RecaptchaV2Solution,
    RecaptchaV3Solution,
    TextSolution,
    TurnstileSolution,
)

_KIND_BASES = [
    (ImageSolution, ("token-value-1234",)),
    (TextSolution, ("answer-5678",)),
    (RecaptchaV2Solution, ("token-value-1234",)),
    (RecaptchaV3Solution, ("token-value-1234", 0.7, "homepage")),
    (HCaptchaSolution, ("token-value-1234",)),
    (FunCaptchaSolution, ("token-value-1234",)),
    (GeeTestV3Solution, ("challenge-a", "validate-b", "seccode-c")),
    (
        GeeTestV4Solution,
        ("cid-1", "lot-2", "pass-3", "gen-4", "output-5"),
    ),
    (TurnstileSolution, ("token-value-1234",)),
]


class _ImageSolution(ImageSolution):
    pass


class _V3Solution(RecaptchaV3Solution):
    pass


class _Gt3Solution(GeeTestV3Solution):
    pass


class TestBaseSolution:
    def test_not_directly_instantiable(self) -> None:
        with pytest.raises(TypeError):
            BaseSolution()

    def test_subclass_instantiable(self) -> None:
        assert isinstance(FakeSolution(), BaseSolution)


class TestKindBases:
    def test_bases_reject_direct_construction(self) -> None:
        for base, args in _KIND_BASES:
            with pytest.raises(TypeError):
                base(*args)

    def test_concrete_subclasses_instantiable(self) -> None:
        assert isinstance(_ImageSolution("token-value-1234"), ImageSolution)
        assert isinstance(
            _V3Solution("token-value-1234", 0.7, "homepage"), RecaptchaV3Solution
        )
        assert isinstance(
            _Gt3Solution("challenge-a", "validate-b", "seccode-c"),
            GeeTestV3Solution,
        )


class TestReprPolicy:
    def test_token_truncated(self) -> None:
        r = repr(_ImageSolution("token-value-1234"))
        assert "***1234" in r
        assert "token-value-1234" not in r

    def test_str_mirrors_repr(self) -> None:
        s = _ImageSolution("token-value-1234")
        assert str(s) == repr(s)

    def test_recaptcha_v3_repr(self) -> None:
        s = _V3Solution("token-value-1234", 0.7, "homepage")
        assert "***1234" in repr(s)
        assert "token-value-1234" not in repr(s)
        assert "0.7" in repr(s)

    def test_geetest_fields_truncated(self) -> None:
        s = _Gt3Solution("challenge-a", "validate-b", "seccode-c")
        r = repr(s)
        assert "challenge-a" not in r
        assert "***ge-a" in r
