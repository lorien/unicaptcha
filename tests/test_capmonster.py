"""CapMonster adapter, challenges, solutions, facades."""

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
from unicaptcha.provider.capmonster import (
    AsyncCapMonsterClient,
    CapMonsterAdapter,
    CapMonsterClient,
    CapMonsterFunCaptchaChallenge,
    CapMonsterGeeTestV3Challenge,
    CapMonsterGeeTestV3Solution,
    CapMonsterGeeTestV4Challenge,
    CapMonsterGeeTestV4Solution,
    CapMonsterHCaptchaChallenge,
    CapMonsterImageChallenge,
    CapMonsterRecaptchaV2Challenge,
    CapMonsterRecaptchaV2Solution,
    CapMonsterRecaptchaV3Challenge,
    CapMonsterTurnstileChallenge,
)
from unicaptcha.types import TaskRef, TaskStatus

BASE = "https://api.capmonster.cloud"
CREATE = f"{BASE}/createTask"
POLL = f"{BASE}/getTaskResult"
BALANCE = f"{BASE}/getBalance"


def _j(**data: object) -> bytes:
    return json.dumps(data).encode()


def adapter(referral: bool | str = False) -> CapMonsterAdapter:
    return CapMonsterAdapter("test-key", referral=referral)


# -- challenges ----------------------------------------------------------


def test_image_challenge_validations() -> None:
    CapMonsterImageChallenge(b"png", module_name="google", threshold=80, numeric=1)
    with pytest.raises(InvalidChallengeError):
        CapMonsterImageChallenge(b"png", module_name="bogus")
    with pytest.raises(InvalidChallengeError):
        CapMonsterImageChallenge(b"png", threshold=101)
    with pytest.raises(InvalidChallengeError):
        CapMonsterImageChallenge(b"png", numeric=2)


def test_v3_min_score_range() -> None:
    CapMonsterRecaptchaV3Challenge(sitekey="k", pageurl="u", min_score=0.5)
    with pytest.raises(InvalidChallengeError):
        CapMonsterRecaptchaV3Challenge(sitekey="k", pageurl="u", min_score=1.0)


def test_turnstile_token_only() -> None:
    CapMonsterTurnstileChallenge(sitekey="t", pageurl="u", cloudflare_task_type="token")
    with pytest.raises(InvalidChallengeError):
        CapMonsterTurnstileChallenge(
            sitekey="t", pageurl="u", cloudflare_task_type="cf_clearance"
        )


def test_all_challenges_construct() -> None:
    CapMonsterImageChallenge(b"png")
    CapMonsterRecaptchaV2Challenge(sitekey="k", pageurl="u")
    CapMonsterRecaptchaV3Challenge(sitekey="k", pageurl="u")
    CapMonsterHCaptchaChallenge(sitekey="k", pageurl="u")
    CapMonsterFunCaptchaChallenge(public_key="pk", pageurl="u")
    CapMonsterGeeTestV3Challenge(gt_key="g", challenge="c", pageurl="u")
    CapMonsterGeeTestV4Challenge(captcha_id="cid", pageurl="u")
    CapMonsterTurnstileChallenge(sitekey="t", pageurl="u")


# -- adapter payloads -----------------------------------------------------


def test_image_payload() -> None:
    task = adapter().build_payload(
        CapMonsterImageChallenge(b"img", module_name="google", threshold=80, case=True)
    )["task"]
    assert task == {
        "type": "ImageToTextTask",
        "body": "aW1n",
        "CapMonsterModule": "google",
        "recognizingThreshold": 80,
        "Case": True,
    }


def test_recaptcha_v2_classic_and_enterprise() -> None:
    a = adapter()
    classic = a.build_payload(
        CapMonsterRecaptchaV2Challenge(
            sitekey="sk", pageurl="pu", data_s={"s": "tok"}, invisible=True
        )
    )["task"]
    assert classic["type"] == "RecaptchaV2Task"
    assert classic["recaptchaDataSValue"] == "tok"
    assert classic["isInvisible"] is True

    ent = a.build_payload(
        CapMonsterRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            is_enterprise=True,
            data_s={"s": "tok"},
            api_domain="recaptcha.net",
            action="login",
        )
    )["task"]
    assert ent["type"] == "RecaptchaV2EnterpriseTask"
    assert ent["enterprisePayload"] == {"s": "tok"}
    assert ent["apiDomain"] == "recaptcha.net"
    assert ent["pageAction"] == "login"


def test_recaptcha_v3_enterprise_separate_type() -> None:
    a = adapter()
    plain = a.build_payload(
        CapMonsterRecaptchaV3Challenge(
            sitekey="sk", pageurl="pu", min_score=0.7, action="verify"
        )
    )["task"]
    assert plain["type"] == "RecaptchaV3TaskProxyless"
    assert plain["minScore"] == 0.7
    assert plain["pageAction"] == "verify"
    ent = a.build_payload(
        CapMonsterRecaptchaV3Challenge(sitekey="sk", pageurl="pu", is_enterprise=True)
    )["task"]
    assert ent["type"] == "RecaptchaV3EnterpriseTask"
    for absent in ("proxyType", "userAgent", "cookies"):
        assert absent not in ent


def test_hcaptcha_funcaptcha_geetest_turnstile_payloads() -> None:
    a = adapter()
    hcap = a.build_payload(
        CapMonsterHCaptchaChallenge(
            sitekey="h", pageurl="u", rqdata="rq", fallback_to_actual_ua=True
        )
    )["task"]
    assert hcap["type"] == "HCaptchaTask"
    assert hcap["data"] == "rq"  # rqdata rides the wire `data` field
    assert hcap["fallbackToActualUA"] is True

    fun = a.build_payload(
        CapMonsterFunCaptchaChallenge(
            public_key="PK", pageurl="u", data="blob", service_url="https://s"
        )
    )["task"]
    assert fun["type"] == "FunCaptchaTask"
    assert fun["websitePublicKey"] == "PK"
    assert fun["funcaptchaApiJSSubdomain"] == "https://s"
    assert fun["data"] == "blob"

    gv3 = a.build_payload(
        CapMonsterGeeTestV3Challenge(
            gt_key="gt",
            challenge="ch",
            pageurl="u",
            api_server="api.gt",
            geetest_lib="https://lib",
        )
    )["task"]
    assert gv3["type"] == "GeeTestTask"
    assert gv3["version"] == 3
    assert gv3["challenge"] == "ch"
    assert gv3["geetestApiServerSubdomain"] == "api.gt"
    assert gv3["geetestGetLib"] == "https://lib"

    gv4 = a.build_payload(
        CapMonsterGeeTestV4Challenge(captcha_id="cid", pageurl="u", risk_type="slide")
    )["task"]
    assert gv4["type"] == "GeeTestTask"
    assert gv4["version"] == 4
    assert gv4["gt"] == "cid"  # v4 id rides gt (vendor SDK requires gt)
    assert gv4["initParameters"] == {"riskType": "slide"}

    ts = a.build_payload(
        CapMonsterTurnstileChallenge(
            sitekey="ts",
            pageurl="u",
            action="act",
            c_data="cd",
            chl_page_data="pd",
            cloudflare_task_type="token",
            user_agent="UA",
        )
    )["task"]
    assert ts["type"] == "TurnstileTask"
    assert ts["pageAction"] == "act"
    assert ts["data"] == "cd"
    assert ts["pageData"] == "pd"
    assert ts["cloudflareTaskType"] == "token"
    assert ts["userAgent"] == "UA"


def test_softid_referral() -> None:
    ch = CapMonsterImageChallenge(b"png")
    assert "softId" not in adapter(False).build_payload(ch)
    assert adapter("4704").build_payload(ch)["softId"] == 4704
    assert "softId" not in CapMonsterAdapter("test-key").build_payload(ch)
    with pytest.raises(InvalidConfigError):
        adapter("not-a-number").build_payload(ch)


# -- response parsing ------------------------------------------------------


def test_task_status_states() -> None:
    a = adapter()
    assert a.parse_task_status(_j(errorId=0, status="processing")).state is (
        TaskStatus.PENDING
    )
    ready = a.parse_task_status(
        _j(errorId=0, status="ready", solution={"gRecaptchaResponse": "tok123456"})
    )
    assert ready.state is TaskStatus.READY
    assert isinstance(ready.solution, CapMonsterRecaptchaV2Solution)
    unsolvable = a.parse_task_status(
        _j(errorId=12, errorCode="ERROR_CAPTCHA_UNSOLVABLE")
    )
    assert unsolvable.state is TaskStatus.NO_SOLUTION
    unknown = a.parse_task_status(_j(errorId=16, errorCode="ERROR_TASK_ABSENT"))
    assert unknown.state is TaskStatus.UNKNOWN


def test_solution_shape_dispatch() -> None:
    a = adapter()
    gv3 = a._solution_from({"challenge": "c", "validate": "v", "seccode": "s"})
    assert isinstance(gv3, CapMonsterGeeTestV3Solution)
    gv4 = a._solution_from(
        {
            "captcha_id": "i",
            "lot_number": "l",
            "pass_token": "p",
            "gen_time": "1",
            "captcha_output": "o",
        }
    )
    assert isinstance(gv4, CapMonsterGeeTestV4Solution)
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


def test_reports_default_off() -> None:
    a = adapter()
    assert a.report_bad_supported(object) is False
    assert a.report_good_supported(object) is False
    from unicaptcha.errors import UnsupportedChallengeError

    with pytest.raises(UnsupportedChallengeError):
        a.build_report_bad(TaskRef(provider="capmonster", task_id=1))


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
    with CapMonsterClient("test-key", time=fast_time, retry=fast_retry) as client:
        result = client.solve_image(b"png", module_name="google")
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
    async with AsyncCapMonsterClient(
        "test-key", time=fast_time, retry=fast_retry
    ) as client:
        result = await client.solve_geetest_v3(
            gt_key="g", challenge="c0", pageurl="https://page"
        )
    assert isinstance(result.solution, CapMonsterGeeTestV3Solution)


def test_facade_rejects_wrong_provider_and_closed_use() -> None:
    with CapMonsterClient("test-key") as client:
        foreign = TaskRef(provider="other", task_id=1)
        with pytest.raises(TypeError):
            client.get_task_status(foreign)
    with pytest.raises(ClientClosedError):
        client.get_balance()
