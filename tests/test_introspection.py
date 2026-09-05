"""Capability introspection tests: supports / providers_supporting /
supported_kinds, and the KIND_TAGS / TAG_KINDS registry."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from unicaptcha import (
    KIND_TAGS,
    TAG_KINDS,
    AsyncSolver,
    FunCaptchaChallenge,
    GeeTestV3Challenge,
    GeeTestV4Challenge,
    HCaptchaChallenge,
    ImageChallenge,
    RecaptchaV2Challenge,
    RecaptchaV3Challenge,
    Solver,
    TextChallenge,
    TurnstileChallenge,
)
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import ErrorKind
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter
from unicaptcha.types import ParsedTask, SubmitAccepted


class _IntroAdapter(BaseAdapter):
    provider = "intro"
    challenges: frozenset[type[BaseChallenge]] = frozenset()
    default_base_url = "https://intro.example"

    def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
        raise NotImplementedError

    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        raise NotImplementedError

    def parse_task_status(self, raw: bytes) -> ParsedTask:
        raise NotImplementedError

    def parse_balance(self, raw: bytes) -> Decimal:
        raise NotImplementedError

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        raise NotImplementedError


class V2Adapter(_IntroAdapter):
    provider = "v2"
    challenges = frozenset({RecaptchaV2Challenge})


class CapAdapter(_IntroAdapter):
    provider = "cap"
    challenges = frozenset({RecaptchaV2Challenge, TurnstileChallenge})


class TextAdapter(_IntroAdapter):
    provider = "text"
    challenges = frozenset({TextChallenge})


class TestKindTags:
    def test_all_nine_kinds_present(self) -> None:
        assert len(KIND_TAGS) == 9
        for kind in (
            ImageChallenge,
            TextChallenge,
            RecaptchaV2Challenge,
            RecaptchaV3Challenge,
            HCaptchaChallenge,
            FunCaptchaChallenge,
            GeeTestV3Challenge,
            GeeTestV4Challenge,
            TurnstileChallenge,
        ):
            assert kind in KIND_TAGS

    def test_roundtrip(self) -> None:
        assert KIND_TAGS[RecaptchaV2Challenge] == "recaptcha-v2"
        assert TAG_KINDS["recaptcha-v2"] is RecaptchaV2Challenge
        assert set(TAG_KINDS) == set(KIND_TAGS.values())
        assert set(TAG_KINDS.values()) == set(KIND_TAGS)

    def test_detect_tags_are_canonical(self) -> None:
        for tag in (
            "recaptcha-v2",
            "recaptcha-v3",
            "hcaptcha",
            "turnstile",
            "funcaptcha",
            "geetest-v3",
            "geetest-v4",
        ):
            assert tag in TAG_KINDS


@pytest.fixture
def solver() -> Solver:
    return Solver([V2Adapter("k"), CapAdapter("k"), TextAdapter("k")])


class TestSupports:
    def test_class_and_tag_equivalent(self, solver: Solver) -> None:
        assert solver.supports(RecaptchaV2Challenge) is True
        assert solver.supports("recaptcha-v2") is True
        assert solver.supports(TurnstileChallenge) is True
        assert solver.supports("turnstile") is True

    def test_unsupported_never_raises(self, solver: Solver) -> None:
        assert solver.supports(HCaptchaChallenge) is False
        assert solver.supports("hcaptcha") is False
        assert solver.supports("geetest-v4") is False

    def test_unknown_kind_type_error(self, solver: Solver) -> None:
        with pytest.raises(TypeError):
            solver.supports("bogus-kind")
        with pytest.raises(TypeError):
            solver.supports(object)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            solver.supports(123)  # type: ignore[arg-type]

    def test_works_after_close(self) -> None:
        client = Solver([V2Adapter("k")])
        client.close()
        assert client.supports(RecaptchaV2Challenge) is True


class TestProvidersSupporting:
    def test_registration_order(self, solver: Solver) -> None:
        assert solver.providers_supporting(RecaptchaV2Challenge) == ("v2", "cap")
        assert solver.providers_supporting("turnstile") == ("cap",)

    def test_empty_when_unsupported(self, solver: Solver) -> None:
        assert solver.providers_supporting(HCaptchaChallenge) == ()


class TestSupportedKinds:
    def test_tags_in_definition_order(self, solver: Solver) -> None:
        assert solver.supported_kinds() == ("text", "recaptcha-v2", "turnstile")

    def test_single_all_kind_provider(self) -> None:
        client = Solver([TwoCaptchaAdapter("k")])
        assert client.supported_kinds() == tuple(KIND_TAGS.values())


class TestAsyncSolver:
    def test_mirrors_sync(self) -> None:
        client = AsyncSolver([V2Adapter("k"), CapAdapter("k"), TextAdapter("k")])
        assert client.supports("turnstile") is True
        assert client.supports("hcaptcha") is False
        assert client.providers_supporting(RecaptchaV2Challenge) == ("v2", "cap")
        assert client.supported_kinds() == ("text", "recaptcha-v2", "turnstile")
