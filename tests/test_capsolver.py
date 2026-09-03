"""Capsolver adapter, challenges, solutions, facades."""

import json
from decimal import Decimal

import httpx
import pytest
import respx

from unicaptcha.errors import (
    ClientClosedError,
    EmptySolutionError,
    ErrorKind,
    InsufficientBalanceError,
    InvalidChallengeError,
    ProviderError,
)
from unicaptcha.provider.capsolver import (
    AsyncCapsolverClient,
    CapsolverAdapter,
    CapsolverClient,
    CapsolverFunCaptchaChallenge,
    CapsolverGeeTestV3Challenge,
    CapsolverGeeTestV3Solution,
    CapsolverGeeTestV4Challenge,
    CapsolverGeeTestV4Solution,
    CapsolverHCaptchaChallenge,
    CapsolverImageChallenge,
    CapsolverImageSolution,
    CapsolverRecaptchaV2Challenge,
    CapsolverRecaptchaV2Solution,
    CapsolverRecaptchaV3Challenge,
    CapsolverTurnstileChallenge,
    CapsolverTurnstileSolution,
)
from unicaptcha.types import Proxy, TaskRef, TaskStatus

BASE = "https://api.capsolver.com"
CREATE = f"{BASE}/createTask"
POLL = f"{BASE}/getTaskResult"
BALANCE = f"{BASE}/getBalance"

TASK_ID = "61138bb6-19fb-11ec-a9c8-0242ac110006"


def _j(**data: object) -> bytes:
    return json.dumps(data).encode()


def adapter() -> CapsolverAdapter:
    return CapsolverAdapter("test-key")


# -- challenges ----------------------------------------------------------


def test_v3_rejects_enterprise() -> None:
    with pytest.raises(InvalidChallengeError):
        CapsolverRecaptchaV3Challenge(sitekey="k", pageurl="u", is_enterprise=True)


def test_turnstile_rejects_chl_page_data() -> None:
    with pytest.raises(InvalidChallengeError):
        CapsolverTurnstileChallenge(sitekey="t", pageurl="u", chl_page_data="x")


def test_all_challenges_construct() -> None:
    proxy = Proxy(host="1.2.3.4", port=8080)
    CapsolverImageChallenge(b"png", module="common")
    CapsolverRecaptchaV2Challenge(sitekey="k", pageurl="u")
    CapsolverRecaptchaV3Challenge(sitekey="k", pageurl="u")
    CapsolverHCaptchaChallenge(sitekey="k", pageurl="u")
    CapsolverFunCaptchaChallenge(public_key="pk", pageurl="u")
    CapsolverGeeTestV3Challenge(gt_key="g", challenge="c", pageurl="u")
    CapsolverGeeTestV4Challenge(captcha_id="cid", pageurl="u")
    CapsolverTurnstileChallenge(sitekey="t", pageurl="u")
    CapsolverRecaptchaV2Challenge(sitekey="k", pageurl="u", proxy=proxy)


# -- adapter payloads -----------------------------------------------------


def test_image_payload() -> None:
    task = adapter().build_payload(CapsolverImageChallenge(b"img", module="number"))[
        "task"
    ]
    assert task == {"type": "ImageToTextTask", "body": "aW1n", "module": "number"}


def test_recaptcha_v2_proxyless_vs_proxy_and_enterprise() -> None:
    a = adapter()
    base = a.build_payload(
        CapsolverRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            data_s={"s": "tok"},
            action="submit",
            api_domain="www.recaptcha.net",
            invisible=True,
        )
    )["task"]
    assert base["type"] == "ReCaptchaV2TaskProxyLess"
    assert base["recaptchaDataSValue"] == "tok"
    assert base["pageAction"] == "submit"
    assert base["apiDomain"] == "www.recaptcha.net"
    assert base["isInvisible"] is True

    ent = a.build_payload(
        CapsolverRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            is_enterprise=True,
            data_s={"s": "tok"},
        )
    )["task"]
    assert ent["type"] == "ReCaptchaV2EnterpriseTaskProxyLess"
    assert ent["enterprisePayload"] == {"s": "tok"}
    assert "recaptchaDataSValue" not in ent

    proxied = a.build_payload(
        CapsolverRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            proxy=Proxy(host="p.h", port=3128, username="u", password="p"),
        )
    )["task"]
    assert proxied["type"] == "ReCaptchaV2Task"
    assert proxied["proxyType"] == "http"
    assert proxied["proxyAddress"] == "p.h"
    assert proxied["proxyLogin"] == "u"


def test_recaptcha_v3_proxyless_only() -> None:
    task = adapter().build_payload(
        CapsolverRecaptchaV3Challenge(
            sitekey="sk", pageurl="pu", action="verify", min_score=0.9
        )
    )["task"]
    assert task["type"] == "ReCaptchaV3TaskProxyLess"
    assert task["pageAction"] == "verify"
    assert task["minScore"] == 0.9
    for absent in ("proxyType", "userAgent", "cookies"):
        assert absent not in task


def test_hcaptcha_funcaptcha_geetest_turnstile_payloads() -> None:
    a = adapter()
    hcap = a.build_payload(
        CapsolverHCaptchaChallenge(sitekey="h", pageurl="u", rqdata="rq")
    )["task"]
    assert hcap["type"] == "HCaptchaTaskProxyLess"
    assert hcap["rqdata"] == "rq"

    fun = a.build_payload(CapsolverFunCaptchaChallenge(public_key="PK", pageurl="u"))[
        "task"
    ]
    assert fun["type"] == "FunCaptchaTaskProxyLess"
    assert fun["websitePublicKey"] == "PK"

    gv3 = a.build_payload(
        CapsolverGeeTestV3Challenge(
            gt_key="gt", challenge="ch", pageurl="u", api_server="api.gt"
        )
    )["task"]
    assert gv3["type"] == "GeeTestTaskProxyLess"
    assert gv3["gt"] == "gt"
    assert gv3["challenge"] == "ch"
    assert gv3["geetestApiServerSubdomain"] == "api.gt"

    gv4 = a.build_payload(
        CapsolverGeeTestV4Challenge(captcha_id="cid", pageurl="u", risk_type="slide")
    )["task"]
    assert gv4["type"] == "GeeTestTaskProxyLess"
    assert gv4["captchaId"] == "cid"
    assert gv4["riskType"] == "slide"

    ts = a.build_payload(
        CapsolverTurnstileChallenge(
            sitekey="ts", pageurl="u", action="act", c_data="cd"
        )
    )["task"]
    assert ts["type"] == "AntiTurnstileTaskProxyLess"
    assert ts["metadata"] == {"action": "act", "cdata": "cd"}


def test_no_softid_emitted() -> None:
    # Capsolver has no affiliate-id field; referral accepted but inert.
    payload = adapter().build_payload(CapsolverImageChallenge(b"png"))
    assert set(payload) == {"clientKey", "task"}


# -- response parsing ------------------------------------------------------


def test_string_task_id_accepted() -> None:
    accepted = adapter().parse_submit_response(_j(errorId=0, taskId=TASK_ID))
    assert accepted.task_id == TASK_ID
    assert isinstance(accepted.task_id, str)
    numeric = adapter().parse_submit_response(_j(errorId=0, taskId="123"))
    assert numeric.task_id == 123
    assert isinstance(numeric.task_id, int)


def test_instant_ready_fast_path() -> None:
    raw = _j(
        errorId=0,
        status="ready",
        taskId=TASK_ID,
        solution={"text": "44795sds"},
    )
    accepted = adapter().parse_submit_response(raw)
    assert accepted.instant_answer is not None
    instant = accepted.instant_answer
    assert instant.state is TaskStatus.READY
    assert isinstance(instant.solution, CapsolverImageSolution)
    assert instant.solution.text == "44795sds"


def test_status_states_and_failed() -> None:
    a = adapter()
    assert a.parse_task_status(_j(errorId=0, status="processing")).state is (
        TaskStatus.PENDING
    )
    ready = a.parse_task_status(
        _j(errorId=0, status="ready", solution={"gRecaptchaResponse": "tok123456"})
    )
    assert ready.state is TaskStatus.READY
    assert isinstance(ready.solution, CapsolverRecaptchaV2Solution)
    failed = a.parse_task_status(_j(errorId=0, status="failed"))
    assert failed.state is TaskStatus.NO_SOLUTION
    unknown = a.parse_task_status(_j(errorId=16, errorCode="ERROR_TASK_NOT_FOUND"))
    assert unknown.state is TaskStatus.UNKNOWN


def test_solution_dispatch_with_type_disambiguation() -> None:
    a = adapter()
    ts = a._solution_from({"token": "t", "type": "turnstile", "userAgent": "UA"})
    assert isinstance(ts, CapsolverTurnstileSolution)
    gv3 = a._solution_from({"challenge": "c", "validate": "v", "seccode": "s"})
    assert isinstance(gv3, CapsolverGeeTestV3Solution)
    gv4 = a._solution_from(
        {
            "captcha_id": "i",
            "lot_number": "l",
            "pass_token": "p",
            "gen_time": "1",
            "captcha_output": "o",
        }
    )
    assert isinstance(gv4, CapsolverGeeTestV4Solution)
    with pytest.raises(EmptySolutionError):
        a._solution_from({"bogus": 1})


def test_balance_and_error_mapping() -> None:
    a = adapter()
    assert a.parse_balance(_j(errorId=0, balance=1234567)) == Decimal("1234567")
    with pytest.raises(InsufficientBalanceError):
        a.parse_balance(_j(errorId=1, errorCode="ERROR_ZERO_BALANCE"))
    kind, message = a.map_provider_error(
        _j(errorId=1, errorCode="ERROR_TOO_MANY_REQUESTS", errorDescription="slow")
    )
    assert kind is ErrorKind.RATE_LIMIT
    assert message == "slow"


def test_malformed_json_chains_provider_error() -> None:
    with pytest.raises(ProviderError) as excinfo:
        adapter().parse_submit_response(b"not json")
    assert isinstance(excinfo.value.__cause__, ValueError)


# -- facades ----------------------------------------------------------------


@respx.mock
def test_sync_facade_instant_image(fast_time, fast_retry) -> None:
    respx.post(CREATE).mock(
        return_value=httpx.Response(
            200,
            content=_j(
                errorId=0,
                status="ready",
                taskId=TASK_ID,
                solution={"text": "hello"},
            ),
        )
    )
    with CapsolverClient("test-key", time=fast_time, retry=fast_retry) as client:
        result = client.solve_image(b"png", module="common")
    assert result.task_id == TASK_ID
    assert result.solution.text == "hello"


@respx.mock
@pytest.mark.asyncio
async def test_async_facade_solve(fast_time, fast_retry) -> None:
    respx.post(CREATE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, taskId=TASK_ID))
    )
    respx.post(POLL).mock(
        return_value=httpx.Response(
            200,
            content=_j(
                errorId=0,
                status="ready",
                solution={"challenge": "c", "validate": "v", "seccode": "s"},
            ),
        )
    )
    async with AsyncCapsolverClient(
        "test-key", time=fast_time, retry=fast_retry
    ) as client:
        result = await client.solve_geetest_v3(
            gt_key="g", challenge="c0", pageurl="https://page"
        )
    assert isinstance(result.solution, CapsolverGeeTestV3Solution)


@respx.mock
def test_facade_rejects_wrong_provider_and_closed_use() -> None:
    respx.post(POLL).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, status="processing"))
    )
    with CapsolverClient("test-key") as client:
        foreign = TaskRef(provider="other", task_id=1)
        with pytest.raises(TypeError):
            client.get_task_status(foreign)
        status = client.get_task_status(TASK_ID)
        assert status.task_id == TASK_ID
    with pytest.raises(ClientClosedError):
        client.get_balance()
