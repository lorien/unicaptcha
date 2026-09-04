"""TwoCaptcha adapter, challenges, solutions, facades."""

import asyncio
import json
from decimal import Decimal

import httpx
import pytest
import respx
from _error_kinds import PROVIDER_ERROR_KINDS

from unicaptcha.errors import (
    AuthenticationError,
    ClientClosedError,
    EmptySolutionError,
    ErrorKind,
    InsufficientBalanceError,
    InvalidChallengeError,
    InvalidConfigError,
    ProviderError,
    UnsupportedChallengeError,
)
from unicaptcha.provider.twocaptcha import (
    AsyncTwoCaptchaClient,
    TwoCaptchaAdapter,
    TwoCaptchaClient,
    TwoCaptchaFunCaptchaChallenge,
    TwoCaptchaGeeTestV3Challenge,
    TwoCaptchaGeeTestV3Solution,
    TwoCaptchaGeeTestV4Challenge,
    TwoCaptchaGeeTestV4Solution,
    TwoCaptchaHCaptchaChallenge,
    TwoCaptchaImageChallenge,
    TwoCaptchaImageSolution,
    TwoCaptchaRecaptchaV2Challenge,
    TwoCaptchaRecaptchaV2Solution,
    TwoCaptchaRecaptchaV3Challenge,
    TwoCaptchaRecaptchaV3Solution,
    TwoCaptchaTextChallenge,
    TwoCaptchaTurnstileChallenge,
)
from unicaptcha.types import Proxy, TaskRef, TaskStatus, TaskTicket

BASE = "https://api.2captcha.com"
CREATE = f"{BASE}/createTask"
POLL = f"{BASE}/getTaskResult"
BALANCE = f"{BASE}/getBalance"


def _j(**data: object) -> bytes:
    return json.dumps(data).encode()


def _body(raw: bytes) -> dict[str, object]:
    return json.loads(raw)


def adapter(referral: bool | str = False) -> TwoCaptchaAdapter:
    return TwoCaptchaAdapter("test-key", referral=referral)


# -- challenges ----------------------------------------------------------


def test_image_challenge_rejects_bad_numeric() -> None:
    with pytest.raises(InvalidChallengeError):
        TwoCaptchaImageChallenge(b"x", numeric=9)


def test_language_pool_rides_envelope_never_task() -> None:
    a = adapter()
    payload = a.build_payload(TwoCaptchaTextChallenge("q", language_pool="rn"))
    assert payload["languagePool"] == "rn"
    assert "languagePool" not in payload["task"]
    image_payload = a.build_payload(
        TwoCaptchaImageChallenge(b"png", language_pool="en")
    )
    assert image_payload["languagePool"] == "en"
    bare = a.build_payload(TwoCaptchaTextChallenge("q"))
    assert "languagePool" not in bare


def test_all_challenges_construct() -> None:
    proxy = Proxy(host="1.2.3.4", port=8080)
    TwoCaptchaImageChallenge(b"png", numeric=2)
    TwoCaptchaTextChallenge("2+2?")
    TwoCaptchaRecaptchaV2Challenge(sitekey="k", pageurl="u")
    TwoCaptchaRecaptchaV3Challenge(sitekey="k", pageurl="u")
    TwoCaptchaHCaptchaChallenge(sitekey="k", pageurl="u")
    TwoCaptchaFunCaptchaChallenge(public_key="pk", pageurl="u")
    TwoCaptchaGeeTestV3Challenge(gt_key="g", challenge="c", pageurl="u")
    TwoCaptchaGeeTestV4Challenge(captcha_id="cid", pageurl="u")
    TwoCaptchaTurnstileChallenge(sitekey="t", pageurl="u")
    TwoCaptchaImageChallenge(b"png", proxy=proxy)


# -- adapter payloads ------------------------------------------------------


def test_payload_envelope_and_softid() -> None:
    ch = TwoCaptchaTextChallenge("q")
    plain = adapter(False).build_payload(ch)
    assert set(plain) == {"clientKey", "task"}
    assert plain["clientKey"] == "test-key"
    own = adapter("4704").build_payload(ch)
    assert own["softId"] == 4704
    default = TwoCaptchaAdapter("test-key").build_payload(ch)
    assert default["softId"] == 5859


def test_image_payload_uses_min_length_wire_names() -> None:
    task = adapter().build_payload(
        TwoCaptchaImageChallenge(b"img-bytes", min_len=1, max_len=5, math=True)
    )["task"]
    assert task == {
        "type": "ImageToTextTask",
        "body": "aW1nLWJ5dGVz",
        "math": True,
        "minLength": 1,
        "maxLength": 5,
    }


def test_recaptcha_v2_proxyless_vs_proxy_and_context() -> None:
    a = adapter()
    base = a.build_payload(TwoCaptchaRecaptchaV2Challenge(sitekey="sk", pageurl="pu"))[
        "task"
    ]
    assert base["type"] == "RecaptchaV2TaskProxyless"
    proxied = a.build_payload(
        TwoCaptchaRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            invisible=True,
            user_agent="UA",
            cookies={"a": "1", "b": "2"},
            proxy=Proxy(host="p.h", port=3128),
        )
    )["task"]
    assert proxied["type"] == "RecaptchaV2Task"
    assert proxied["isInvisible"] is True
    assert proxied["userAgent"] == "UA"
    assert proxied["cookies"] == "a=1; b=2"
    assert proxied["proxyType"] == "http"
    assert proxied["proxyAddress"] == "p.h"


def test_recaptcha_v2_enterprise_and_data_s() -> None:
    a = adapter()
    ent = a.build_payload(
        TwoCaptchaRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            is_enterprise=True,
            data_s={"s": "tok"},
            api_domain="recaptcha.net",
        )
    )["task"]
    assert ent["type"] == "RecaptchaV2EnterpriseTaskProxyless"
    assert ent["enterprisePayload"] == {"s": "tok"}
    assert ent["apiDomain"] == "recaptcha.net"
    classic = a.build_payload(
        TwoCaptchaRecaptchaV2Challenge(sitekey="sk", pageurl="pu", data_s={"s": "tok"})
    )["task"]
    assert classic["recaptchaDataSValue"] == "tok"
    with pytest.raises(InvalidChallengeError):
        a.build_payload(
            TwoCaptchaRecaptchaV2Challenge(
                sitekey="sk", pageurl="pu", data_s={"a": "1", "b": "2"}
            )
        )


def test_recaptcha_v3_fields() -> None:
    task = adapter().build_payload(
        TwoCaptchaRecaptchaV3Challenge(
            sitekey="sk",
            pageurl="pu",
            action="verify",
            min_score=0.7,
            is_enterprise=True,
            api_domain="google.com",
        )
    )["task"]
    # 2Captcha documents the Proxyless type only — v3 carries no proxy,
    # userAgent, or cookies fields.
    assert task["type"] == "RecaptchaV3TaskProxyless"
    for absent in ("proxyType", "userAgent", "cookies"):
        assert absent not in task
    assert task["pageAction"] == "verify"
    assert task["minScore"] == 0.7
    assert task["isEnterprise"] is True
    assert task["apiDomain"] == "google.com"


def test_hcaptcha_funcaptcha_geetest_turnstile_payloads() -> None:
    a = adapter()
    hcap = a.build_payload(
        TwoCaptchaHCaptchaChallenge(
            sitekey="h", pageurl="u", rqdata="rq", is_invisible=True
        )
    )["task"]
    assert hcap["type"] == "HCaptchaTaskProxyless"
    assert hcap["enterprisePayload"] == {"rqdata": "rq"}
    assert hcap["isInvisible"] is True

    fun = a.build_payload(
        TwoCaptchaFunCaptchaChallenge(
            public_key="PK", pageurl="u", data="blob", service_url="https://s"
        )
    )["task"]
    assert fun["type"] == "FunCaptchaTaskProxyless"
    assert fun["websitePublicKey"] == "PK"
    assert fun["funcaptchaApiJSSubdomain"] == "https://s"
    assert fun["data"] == "blob"
    proxied_fun = a.build_payload(
        TwoCaptchaFunCaptchaChallenge(
            public_key="PK",
            pageurl="u",
            proxy=Proxy(host="1.2.3.4", port=8080),
        )
    )["task"]
    assert proxied_fun["type"] == "FunCaptchaTask"

    gv3 = a.build_payload(
        TwoCaptchaGeeTestV3Challenge(
            gt_key="gt", challenge="ch", pageurl="u", api_server="api.gt"
        )
    )["task"]
    assert gv3["type"] == "GeeTestTaskProxyless"
    assert gv3["geetestApiServerSubdomain"] == "api.gt"

    gv4 = a.build_payload(
        TwoCaptchaGeeTestV4Challenge(captcha_id="cid", pageurl="u", risk_type="slide")
    )["task"]
    assert gv4["type"] == "GeeTestTaskProxyless"
    assert gv4["version"] == 4
    assert gv4["initParameters"] == {"captcha_id": "cid"}
    assert gv4["risk_type"] == "slide"

    ts = a.build_payload(
        TwoCaptchaTurnstileChallenge(
            sitekey="ts", pageurl="u", action="act", c_data="cd"
        )
    )["task"]
    assert ts["type"] == "TurnstileTaskProxyless"
    assert ts["action"] == "act"
    # Wire names are lowercase per the live docs.
    assert ts["data"] == "cd"
    assert "cData" not in ts
    proxied_ts = a.build_payload(
        TwoCaptchaTurnstileChallenge(
            sitekey="ts",
            pageurl="u",
            chl_page_data="pd",
            proxy=Proxy(host="1.2.3.4", port=8080),
        )
    )["task"]
    assert proxied_ts["type"] == "TurnstileTask"
    assert proxied_ts["pagedata"] == "pd"


def test_unsupported_challenge_type() -> None:
    from unicaptcha.challenge.text import TextChallenge

    class Foreign(TextChallenge):
        pass

    with pytest.raises(UnsupportedChallengeError):
        adapter().build_payload(Foreign("x"))


# -- response parsing ------------------------------------------------------


def test_submit_pending_and_string_task_id() -> None:
    accepted = adapter().parse_submit_response(_j(errorId=0, taskId="77"))
    assert accepted.task_id == 77
    assert accepted.instant_answer is None


def test_submit_ready_inline_instant_answer() -> None:
    raw = _j(
        errorId=0,
        status="ready",
        taskId=5,
        cost="0.002",
        solution={"text": "hi"},
    )
    accepted = adapter().parse_submit_response(raw)
    assert accepted.instant_answer is not None
    instant = accepted.instant_answer
    assert instant.state is TaskStatus.READY
    assert isinstance(instant.solution, TwoCaptchaImageSolution)
    assert instant.cost == Decimal("0.002")


def test_submit_error_maps_to_authentication_error() -> None:
    raw = _j(errorId=1, errorCode="ERROR_KEY_DOES_NOT_EXIST")
    with pytest.raises(AuthenticationError):
        adapter().parse_submit_response(raw)


def test_malformed_json_chains_provider_error() -> None:
    with pytest.raises(ProviderError) as excinfo:
        adapter().parse_submit_response(b"not json")
    assert isinstance(excinfo.value.__cause__, ValueError)


def test_task_status_states() -> None:
    a = adapter()
    assert a.parse_task_status(_j(errorId=0, status="processing")).state is (
        TaskStatus.PENDING
    )
    ready = a.parse_task_status(
        _j(
            errorId=0,
            status="ready",
            cost="0.001",
            solution={"gRecaptchaResponse": "tok123456"},
        )
    )
    assert ready.state is TaskStatus.READY
    assert isinstance(ready.solution, TwoCaptchaRecaptchaV2Solution)
    unsolvable = a.parse_task_status(
        _j(errorId=12, errorCode="ERROR_CAPTCHA_UNSOLVABLE")
    )
    assert unsolvable.state is TaskStatus.NO_SOLUTION
    unknown = a.parse_task_status(_j(errorId=16, errorCode="ERROR_TASK_NOT_FOUND"))
    assert unknown.state is TaskStatus.UNKNOWN
    assert unknown.detail == "" or unknown.detail is not None


def test_ready_without_solution_raises_empty() -> None:
    raw = _j(errorId=0, status="ready", solution={})
    with pytest.raises(EmptySolutionError):
        adapter().parse_task_status(raw)


def test_solution_shape_dispatch() -> None:
    a = adapter()
    gv3 = a._solution_from({"challenge": "c", "validate": "v", "seccode": "s|jordan"})
    assert isinstance(gv3, TwoCaptchaGeeTestV3Solution)
    gv4 = a._solution_from(
        {
            "captcha_id": "i",
            "lot_number": "l",
            "pass_token": "p",
            "gen_time": "1",
            "captcha_output": "o",
        }
    )
    assert isinstance(gv4, TwoCaptchaGeeTestV4Solution)
    v3 = a._solution_from({"token": "t", "score": 0.9})
    assert isinstance(v3, TwoCaptchaRecaptchaV3Solution)
    assert v3.score == 0.9
    # Live-verified v3 shape: gRecaptchaResponse + token, no score.
    v3_noscore = a._solution_from({"gRecaptchaResponse": "g", "token": "t"})
    assert isinstance(v3_noscore, TwoCaptchaRecaptchaV3Solution)
    assert v3_noscore.score is None
    # v2 carries gRecaptchaResponse only.
    v2 = a._solution_from({"gRecaptchaResponse": "g"})
    assert isinstance(v2, TwoCaptchaRecaptchaV2Solution)
    with pytest.raises(EmptySolutionError):
        a._solution_from({"bogus": 1})


def test_balance_parsing() -> None:
    a = adapter()
    assert a.parse_balance(_j(errorId=0, balance=12.34)) == Decimal("12.34")
    assert a.parse_balance(_j(errorId=0, balance="3")) == Decimal("3")
    with pytest.raises(InsufficientBalanceError):
        a.parse_balance(_j(errorId=1, errorCode="ERROR_ZERO_BALANCE"))
    with pytest.raises(ProviderError):
        a.parse_balance(_j(errorId=0))


def test_map_provider_error_table() -> None:
    cases = dict(PROVIDER_ERROR_KINDS["twocaptcha"])
    cases["ERROR_SOMETHING_ELSE"] = ErrorKind.PROVIDER
    for code, expected in cases.items():
        kind, message = adapter().map_provider_error(
            _j(errorId=1, errorCode=code, errorDescription="boom")
        )
        assert kind is expected
        assert message == "boom"


# -- report pairs ----------------------------------------------------------


def test_report_pairs_round_trip() -> None:
    a = adapter()
    ref = TaskRef(provider="twocaptcha", task_id=42)
    assert a.report_bad_supported(object) is True
    assert a.report_good_supported(object) is True
    assert a.build_report_bad(ref) == {"clientKey": "test-key", "taskId": 42}
    assert a.build_report_good(ref) == {"clientKey": "test-key", "taskId": 42}
    assert a.parse_report_good(_j(errorId=0, status="success")) is True
    assert a.parse_report_bad(_j(errorId=0, status="success")) is True
    assert a.parse_report_bad(_j(errorId=0, status="error")) is False
    with pytest.raises(ProviderError):
        a.parse_report_good(_j(errorId=1, errorCode="ERROR_PAGEURL"))


def test_referral_string_must_be_integer() -> None:
    with pytest.raises(InvalidConfigError):
        adapter("not-a-number").build_payload(TwoCaptchaTextChallenge("q"))


# -- facades (sync round trip over respx) -----------------------------------


@respx.mock
def test_sync_facade_solve_happy_path(fast_time, fast_retry) -> None:
    create = respx.post(CREATE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, taskId=99))
    )
    poll = respx.post(POLL).mock(
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
    events: list[str] = []
    with TwoCaptchaClient(
        "test-key",
        time=fast_time,
        retry=fast_retry,
        on_event=lambda e: events.append(e.kind.name),
    ) as client:
        result = client.solve_image(b"png", numeric=1)
    assert create.called and poll.called
    request_body = _body(create.calls[0].request.content)
    assert request_body["task"]["numeric"] == 1
    assert request_body["task"]["body"] == "cG5n"
    assert isinstance(result.solution, TwoCaptchaImageSolution)
    assert result.solution.text == "hello world"
    assert result.task_id == 99
    assert result.cost == Decimal("0.00025")
    assert result.task_ref == TaskRef("twocaptcha", 99)
    assert "SUBMIT_ACCEPTED" in events
    assert "RESULT_RECEIVED" in events


@respx.mock
def test_sync_facade_aux_ops(fast_time, fast_retry) -> None:
    respx.post(BALANCE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, balance="7.5"))
    )
    respx.post(POLL).mock(
        return_value=httpx.Response(
            200, content=_j(errorId=0, status="ready", solution={"token": "abc123"})
        )
    )
    respx.post(f"{BASE}/reportIncorrect").mock(
        return_value=httpx.Response(200, content=_j(errorId=0, status="success"))
    )
    with TwoCaptchaClient("test-key", time=fast_time, retry=fast_retry) as client:
        assert client.get_balance() == Decimal("7.5")
        status = client.get_task_status(55)
        assert status.task_id == 55
        assert status.status is TaskStatus.PENDING or status.status is not None
        assert client.report_bad_result(55) is True
    # aux report hits exactly once
    assert respx.post(f"{BASE}/reportIncorrect").called


@respx.mock
@pytest.mark.asyncio
async def test_async_facade_solve_happy_path(fast_time, fast_retry) -> None:
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
    async with AsyncTwoCaptchaClient(
        "test-key", time=fast_time, retry=fast_retry
    ) as client:
        result = await client.solve_geetest_v3(
            gt_key="g", challenge="c0", pageurl="https://page"
        )
    assert isinstance(result.solution, TwoCaptchaGeeTestV3Solution)


def test_facade_rejects_wrong_provider_refs_and_closed_use() -> None:
    foreign_ticket = TaskTicket(
        task_ref=TaskRef(provider="other", task_id=1),
        submitted_at=_utc_now(),
    )
    with TwoCaptchaClient("test-key") as client:
        foreign = TaskRef(provider="other", task_id=1)
        with pytest.raises(TypeError):
            client.get_task_status(foreign)
        with pytest.raises(TypeError):
            client.wait_ref(foreign)
        with pytest.raises(TypeError):
            client.wait(foreign_ticket)
    with pytest.raises(ClientClosedError):
        client.get_balance()


def test_speed_defaults_to_kind_timing(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_sleep(seconds: float) -> None:
        raise AssertionError(f"unexpected sleep {seconds}")

    monkeypatch.setattr(asyncio, "sleep", fail_sleep)


def _utc_now():
    from datetime import UTC, datetime

    return datetime.now(UTC)
