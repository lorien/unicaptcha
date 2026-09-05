"""HTML captcha detection tests (ADR-0077)."""

from __future__ import annotations

import pytest

from unicaptcha import (
    BaseChallenge,
    FunCaptchaChallenge,
    GeeTestV3Challenge,
    GeeTestV4Challenge,
    HCaptchaChallenge,
    InvalidChallengeError,
    RecaptchaV2Challenge,
    RecaptchaV3Challenge,
    TurnstileChallenge,
    detect,
)

URL = "https://example.com/login"

_SITEKEY = "6Lc2wvkSAAAAAKGZfA8mF6J7kd5U3lGiPNvzY6j"
_GT = "019924a82c70bb123aae90d483087f94"
_CHALLENGE = "12345678abc90123d45678ef90123a456b7"
_CAPTCHA_ID = "e392e1d7fd421dc63325744d5a2b9c73"
_PKEY = "B7D8911C-5CC8-A9A3-35B0-9AC9CCD110DA"


def test_no_matches_is_empty_tuple() -> None:
    assert detect("<html><body><p>no captcha here</p></body></html>", URL) == ()


def test_malformed_html_is_empty_tuple() -> None:
    assert detect("", URL) == ()
    assert detect("  ", URL) == ()
    assert detect("<div", URL) == ()


def test_html_must_be_str() -> None:
    with pytest.raises(TypeError):
        detect(b"<html></html>", URL)  # type: ignore[arg-type]


def test_pageurl_must_be_non_empty() -> None:
    with pytest.raises(InvalidChallengeError):
        detect("<div class='g-recaptcha'></div>", "")


def test_unsupported_tags_ignored() -> None:
    html = '<div class="g-recaptcha"></div><div class="other"></div>'
    assert detect(html, URL) == ()


class TestElementDetection:
    def test_recaptcha_v2_checkbox(self) -> None:
        html = f'<div class="g-recaptcha" data-sitekey="{_SITEKEY}"></div>'
        (found,) = detect(html, URL)
        assert found.kind == "recaptcha-v2"
        assert isinstance(found.challenge, RecaptchaV2Challenge)
        assert found.challenge.sitekey == _SITEKEY
        assert found.challenge.invisible is False
        assert found.challenge.pageurl == URL
        assert found.page == URL

    def test_recaptcha_v2_invisible(self) -> None:
        html = (
            f'<div class="g-recaptcha" data-sitekey="{_SITEKEY}" '
            'data-size="invisible"></div>'
        )
        (found,) = detect(html, URL)
        assert isinstance(found.challenge, RecaptchaV2Challenge)
        assert found.challenge.invisible is True

    def test_hcaptcha(self) -> None:
        html = (
            '<div class="h-captcha" data-sitekey="f06e3f9e-1a0e-4a4e-9c8e-'
            '9d8a1f9f9b0a" data-size="invisible" data-rqdata="abc"></div>'
        )
        (found,) = detect(html, URL)
        assert found.kind == "hcaptcha"
        assert isinstance(found.challenge, HCaptchaChallenge)
        assert found.challenge.is_invisible is True
        assert found.challenge.rqdata == "abc"

    def test_turnstile_with_optional_fields(self) -> None:
        html = (
            '<div class="cf-turnstile" data-sitekey="0x4AAAAAAA-e1x0myl8QqgN" '
            'data-action="login" data-c-data="cookie" '
            'data-chl-page-data="page"></div>'
        )
        (found,) = detect(html, URL)
        assert found.kind == "turnstile"
        assert isinstance(found.challenge, TurnstileChallenge)
        assert found.challenge.action == "login"
        assert found.challenge.c_data == "cookie"
        assert found.challenge.chl_page_data == "page"

    def test_funcaptcha_iframe(self) -> None:
        html = (
            '<iframe src="https://client-api.arkoselabs.com/fc/api/v2/" '
            f'data-pkey="{_PKEY}"></iframe>'
        )
        (found,) = detect(html, URL)
        assert found.kind == "funcaptcha"
        assert isinstance(found.challenge, FunCaptchaChallenge)
        assert found.challenge.public_key == _PKEY


class TestJsDetection:
    def test_grecaptcha_render_v2(self) -> None:
        html = (
            '<script>grecaptcha.render("cap", '
            f'{{sitekey: "{_SITEKEY}", size: "invisible"}});</script>'
        )
        (found,) = detect(html, URL)
        assert isinstance(found.challenge, RecaptchaV2Challenge)
        assert found.challenge.invisible is True

    def test_grecaptcha_execute_v3(self) -> None:
        html = (
            f"<script>grecaptcha.execute('{_SITEKEY}', {{action: 'login'}});</script>"
        )
        (found,) = detect(html, URL)
        assert found.kind == "recaptcha-v3"
        assert isinstance(found.challenge, RecaptchaV3Challenge)
        assert found.challenge.action == "login"

    def test_bare_execute_ignored(self) -> None:
        html = "<script>grecaptcha.execute();</script>"
        assert detect(html, URL) == ()

    def test_hcaptcha_render(self) -> None:
        html = (
            '<script>hcaptcha.render("cap", {sitekey: '
            '"f06e3f9e-1a0e-4a4e-9c8e-9d8a1f9f9b0a", size: "invisible"'
            "});</script>"
        )
        (found,) = detect(html, URL)
        assert found.kind == "hcaptcha"
        assert isinstance(found.challenge, HCaptchaChallenge)
        assert found.challenge.is_invisible is True

    def test_turnstile_render(self) -> None:
        html = (
            '<script>turnstile.render("cap", {sitekey: '
            '"0x4AAAAAAA-e1x0myl8QqgN", action: "home"});</script>'
        )
        (found,) = detect(html, URL)
        assert isinstance(found.challenge, TurnstileChallenge)
        assert found.challenge.action == "home"

    def test_init_geetest_v3(self) -> None:
        html = (
            "<script>initGeetest({"
            f"gt: '{_GT}', challenge: '{_CHALLENGE}', "
            "offline: false, new_captcha: true});</script>"
        )
        (found,) = detect(html, URL)
        assert found.kind == "geetest-v3"
        assert isinstance(found.challenge, GeeTestV3Challenge)
        assert found.challenge.gt_key == _GT
        assert found.challenge.challenge == _CHALLENGE

    def test_init_geetest_v4(self) -> None:
        html = (
            f"<script>initGeetest4({{captcha_id: '{_CAPTCHA_ID}', "
            "product: 'bind'});</script>"
        )
        (found,) = detect(html, URL)
        assert found.kind == "geetest-v4"
        assert isinstance(found.challenge, GeeTestV4Challenge)
        assert found.challenge.captcha_id == _CAPTCHA_ID

    def test_whitespace_inside_call(self) -> None:
        html = (
            "<script>\n"
            "  initGeetest4({\n"
            f"    captcha_id: '{_CAPTCHA_ID}',\n"
            "    product: 'bind'\n"
            "  });\n"
            "</script>"
        )
        (found,) = detect(html, URL)
        assert isinstance(found.challenge, GeeTestV4Challenge)


class TestOrderingAndAmbiguity:
    def test_recaptcha_v2_and_v3_both_detected_in_order(self) -> None:
        html = (
            '<div class="g-recaptcha" '
            f'data-sitekey="{_SITEKEY}"></div>'
            f"<script>grecaptcha.execute('{_SITEKEY}', "
            "{action: 'login'});</script>"
        )
        found = detect(html, URL)
        assert len(found) == 2
        assert found[0].kind == "recaptcha-v2"
        assert found[1].kind == "recaptcha-v3"

    def test_multi_instance_document_order(self) -> None:
        html = (
            '<div class="h-captcha" data-sitekey="f06e3f9e-1a0e-4a4e-9c8e-'
            '9d8a1f9f9b0a"></div>'
            '<div class="cf-turnstile" data-sitekey="0x4AAAAAAA-e1x0myl8QqgN">'
            "</div>"
        )
        found = detect(html, URL)
        assert [item.kind for item in found] == ["hcaptcha", "turnstile"]

    def test_element_before_script_order(self) -> None:
        html = (
            '<div class="g-recaptcha" '
            f'data-sitekey="{_SITEKEY}"></div>'
            f"<script>initGeetest({{gt: '{_GT}', challenge: "
            f"'{_CHALLENGE}'}});</script>"
        )
        found = detect(html, URL)
        assert [item.kind for item in found] == ["recaptcha-v2", "geetest-v3"]


def test_attribute_entity_unescape() -> None:
    html = '<div class="g-recaptcha" data-sitekey="a&amp;b"></div>'
    (found,) = detect(html, URL)
    assert found.challenge.sitekey == "a&b"


def test_detected_challenge_is_frozen() -> None:
    from dataclasses import FrozenInstanceError

    (found,) = detect(f'<div class="g-recaptcha" data-sitekey="{_SITEKEY}"></div>', URL)
    with pytest.raises(FrozenInstanceError):
        found.challenge = RecaptchaV2Challenge(  # type: ignore[misc]
            sitekey=_SITEKEY, pageurl=URL
        )
    assert isinstance(found.challenge, BaseChallenge)
