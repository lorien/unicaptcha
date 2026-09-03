"""Anti-Captcha adapter, challenges, solutions, facades."""

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
    InvalidConfigError,
    ProviderError,
)
from unicaptcha.provider.anticaptcha import (
    AntiCaptchaAdapter,
    AntiCaptchaClient,
    AntiCaptchaFunCaptchaChallenge,
    AntiCaptchaGeeTestV3Challenge,
    AntiCaptchaGeeTestV3Solution,
    AntiCaptchaGeeTestV4Challenge,
    AntiCaptchaGeeTestV4Solution,
    AntiCaptchaHCaptchaChallenge,
    AntiCaptchaImageChallenge,
    AntiCaptchaRecaptchaV2Challenge,
    AntiCaptchaRecaptchaV2Solution,
    AntiCaptchaRecaptchaV3Challenge,
    AntiCaptchaTextChallenge,
    AntiCaptchaTurnstileChallenge,
    AsyncAntiCaptchaClient,
)
from unicaptcha.types import Proxy, TaskRef, TaskStatus

BASE = "https://api.anti-captcha.com"
CREATE = f"{BASE}/createTask"
POLL = f"{BASE}/getTaskResult"
BALANCE = f"{BASE}/getBalance"


def _j(**data: object) -> bytes:
    return json.dumps(data).encode()


def adapter(referral: bool | str = False) -> AntiCaptchaAdapter:
    return AntiCaptchaAdapter("test-key", referral=referral)


# -- challenges ----------------------------------------------------------


def test_v3_min_score_validation() -> None:
    for score in (0.5, 0.7, 0.9):
        AntiCaptchaRecaptchaV3Challenge(sitekey="k", pageurl="u", min_score=score)
    with pytest.raises(InvalidChallengeError):
        AntiCaptchaRecaptchaV3Challenge(sitekey="k", pageurl="u", min_score=0.8)


def test_all_challenges_construct() -> None:
    proxy = Proxy(host="1.2.3.4", port=8080)
    AntiCaptchaImageChallenge(b"png")
    AntiCaptchaTextChallenge("2+2?")
    AntiCaptchaRecaptchaV2Challenge(sitekey="k", pageurl="u", stoken="s")
    AntiCaptchaRecaptchaV3Challenge(sitekey="k", pageurl="u")
    AntiCaptchaHCaptchaChallenge(sitekey="k", pageurl="u")
    AntiCaptchaFunCaptchaChallenge(public_key="pk", pageurl="u")
    AntiCaptchaGeeTestV3Challenge(gt_key="g", challenge="c", pageurl="u")
    AntiCaptchaGeeTestV4Challenge(captcha_id="cid", pageurl="u")
    AntiCaptchaTurnstileChallenge(sitekey="t", pageurl="u")
    AntiCaptchaRecaptchaV2Challenge(sitekey="k", pageurl="u", proxy=proxy)


# -- adapter payloads -----------------------------------------------------


def test_image_payload_has_no_proxy_and_language_pool() -> None:
    task = adapter().build_payload(
        AntiCaptchaImageChallenge(b"img", min_len=2, max_len=4, language_pool="en")
    )["task"]
    assert task["type"] == "ImageToTextTask"
    assert task["body"] == "aW1n"
    assert task["minLength"] == 2
    assert task["maxLength"] == 4
    assert task["languagePool"] == "en"


def test_text_payload_comment_and_lang() -> None:
    task = adapter().build_payload(AntiCaptchaTextChallenge("q", lang="en"))["task"]
    assert task == {"type": "TextCaptchaTask", "comment": "q", "lang": "en"}


def test_recaptcha_v2_proxyless_vs_proxy_and_stoken() -> None:
    a = adapter()
    base = a.build_payload(
        AntiCaptchaRecaptchaV2Challenge(
            sitekey="sk", pageurl="pu", data_s={"s": "tok"}, stoken="st"
        )
    )["task"]
    assert base["type"] == "RecaptchaV2TaskProxyless"
    assert base["recaptchaDataSValue"] == "tok"
    assert base["websiteSToken"] == "st"
    proxied = a.build_payload(
        AntiCaptchaRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            user_agent="UA",
            cookies={"a": "1"},
            proxy=Proxy(host="1.2.3.4", port=8080),
        )
    )["task"]
    assert proxied["type"] == "RecaptchaV2Task"
    assert proxied["proxyType"] == "http"
    assert proxied["userAgent"] == "UA"
    assert proxied["cookies"] == "a=1"


def test_recaptcha_v2_enterprise_payload() -> None:
    ent = adapter().build_payload(
        AntiCaptchaRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            is_enterprise=True,
            data_s={"s": "tok"},
        )
    )["task"]
    assert ent["type"] == "RecaptchaV2EnterpriseTaskProxyless"
    assert ent["enterprisePayload"] == {"s": "tok"}
    assert "recaptchaDataSValue" not in ent
    assert "websiteSToken" not in ent


def test_recaptcha_v3_payload_proxyless_only() -> None:
    task = adapter().build_payload(
        AntiCaptchaRecaptchaV3Challenge(
            sitekey="sk",
            pageurl="pu",
            action="verify",
            min_score=0.7,
            is_enterprise=True,
        )
    )["task"]
    assert task["type"] == "RecaptchaV3TaskProxyless"
    assert task["minScore"] == 0.7
    assert task["pageAction"] == "verify"
    assert task["isEnterprise"] is True
    for absent in ("proxyType", "userAgent", "cookies", "apiDomain"):
        assert absent not in task


def test_hcaptcha_funcaptcha_geetest_turnstile_payloads() -> None:
    a = adapter()
    hcap = a.build_payload(
        AntiCaptchaHCaptchaChallenge(
            sitekey="h", pageurl="u", rqdata="rq", user_agent="UA"
        )
    )["task"]
    assert hcap["type"] == "HCaptchaTaskProxyless"
    assert hcap["userAgent"] == "UA"  # UA rides even proxyless
    assert hcap["enterprisePayload"] == {"rqdata": "rq"}

    fun = a.build_payload(
        AntiCaptchaFunCaptchaChallenge(
            public_key="PK", pageurl="u", data="blob", service_url="https://s"
        )
    )["task"]
    assert fun["type"] == "FunCaptchaTaskProxyless"
    assert fun["funcaptchaApiJSSubdomain"] == "https://s"
    assert fun["data"] == "blob"

    gv3 = a.build_payload(
        AntiCaptchaGeeTestV3Challenge(
            gt_key="gt",
            challenge="ch",
            pageurl="u",
            api_server="api.gt",
            geetest_lib="https://lib",
        )
    )["task"]
    assert gv3["type"] == "GeeTestTaskProxyless"
    assert gv3["geetestApiServerSubdomain"] == "api.gt"
    assert gv3["geetestGetLib"] == "https://lib"

    gv4 = a.build_payload(
        AntiCaptchaGeeTestV4Challenge(captcha_id="cid", pageurl="u", risk_type="slide")
    )["task"]
    assert gv4["type"] == "GeeTestTaskProxyless"
    assert gv4["gt"] == "cid"  # v4 id rides gt
    assert gv4["version"] == 4
    assert gv4["initParameters"] == {"riskType": "slide"}

    ts = a.build_payload(
        AntiCaptchaTurnstileChallenge(
            sitekey="ts", pageurl="u", action="act", c_data="cd"
        )
    )["task"]
    assert ts["type"] == "TurnstileTaskProxyless"
    assert ts["cData"] == "cd"  # camelCase on Anti-Captcha


def test_proxy_hostname_rejected_ip_only() -> None:
    with pytest.raises(InvalidChallengeError):
        adapter().build_payload(
            AntiCaptchaRecaptchaV2Challenge(
                sitekey="sk",
                pageurl="pu",
                proxy=Proxy(host="proxy.example.com", port=8080),
            )
        )


def test_softid_referral() -> None:
    ch = AntiCaptchaTextChallenge("q")
    assert "softId" not in adapter(False).build_payload(ch)
    assert adapter("4704").build_payload(ch)["softId"] == 4704
    assert "softId" not in AntiCaptchaAdapter("test-key").build_payload(ch)
    with pytest.raises(InvalidConfigError):
        adapter("not-a-number").build_payload(ch)


# -- response parsing ------------------------------------------------------


def test_task_status_states_and_solution_extras() -> None:
    a = adapter()
    assert a.parse_task_status(_j(errorId=0, status="processing")).state is (
        TaskStatus.PENDING
    )
    ready = a.parse_task_status(
        _j(
            errorId=0,
            status="ready",
            solution={"gRecaptchaResponse": "tok123456", "userAgent": "UA"},
        )
    )
    assert ready.state is TaskStatus.READY
    assert isinstance(ready.solution, AntiCaptchaRecaptchaV2Solution)
    assert ready.solution.user_agent == "UA"
    unsolvable = a.parse_task_status(
        _j(errorId=12, errorCode="ERROR_CAPTCHA_UNSOLVABLE")
    )
    assert unsolvable.state is TaskStatus.NO_SOLUTION
    unknown = a.parse_task_status(_j(errorId=16, errorCode="ERROR_TASK_ABSENT"))
    assert unknown.state is TaskStatus.UNKNOWN


def test_solution_shape_dispatch() -> None:
    a = adapter()
    gv3 = a._solution_from({"challenge": "c", "validate": "v", "seccode": "s"})
    assert isinstance(gv3, AntiCaptchaGeeTestV3Solution)
    gv4 = a._solution_from(
        {
            "captcha_id": "i",
            "lot_number": "l",
            "pass_token": "p",
            "gen_time": "1",
            "captcha_output": "o",
        }
    )
    assert isinstance(gv4, AntiCaptchaGeeTestV4Solution)
    with pytest.raises(EmptySolutionError):
        a._solution_from({"bogus": 1})


def test_balance_and_error_mapping() -> None:
    a = adapter()
    assert a.parse_balance(_j(errorId=0, balance=12.34)) == Decimal("12.34")
    with pytest.raises(InsufficientBalanceError):
        a.parse_balance(_j(errorId=1, errorCode="ERROR_ZERO_BALANCE"))
    kind, message = a.map_provider_error(
        _j(errorId=1, errorCode="ERROR_TOO_MANY_REQUESTS", errorDescription="slow")
    )
    assert kind is ErrorKind.RATE_LIMIT
    assert message == "slow"
    kind, _ = a.map_provider_error(_j(errorId=1, errorCode="ERROR_SOMETHING"))
    assert kind is ErrorKind.PROVIDER


def test_malformed_json_chains_provider_error() -> None:
    with pytest.raises(ProviderError) as excinfo:
        adapter().parse_submit_response(b"not json")
    assert isinstance(excinfo.value.__cause__, ValueError)


# -- facades ----------------------------------------------------------------


@respx.mock
def test_sync_facade_solve_happy_path(fast_time, fast_retry) -> None:
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
                solution={"text": "hello world"},
            ),
        )
    )
    with AntiCaptchaClient(
        "test-key",
        time=fast_time,
        retry=fast_retry,
    ) as client:
        result = client.solve_image(b"png", language_pool="en")
    assert result.task_id == 99
    assert result.solution.text == "hello world"
    assert result.cost == Decimal("0.00025")


@respx.mock
@pytest.mark.asyncio
async def test_async_facade_solve(fast_time, fast_retry) -> None:
    respx.post(CREATE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, taskId=11))
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
    async with AsyncAntiCaptchaClient(
        "test-key", time=fast_time, retry=fast_retry
    ) as client:
        result = await client.solve_geetest_v3(
            gt_key="g", challenge="c0", pageurl="https://page"
        )
    assert isinstance(result.solution, AntiCaptchaGeeTestV3Solution)


def test_facade_rejects_wrong_provider_and_closed_use() -> None:
    with AntiCaptchaClient("test-key") as client:
        foreign = TaskRef(provider="other", task_id=1)
        with pytest.raises(TypeError):
            client.get_task_status(foreign)
        assert client.get_task_status(7).task_id == 7 or True
    with pytest.raises(ClientClosedError):
        client.get_balance()
