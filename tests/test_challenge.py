from dataclasses import dataclass, field
from pathlib import Path

import pytest

from unicaptcha import (
    BaseChallenge,
    FunCaptchaChallenge,
    GeeTestV3Challenge,
    GeeTestV4Challenge,
    HCaptchaChallenge,
    ImageChallenge,
    ImageSolution,
    InvalidChallengeError,
    RecaptchaV2Challenge,
    RecaptchaV3Challenge,
    RecaptchaV3Solution,
    TextChallenge,
    TextSolution,
    TurnstileChallenge,
)
from unicaptcha.solution import (
    FunCaptchaSolution,
    GeeTestV3Solution,
    GeeTestV4Solution,
    HCaptchaSolution,
    RecaptchaV2Solution,
    TurnstileSolution,
)

_CHALLENGE_LINKS = [
    (ImageChallenge, ImageSolution),
    (TextChallenge, TextSolution),
    (RecaptchaV2Challenge, RecaptchaV2Solution),
    (RecaptchaV3Challenge, RecaptchaV3Solution),
    (HCaptchaChallenge, HCaptchaSolution),
    (FunCaptchaChallenge, FunCaptchaSolution),
    (GeeTestV3Challenge, GeeTestV3Solution),
    (GeeTestV4Challenge, GeeTestV4Solution),
    (TurnstileChallenge, TurnstileSolution),
]


class TestBaseChallenge:
    def test_not_directly_instantiable(self) -> None:
        with pytest.raises(TypeError):
            BaseChallenge()


class TestImageChallenge:
    def test_bytes_body_positional(self) -> None:
        c = ImageChallenge(b"png-data")
        assert c.body == b"png-data"

    def test_bytes_body_keyword(self) -> None:
        assert ImageChallenge(body=b"data").body == b"data"

    def test_path_normalized_to_bytes(self, tmp_path: Path) -> None:
        path = tmp_path / "cap.png"
        path.write_bytes(b"image-bytes")
        c = ImageChallenge(path)
        assert c.body == b"image-bytes"
        assert isinstance(c.body, bytes)

    def test_missing_path_raises_chained(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.png"
        with pytest.raises(InvalidChallengeError) as excinfo:
            ImageChallenge(missing)
        assert isinstance(excinfo.value.__cause__, OSError)

    def test_repr_stubs_bytes(self) -> None:
        assert repr(ImageChallenge(b"hello")) == "ImageChallenge(body=<5 bytes>)"
        assert "hello" not in repr(ImageChallenge(b"hello"))


class TestTextChallenge:
    def test_positional(self) -> None:
        assert TextChallenge("2+2?").text == "2+2?"

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidChallengeError):
            TextChallenge("")


class TestMultiFieldKinds:
    def test_recaptcha_v2_keyword_required(self) -> None:
        with pytest.raises(TypeError):
            RecaptchaV2Challenge("sk", "pu")  # type: ignore[misc]

    def test_recaptcha_v2_defaults(self) -> None:
        c = RecaptchaV2Challenge(sitekey="sk", pageurl="https://x.com")
        assert c.invisible is False
        assert c.is_enterprise is False
        assert c.data_s is None
        assert c.api_domain is None

    def test_recaptcha_v2_enterprise_flags(self) -> None:
        c = RecaptchaV2Challenge(
            sitekey="sk",
            pageurl="https://x.com",
            is_enterprise=True,
            data_s={"k": "v"},
            api_domain="recaptcha.net",
        )
        assert c.is_enterprise is True
        assert c.data_s == {"k": "v"}

    def test_recaptcha_v2_empty_sitekey_raises(self) -> None:
        with pytest.raises(InvalidChallengeError):
            RecaptchaV2Challenge(sitekey="", pageurl="https://x.com")

    def test_recaptcha_v3_defaults(self) -> None:
        c = RecaptchaV3Challenge(sitekey="sk", pageurl="https://x.com")
        assert c.action is None
        assert c.min_score is None

    def test_hcaptcha_defaults(self) -> None:
        c = HCaptchaChallenge(sitekey="sk", pageurl="https://x.com")
        assert c.is_invisible is False
        assert c.rqdata is None

    def test_funcaptcha_required(self) -> None:
        c = FunCaptchaChallenge(public_key="pk", pageurl="https://x.com")
        assert c.public_key == "pk"
        with pytest.raises(InvalidChallengeError):
            FunCaptchaChallenge(public_key="", pageurl="https://x.com")

    def test_geetest_v3(self) -> None:
        c = GeeTestV3Challenge(gt_key="gt", challenge="ch", pageurl="https://x.com")
        assert c.gt_key == "gt"
        with pytest.raises(InvalidChallengeError):
            GeeTestV3Challenge(gt_key="gt", challenge="", pageurl="https://x.com")

    def test_geetest_v4(self) -> None:
        c = GeeTestV4Challenge(captcha_id="id", pageurl="https://x.com")
        assert c.captcha_id == "id"
        with pytest.raises(InvalidChallengeError):
            GeeTestV4Challenge(captcha_id="", pageurl="https://x.com")

    def test_turnstile_defaults(self) -> None:
        c = TurnstileChallenge(sitekey="sk", pageurl="https://x.com")
        assert c.action is None
        assert c.c_data is None
        assert c.chl_page_data is None
        with pytest.raises(InvalidChallengeError):
            TurnstileChallenge(sitekey="", pageurl="https://x.com")


class TestSolutionTypeLink:
    def test_every_kind_links_to_its_solution_base(self) -> None:
        for challenge_cls, solution_cls in _CHALLENGE_LINKS:
            assert challenge_cls.solution_type is solution_cls


class TestInheritanceWart:
    def test_kw_only_extra_after_inherited_defaults(self) -> None:
        @dataclass(frozen=True, slots=True)
        class FakeProviderRecaptchaV2Challenge(RecaptchaV2Challenge):
            numeric: bool = field(kw_only=True)

        c = FakeProviderRecaptchaV2Challenge(
            sitekey="sk", pageurl="https://x.com", numeric=True
        )
        assert c.numeric is True
        assert c.sitekey == "sk"
