"""Solver.auto_solve / AsyncSolver.auto_solve tests (ADR-0077)."""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal

import httpx
import pytest
import respx

from unicaptcha import (
    AsyncSolver,
    AutoSolveResult,
    ClientClosedError,
    ErrorKind,
    InvalidChallengeError,
    NoCaptchaDetectedError,
    Solver,
)
from unicaptcha._internal.fill import build_fill
from unicaptcha.provider.twocaptcha import (
    TwoCaptchaAdapter,
    TwoCaptchaFunCaptchaSolution,
    TwoCaptchaGeeTestV3Solution,
    TwoCaptchaGeeTestV4Solution,
    TwoCaptchaHCaptchaSolution,
    TwoCaptchaRecaptchaV2Solution,
    TwoCaptchaRecaptchaV3Solution,
    TwoCaptchaTurnstileSolution,
)
from unicaptcha.types import TaskRef, TimeConfig

BASE = "https://api.2captcha.com"
CREATE = f"{BASE}/createTask"
POLL = f"{BASE}/getTaskResult"

_SITEKEY = "6Lc2wvkSAAAAAKGZfA8mF6J7kd5U3lGiPNvzY6j"
URL = "https://example.com/login"

FAST_TIME = TimeConfig(poll_delay=0.0, poll_interval=0.01, total_timeout=1.0)


def _j(**data: object) -> bytes:
    return json.dumps(data).encode()


def _mock_solve(token: str = "03AGdBq7solved-token") -> None:
    respx.post(CREATE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, taskId=99))
    )
    respx.post(POLL).mock(
        return_value=httpx.Response(
            200,
            content=_j(
                errorId=0,
                status="ready",
                cost="0.00025",
                solution={"gRecaptchaResponse": token},
            ),
        )
    )


RECAPTCHA_V2_HTML = (
    f'<form><div class="g-recaptcha" data-sitekey="{_SITEKEY}"></div></form>'
)


class TestBuildFill:
    """Selector mapping per solved kind (no network)."""

    def test_recaptcha_v2_and_v3(self) -> None:
        assert build_fill(TwoCaptchaRecaptchaV2Solution("tok")) == {
            "#g-recaptcha-response": "tok"
        }
        assert build_fill(TwoCaptchaRecaptchaV3Solution("tok")) == {
            "#g-recaptcha-response": "tok"
        }

    def test_hcaptcha(self) -> None:
        assert build_fill(TwoCaptchaHCaptchaSolution("tok")) == {
            "textarea[name=h-captcha-response]": "tok"
        }

    def test_turnstile(self) -> None:
        assert build_fill(TwoCaptchaTurnstileSolution("tok")) == {
            "input[name=cf-turnstile-response]": "tok"
        }

    def test_funcaptcha_empty(self) -> None:
        assert build_fill(TwoCaptchaFunCaptchaSolution("tok")) == {}

    def test_geetest_v3(self) -> None:
        sol = TwoCaptchaGeeTestV3Solution(challenge="c", validate="v", seccode="s")
        assert build_fill(sol) == {
            "#geetest_challenge": "c",
            "#geetest_validate": "v",
            "#geetest_seccode": "s",
        }

    def test_geetest_v4(self) -> None:
        sol = TwoCaptchaGeeTestV4Solution(
            captcha_id="id",
            lot_number="lot",
            pass_token="pass",
            gen_time="123",
            captcha_output="out",
        )
        assert build_fill(sol) == {
            "#geetest_lot_number": "lot",
            "#geetest_pass_token": "pass",
            "#geetest_gen_time": "123",
            "#geetest_captcha_output": "out",
        }


class TestSyncAutoSolve:
    @respx.mock
    def test_happy_path(self) -> None:
        _mock_solve()
        with Solver([TwoCaptchaAdapter("test-key")], time=FAST_TIME) as solver:
            auto = solver.auto_solve(RECAPTCHA_V2_HTML, URL)
        assert isinstance(auto, AutoSolveResult)
        assert auto.detected.kind == "recaptcha-v2"
        assert auto.detected.page == URL
        assert isinstance(auto.result.solution, TwoCaptchaRecaptchaV2Solution)
        assert auto.fill == {"#g-recaptcha-response": "03AGdBq7solved-token"}
        assert auto.result.task_ref == TaskRef("twocaptcha", 99)
        assert auto.result.cost == Decimal("0.00025")

    def test_no_detection_raises(self) -> None:
        with (
            Solver([TwoCaptchaAdapter("test-key")], time=FAST_TIME) as solver,
            pytest.raises(NoCaptchaDetectedError) as exc,
        ):
            solver.auto_solve("<html><body></body></html>", URL)
        assert exc.value.kind is ErrorKind.NO_CAPTCHA_DETECTED

    @respx.mock
    def test_provider_pinned(self) -> None:
        _mock_solve()
        with Solver([TwoCaptchaAdapter("test-key")], time=FAST_TIME) as solver:
            auto = solver.auto_solve(RECAPTCHA_V2_HTML, URL, provider="twocaptcha")
        assert auto.fill

    def test_unknown_provider_is_type_error(self) -> None:
        with (
            Solver([TwoCaptchaAdapter("test-key")], time=FAST_TIME) as solver,
            pytest.raises(TypeError),
        ):
            solver.auto_solve(RECAPTCHA_V2_HTML, URL, provider="nope")

    def test_closed_client_raises(self) -> None:
        solver = Solver([TwoCaptchaAdapter("test-key")], time=FAST_TIME)
        solver.close()
        with pytest.raises(ClientClosedError):
            solver.auto_solve(RECAPTCHA_V2_HTML, URL)

    def test_bad_arguments(self) -> None:
        with Solver([TwoCaptchaAdapter("test-key")], time=FAST_TIME) as solver:
            with pytest.raises(TypeError):
                solver.auto_solve(b"<html>", URL)  # type: ignore[arg-type]
            with pytest.raises(InvalidChallengeError):
                solver.auto_solve(RECAPTCHA_V2_HTML, "")

    @respx.mock
    def test_repr_truncates_fill_values(self) -> None:
        _mock_solve(token="0123456789abcdef")
        with Solver([TwoCaptchaAdapter("test-key")], time=FAST_TIME) as solver:
            auto = solver.auto_solve(RECAPTCHA_V2_HTML, URL)
        assert "***cdef" in repr(auto)
        assert "0123456789abcdef" not in repr(auto)


class TestAsyncAutoSolve:
    @respx.mock
    def test_happy_path(self) -> None:
        _mock_solve()

        async def run() -> AutoSolveResult:
            async with AsyncSolver(
                [TwoCaptchaAdapter("test-key")], time=FAST_TIME
            ) as solver:
                return await solver.auto_solve(RECAPTCHA_V2_HTML, URL)

        auto = asyncio.run(run())
        assert auto.detected.kind == "recaptcha-v2"
        assert auto.fill == {"#g-recaptcha-response": "03AGdBq7solved-token"}

    def test_no_detection_raises(self) -> None:
        async def run() -> None:
            async with AsyncSolver(
                [TwoCaptchaAdapter("test-key")], time=FAST_TIME
            ) as solver:
                await solver.auto_solve("<html></html>", URL)

        with pytest.raises(NoCaptchaDetectedError):
            asyncio.run(run())
