"""Live 2Captcha integration tests against real workers (ADR-0019).

Gated by the ``integration`` marker: deselected by default
(``addopts = -m 'not integration'``). Requires a real API key in
``UNICAPTCHA_TWOCAPTCHA_API_KEY`` (in-code provider name ``twocaptcha``);
tests skip (not fail) when the key is absent. Real solves deduct credits —
run manually, never in CI.

Demo sitekeys are public 2Captcha demo pages; the image fixture is a
generated text captcha committed under ``tests/fixtures/``.
"""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from unicaptcha.errors import AuthenticationError
from unicaptcha.provider.twocaptcha import (
    AsyncTwoCaptchaClient,
    TwoCaptchaClient,
)
from unicaptcha.types import RetryConfig, TimeConfig

API_KEY_ENV = "UNICAPTCHA_TWOCAPTCHA_API_KEY"

RECAPTCHA_V2_SITEKEY = "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u"
RECAPTCHA_V2_PAGEURL = "https://2captcha.com/demo/recaptcha-v2"
TURNSTILE_SITEKEY = "3x00000000000000000000FF"
TURNSTILE_PAGEURL = "https://2captcha.com/demo/cloudflare-turnstile"

FIXTURES = Path(__file__).parent / "fixtures"
CAPTCHA_IMAGE = FIXTURES / "captcha.png"

# Real solves are slow; budget generously and poll at 2captcha's 5s cadence.
LIVE_TIME = TimeConfig(total_timeout=180.0, poll_interval=5.0, poll_delay=2.0)
LIVE_RETRY = RetryConfig(max_attempts=3, backoff_base=2.0, backoff_cap=10.0)

pytestmark = pytest.mark.integration


def _api_key() -> str:
    key = os.environ.get(API_KEY_ENV)
    if not key:
        pytest.skip(
            f"set {API_KEY_ENV} to run live 2Captcha integration tests "
            "(solves deduct real credits)"
        )
    return key


@pytest.fixture
def api_key() -> str:
    return _api_key()


def test_recaptcha_v2_solve(api_key: str) -> None:
    with TwoCaptchaClient(api_key, time=LIVE_TIME, retry=LIVE_RETRY) as client:
        result = client.solve_recaptcha_v2(
            sitekey=RECAPTCHA_V2_SITEKEY,
            pageurl=RECAPTCHA_V2_PAGEURL,
        )
    assert result.solution.token
    assert result.task_id is not None


def test_turnstile_solve(api_key: str) -> None:
    with TwoCaptchaClient(api_key, time=LIVE_TIME, retry=LIVE_RETRY) as client:
        result = client.solve_turnstile(
            sitekey=TURNSTILE_SITEKEY,
            pageurl=TURNSTILE_PAGEURL,
        )
    assert result.solution.token
    assert result.task_id is not None


def test_image_solve(api_key: str) -> None:
    body = CAPTCHA_IMAGE.read_bytes()
    with TwoCaptchaClient(api_key, time=LIVE_TIME, retry=LIVE_RETRY) as client:
        result = client.solve_image(body)
    assert result.solution.text
    assert result.task_id is not None


@pytest.mark.asyncio
async def test_async_recaptcha_v2_solve(api_key: str) -> None:
    async with AsyncTwoCaptchaClient(
        api_key, time=LIVE_TIME, retry=LIVE_RETRY
    ) as client:
        result = await client.solve_recaptcha_v2(
            sitekey=RECAPTCHA_V2_SITEKEY,
            pageurl=RECAPTCHA_V2_PAGEURL,
        )
    assert result.solution.token
    assert result.task_id is not None


def test_get_balance(api_key: str) -> None:
    with TwoCaptchaClient(api_key) as client:
        balance = client.get_balance()
    assert isinstance(balance, Decimal)
    assert balance >= 0


def test_wrong_key_rejected() -> None:
    with (
        TwoCaptchaClient("definitely-wrong-key") as client,
        pytest.raises(AuthenticationError),
    ):
        client.get_balance()


def test_test_endpoint_echoes_payload(api_key: str) -> None:
    payload = {
        "clientKey": api_key,
        "foo": "bar",
        "test": True,
    }
    response = httpx.post("https://api.2captcha.com/test", json=payload, timeout=30.0)
    response.raise_for_status()
    assert "foo" in response.text
    assert "bar" in response.text
