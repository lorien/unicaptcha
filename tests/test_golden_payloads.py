"""Transport-level golden-payload tests for all five adapters.

The per-provider test files assert ``build_payload``/``parse_*`` at the
adapter level; this suite locks the **wire contract** through the real
``Solver``/``AsyncSolver`` over respx:

- exact outgoing URL + JSON payload per kind x provider, against the
  ADR-0076 field tables (architecture.md section 2),
- referral embedding (ADR-0072),
- proxy / worker-context serialization (ADR-0012, ADR-0069),
- response parsing at transport level: ``SubmitAccepted`` incl. the
  instant fast path (ADR-0075), the ``ParsedTask`` state machine
  (ADR-0058), balance, report bad/good (ADR-0068), malformed bodies ->
  ``ProviderError`` with ``raw_response`` and chained cause (ADR-0040),
- error mapping and the support matrix (ADR-0009, ADR-0057).
"""

import json
from decimal import Decimal

import httpx
import pytest
import respx
from _myservice import (
    MyServiceAdapter,
    MyServiceImageChallenge,
    MyServiceRecaptchaV2Challenge,
)

from unicaptcha import AsyncSolver, Solver
from unicaptcha.challenge.text import TextChallenge
from unicaptcha.errors import (
    AuthenticationError,
    EmptySolutionError,
    InsufficientBalanceError,
    InvalidChallengeError,
    NoSolutionError,
    ProviderError,
    RateLimitError,
    ServiceBusyError,
    UnsupportedChallengeError,
)
from unicaptcha.provider.anticaptcha import (
    AntiCaptchaAdapter,
    AntiCaptchaFunCaptchaChallenge,
    AntiCaptchaGeeTestV3Challenge,
    AntiCaptchaGeeTestV4Challenge,
    AntiCaptchaHCaptchaChallenge,
    AntiCaptchaImageChallenge,
    AntiCaptchaRecaptchaV2Challenge,
    AntiCaptchaRecaptchaV3Challenge,
    AntiCaptchaTextChallenge,
    AntiCaptchaTurnstileChallenge,
)
from unicaptcha.provider.capmonster import (
    CapMonsterAdapter,
    CapMonsterFunCaptchaChallenge,
    CapMonsterGeeTestV3Challenge,
    CapMonsterGeeTestV4Challenge,
    CapMonsterHCaptchaChallenge,
    CapMonsterImageChallenge,
    CapMonsterRecaptchaV2Challenge,
    CapMonsterRecaptchaV3Challenge,
    CapMonsterTurnstileChallenge,
)
from unicaptcha.provider.capsolver import (
    CapsolverAdapter,
    CapsolverFunCaptchaChallenge,
    CapsolverGeeTestV3Challenge,
    CapsolverGeeTestV4Challenge,
    CapsolverHCaptchaChallenge,
    CapsolverImageChallenge,
    CapsolverRecaptchaV2Challenge,
    CapsolverRecaptchaV3Challenge,
    CapsolverTurnstileChallenge,
)
from unicaptcha.provider.twocaptcha import (
    TwoCaptchaAdapter,
    TwoCaptchaFunCaptchaChallenge,
    TwoCaptchaGeeTestV3Challenge,
    TwoCaptchaGeeTestV4Challenge,
    TwoCaptchaHCaptchaChallenge,
    TwoCaptchaImageChallenge,
    TwoCaptchaRecaptchaV2Challenge,
    TwoCaptchaRecaptchaV3Challenge,
    TwoCaptchaTextChallenge,
    TwoCaptchaTurnstileChallenge,
)
from unicaptcha.types import Proxy, TaskRef, TaskStatus


def _j(**data: object) -> bytes:
    return json.dumps(data).encode()


def _body(request: httpx.Request) -> dict[str, object]:
    return json.loads(request.content)


def _fast_time():
    from unicaptcha.types import TimeConfig

    return TimeConfig(poll_delay=0.0, poll_interval=0.01, total_timeout=1.0)


def _fast_retry():
    from unicaptcha.types import RetryConfig

    return RetryConfig(max_attempts=2, backoff_base=0.001, backoff_cap=0.001)


def _submit_once(adapter, challenge) -> httpx.Request:
    """Submit through a real Solver over respx; return the captured request."""
    target = f"{adapter.base_url}/createTask"
    with respx.mock:
        route = respx.post(target).mock(
            return_value=httpx.Response(200, content=_j(errorId=0, taskId=5))
        )
        with Solver(adapters=[adapter]) as solver:
            solver.submit(challenge)
        return route.calls.last.request


# -- golden payload matrix ---------------------------------------------------
#
# One case per kind x provider. Expected payloads follow the ADR-0076 field
# tables (architecture.md section 2); adapters use the default constructor,
# which also pins ADR-0072's "referral=True embeds nothing until an id is
# recorded" behavior (no ``softId`` anywhere).

GOLDEN_CASES: list[tuple[str, object, object, str, dict[str, object]]] = [
    # -- 2Captcha (https://api.2captcha.com) -------------------------------
    (
        "twocaptcha-image",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaImageChallenge(b"img-bytes"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {"type": "ImageToTextTask", "body": "aW1nLWJ5dGVz"},
        },
    ),
    (
        "twocaptcha-text",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaTextChallenge("2+2?"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {"type": "TextCaptchaTask", "comment": "2+2?"},
        },
    ),
    (
        "twocaptcha-recaptcha-v2",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaRecaptchaV2Challenge(sitekey="sk", pageurl="pu"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "twocaptcha-recaptcha-v3",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaRecaptchaV3Challenge(sitekey="sk", pageurl="pu"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "RecaptchaV3TaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "twocaptcha-hcaptcha",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaHCaptchaChallenge(sitekey="sk", pageurl="pu"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "twocaptcha-funcaptcha",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaFunCaptchaChallenge(public_key="pk", pageurl="pu"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "FunCaptchaTaskProxyless",
                "websiteURL": "pu",
                "websitePublicKey": "pk",
            },
        },
    ),
    (
        "twocaptcha-geetest-v3",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaGeeTestV3Challenge(gt_key="gt", challenge="ch", pageurl="pu"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "GeeTestTaskProxyless",
                "websiteURL": "pu",
                "gt": "gt",
                "challenge": "ch",
            },
        },
    ),
    (
        "twocaptcha-geetest-v4",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaGeeTestV4Challenge(captcha_id="cid", pageurl="pu"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "GeeTestTaskProxyless",
                "websiteURL": "pu",
                "version": 4,
                "initParameters": {"captcha_id": "cid"},
            },
        },
    ),
    (
        "twocaptcha-turnstile",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaTurnstileChallenge(sitekey="ts", pageurl="pu"),
        "https://api.2captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "TurnstileTaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "ts",
            },
        },
    ),
    # -- Anti-Captcha (https://api.anti-captcha.com) ------------------------
    (
        "anti-captcha-image",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaImageChallenge(b"img"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {"type": "ImageToTextTask", "body": "aW1n"},
        },
    ),
    (
        "anti-captcha-text",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaTextChallenge("q"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {"type": "TextCaptchaTask", "comment": "q"},
        },
    ),
    (
        "anti-captcha-recaptcha-v2",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaRecaptchaV2Challenge(sitekey="sk", pageurl="pu"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "anti-captcha-recaptcha-v3",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaRecaptchaV3Challenge(sitekey="sk", pageurl="pu"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "RecaptchaV3TaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "anti-captcha-hcaptcha",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaHCaptchaChallenge(sitekey="sk", pageurl="pu"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "anti-captcha-funcaptcha",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaFunCaptchaChallenge(public_key="pk", pageurl="pu"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "FunCaptchaTaskProxyless",
                "websiteURL": "pu",
                "websitePublicKey": "pk",
            },
        },
    ),
    (
        "anti-captcha-geetest-v3",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaGeeTestV3Challenge(gt_key="gt", challenge="ch", pageurl="pu"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "GeeTestTaskProxyless",
                "websiteURL": "pu",
                "gt": "gt",
                "challenge": "ch",
            },
        },
    ),
    (
        "anti-captcha-geetest-v4",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaGeeTestV4Challenge(captcha_id="cid", pageurl="pu"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "GeeTestTaskProxyless",
                "websiteURL": "pu",
                "gt": "cid",
                "version": 4,
            },
        },
    ),
    (
        "anti-captcha-turnstile",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaTurnstileChallenge(sitekey="ts", pageurl="pu"),
        "https://api.anti-captcha.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "TurnstileTaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "ts",
            },
        },
    ),
    # -- CapMonster (https://api.capmonster.cloud) --------------------------
    (
        "capmonster-image",
        CapMonsterAdapter("test-key"),
        CapMonsterImageChallenge(b"img"),
        "https://api.capmonster.cloud/createTask",
        {
            "clientKey": "test-key",
            "task": {"type": "ImageToTextTask", "body": "aW1n"},
        },
    ),
    (
        "capmonster-recaptcha-v2",
        CapMonsterAdapter("test-key"),
        CapMonsterRecaptchaV2Challenge(sitekey="sk", pageurl="pu"),
        "https://api.capmonster.cloud/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "RecaptchaV2Task",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "capmonster-recaptcha-v3",
        CapMonsterAdapter("test-key"),
        CapMonsterRecaptchaV3Challenge(sitekey="sk", pageurl="pu"),
        "https://api.capmonster.cloud/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "RecaptchaV3TaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "capmonster-hcaptcha",
        CapMonsterAdapter("test-key"),
        CapMonsterHCaptchaChallenge(sitekey="sk", pageurl="pu"),
        "https://api.capmonster.cloud/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "HCaptchaTask",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "capmonster-funcaptcha",
        CapMonsterAdapter("test-key"),
        CapMonsterFunCaptchaChallenge(public_key="pk", pageurl="pu"),
        "https://api.capmonster.cloud/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "FunCaptchaTask",
                "websiteURL": "pu",
                "websitePublicKey": "pk",
            },
        },
    ),
    (
        "capmonster-geetest-v3",
        CapMonsterAdapter("test-key"),
        CapMonsterGeeTestV3Challenge(gt_key="gt", challenge="ch", pageurl="pu"),
        "https://api.capmonster.cloud/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "GeeTestTask",
                "websiteURL": "pu",
                "gt": "gt",
                "challenge": "ch",
                "version": 3,
            },
        },
    ),
    (
        "capmonster-geetest-v4",
        CapMonsterAdapter("test-key"),
        CapMonsterGeeTestV4Challenge(captcha_id="cid", pageurl="pu"),
        "https://api.capmonster.cloud/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "GeeTestTask",
                "websiteURL": "pu",
                "gt": "cid",
                "version": 4,
            },
        },
    ),
    (
        "capmonster-turnstile",
        CapMonsterAdapter("test-key"),
        CapMonsterTurnstileChallenge(sitekey="ts", pageurl="pu"),
        "https://api.capmonster.cloud/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "TurnstileTask",
                "websiteURL": "pu",
                "websiteKey": "ts",
            },
        },
    ),
    # -- Capsolver (https://api.capsolver.com) ------------------------------
    (
        "capsolver-image",
        CapsolverAdapter("test-key"),
        CapsolverImageChallenge(b"img"),
        "https://api.capsolver.com/createTask",
        {
            "clientKey": "test-key",
            "task": {"type": "ImageToTextTask", "body": "aW1n"},
        },
    ),
    (
        "capsolver-recaptcha-v2",
        CapsolverAdapter("test-key"),
        CapsolverRecaptchaV2Challenge(sitekey="sk", pageurl="pu"),
        "https://api.capsolver.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "ReCaptchaV2TaskProxyLess",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "capsolver-recaptcha-v3",
        CapsolverAdapter("test-key"),
        CapsolverRecaptchaV3Challenge(sitekey="sk", pageurl="pu"),
        "https://api.capsolver.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "ReCaptchaV3TaskProxyLess",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "capsolver-hcaptcha",
        CapsolverAdapter("test-key"),
        CapsolverHCaptchaChallenge(sitekey="sk", pageurl="pu"),
        "https://api.capsolver.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "HCaptchaTaskProxyLess",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
    (
        "capsolver-funcaptcha",
        CapsolverAdapter("test-key"),
        CapsolverFunCaptchaChallenge(public_key="pk", pageurl="pu"),
        "https://api.capsolver.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "FunCaptchaTaskProxyLess",
                "websiteURL": "pu",
                "websitePublicKey": "pk",
            },
        },
    ),
    (
        "capsolver-geetest-v3",
        CapsolverAdapter("test-key"),
        CapsolverGeeTestV3Challenge(gt_key="gt", challenge="ch", pageurl="pu"),
        "https://api.capsolver.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "GeeTestTaskProxyLess",
                "websiteURL": "pu",
                "gt": "gt",
                "challenge": "ch",
            },
        },
    ),
    (
        "capsolver-geetest-v4",
        CapsolverAdapter("test-key"),
        CapsolverGeeTestV4Challenge(captcha_id="cid", pageurl="pu"),
        "https://api.capsolver.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "GeeTestTaskProxyLess",
                "websiteURL": "pu",
                "captchaId": "cid",
            },
        },
    ),
    (
        "capsolver-turnstile",
        CapsolverAdapter("test-key"),
        CapsolverTurnstileChallenge(sitekey="ts", pageurl="pu"),
        "https://api.capsolver.com/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "AntiTurnstileTaskProxyLess",
                "websiteURL": "pu",
                "websiteKey": "ts",
            },
        },
    ),
    # -- reference "myservice" (https://myservice.example) ------------------
    (
        "myservice-image",
        MyServiceAdapter("test-key"),
        MyServiceImageChallenge(b"png"),
        "https://myservice.example/createTask",
        {
            "clientKey": "test-key",
            "task": {"type": "ImageToTextTask", "body": "cG5n"},
        },
    ),
    (
        "myservice-recaptcha-v2",
        MyServiceAdapter("test-key"),
        MyServiceRecaptchaV2Challenge(sitekey="sk", pageurl="pu"),
        "https://myservice.example/createTask",
        {
            "clientKey": "test-key",
            "task": {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": "pu",
                "websiteKey": "sk",
            },
        },
    ),
]


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c[0] for c in GOLDEN_CASES])
def test_golden_submit_wire_payload(case: tuple[object, ...]) -> None:
    _, adapter, challenge, url, expected = case  # type: ignore[misc]
    request = _submit_once(adapter, challenge)
    assert request.method == "POST"
    assert str(request.url) == url
    assert _body(request) == expected


# -- referral embedding (ADR-0072) ------------------------------------------

SOFT_ID_CASES: list[tuple[str, object, object, dict[str, object]]] = [
    (
        "twocaptcha",
        TwoCaptchaAdapter("test-key", referral="4704"),
        TwoCaptchaTextChallenge("q"),
        {"type": "TextCaptchaTask", "comment": "q"},
    ),
    (
        "anti-captcha",
        AntiCaptchaAdapter("test-key", referral="4704"),
        AntiCaptchaTextChallenge("q"),
        {"type": "TextCaptchaTask", "comment": "q"},
    ),
    (
        "capmonster",
        CapMonsterAdapter("test-key", referral="4704"),
        CapMonsterImageChallenge(b"png"),
        {"type": "ImageToTextTask", "body": "cG5n"},
    ),
]


@pytest.mark.parametrize("case", SOFT_ID_CASES, ids=[c[0] for c in SOFT_ID_CASES])
def test_referral_string_embeds_soft_id(case: tuple[object, ...]) -> None:
    _, adapter, challenge, expected_task = case  # type: ignore[misc]
    request = _submit_once(adapter, challenge)
    assert _body(request) == {
        "clientKey": "test-key",
        "softId": 4704,
        "task": expected_task,
    }


def test_referral_false_embeds_nothing_twocaptcha() -> None:
    request = _submit_once(
        TwoCaptchaAdapter("test-key", referral=False),
        TwoCaptchaTextChallenge("q"),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {"type": "TextCaptchaTask", "comment": "q"},
    }


def test_referral_true_embeds_nothing_until_id_recorded() -> None:
    # ADR-0072: the project affiliate id is not registered yet, so the
    # default ``referral=True`` must send no ``softId``.
    request = _submit_once(
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaTextChallenge("q"),
    )
    assert "softId" not in _body(request)


def test_capsolver_referral_inert() -> None:
    request = _submit_once(
        CapsolverAdapter("test-key", referral="4704"),
        CapsolverImageChallenge(b"png"),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {"type": "ImageToTextTask", "body": "cG5n"},
    }


def test_myservice_referral_string_embeds_soft_id() -> None:
    request = _submit_once(
        MyServiceAdapter("test-key", referral="4704"),
        MyServiceImageChallenge(b"png"),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "softId": 4704,
        "task": {"type": "ImageToTextTask", "body": "cG5n"},
    }


# -- proxy / worker-context serialization (ADR-0012, ADR-0069) -------------


def test_twocaptcha_v2_proxy_and_worker_context_wire() -> None:
    request = _submit_once(
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            invisible=True,
            user_agent="UA",
            cookies={"a": "1", "b": "2"},
            proxy=Proxy(host="p.h", port=3128),
        ),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {
            "type": "RecaptchaV2Task",
            "websiteURL": "pu",
            "websiteKey": "sk",
            "isInvisible": True,
            "userAgent": "UA",
            "cookies": "a=1; b=2",
            "proxyType": "http",
            "proxyAddress": "p.h",
            "proxyPort": 3128,
        },
    }


def test_anticaptcha_v2_proxy_ip_and_context_wire() -> None:
    request = _submit_once(
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            user_agent="UA",
            cookies={"a": "1"},
            proxy=Proxy(host="1.2.3.4", port=8080),
        ),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {
            "type": "RecaptchaV2Task",
            "websiteURL": "pu",
            "websiteKey": "sk",
            "userAgent": "UA",
            "cookies": "a=1",
            "proxyType": "http",
            "proxyAddress": "1.2.3.4",
            "proxyPort": 8080,
        },
    }


def test_anticaptcha_proxy_hostname_rejected_at_wire() -> None:
    with pytest.raises(InvalidChallengeError):
        _submit_once(
            AntiCaptchaAdapter("test-key"),
            AntiCaptchaRecaptchaV2Challenge(
                sitekey="sk",
                pageurl="pu",
                proxy=Proxy(host="proxy.example.com", port=8080),
            ),
        )


def test_capmonster_worker_context_proxyless_wire() -> None:
    request = _submit_once(
        CapMonsterAdapter("test-key"),
        CapMonsterRecaptchaV2Challenge(
            sitekey="sk", pageurl="pu", user_agent="UA", cookies={"a": "1"}
        ),
    )
    task = _body(request)["task"]
    assert task == {
        "type": "RecaptchaV2Task",
        "websiteURL": "pu",
        "websiteKey": "sk",
        "userAgent": "UA",
        "cookies": "a=1",
    }
    # ADR-0012/0076: CapMonster is proxyless — no proxy fields may exist.
    for absent in ("proxyType", "proxyAddress", "proxyPort"):
        assert absent not in task


def test_capsolver_v2_proxy_with_credentials_wire() -> None:
    request = _submit_once(
        CapsolverAdapter("test-key"),
        CapsolverRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            proxy=Proxy(host="p.h", port=3128, username="u", password="p"),
        ),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {
            "type": "ReCaptchaV2Task",
            "websiteURL": "pu",
            "websiteKey": "sk",
            "proxyType": "http",
            "proxyAddress": "p.h",
            "proxyPort": 3128,
            "proxyLogin": "u",
            "proxyPassword": "p",
        },
    }


# -- provider extras -> wire names (ADR-0076 field tables) ------------------


def test_twocaptcha_image_extras_and_language_pool() -> None:
    request = _submit_once(
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaImageChallenge(
            b"img-bytes",
            phrase=True,
            case=True,
            numeric=3,
            math=True,
            min_len=1,
            max_len=5,
            comment="door",
            language_pool="en",
        ),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "languagePool": "en",
        "task": {
            "type": "ImageToTextTask",
            "body": "aW1nLWJ5dGVz",
            "phrase": True,
            "case": True,
            "numeric": 3,
            "math": True,
            "minLength": 1,
            "maxLength": 5,
            "comment": "door",
        },
    }


def test_twocaptcha_recaptcha_v3_extras() -> None:
    request = _submit_once(
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaRecaptchaV3Challenge(
            sitekey="sk",
            pageurl="pu",
            action="verify",
            min_score=0.7,
            is_enterprise=True,
            api_domain="google.com",
        ),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {
            "type": "RecaptchaV3TaskProxyless",
            "websiteURL": "pu",
            "websiteKey": "sk",
            "pageAction": "verify",
            "minScore": 0.7,
            "isEnterprise": True,
            "apiDomain": "google.com",
        },
    }


def test_anticaptcha_image_language_pool_in_task() -> None:
    request = _submit_once(
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaImageChallenge(b"img", min_len=2, max_len=4, language_pool="en"),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {
            "type": "ImageToTextTask",
            "body": "aW1n",
            "minLength": 2,
            "maxLength": 4,
            "languagePool": "en",
        },
    }


def test_anticaptcha_text_lang() -> None:
    request = _submit_once(
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaTextChallenge("q", lang="en"),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {"type": "TextCaptchaTask", "comment": "q", "lang": "en"},
    }


def test_capmonster_v2_enterprise_extras() -> None:
    request = _submit_once(
        CapMonsterAdapter("test-key"),
        CapMonsterRecaptchaV2Challenge(
            sitekey="sk",
            pageurl="pu",
            is_enterprise=True,
            data_s={"s": "tok"},
            api_domain="recaptcha.net",
            action="login",
        ),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {
            "type": "RecaptchaV2EnterpriseTask",
            "websiteURL": "pu",
            "websiteKey": "sk",
            "enterprisePayload": {"s": "tok"},
            "apiDomain": "recaptcha.net",
            "pageAction": "login",
        },
    }


def test_capmonster_turnstile_extras() -> None:
    request = _submit_once(
        CapMonsterAdapter("test-key"),
        CapMonsterTurnstileChallenge(
            sitekey="ts",
            pageurl="pu",
            action="act",
            c_data="cd",
            chl_page_data="pd",
            cloudflare_task_type="token",
            user_agent="UA",
        ),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {
            "type": "TurnstileTask",
            "websiteURL": "pu",
            "websiteKey": "ts",
            "pageAction": "act",
            "data": "cd",
            "pageData": "pd",
            "cloudflareTaskType": "token",
            "userAgent": "UA",
        },
    }


def test_capsolver_turnstile_metadata() -> None:
    request = _submit_once(
        CapsolverAdapter("test-key"),
        CapsolverTurnstileChallenge(
            sitekey="ts", pageurl="pu", action="act", c_data="cd"
        ),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {
            "type": "AntiTurnstileTaskProxyLess",
            "websiteURL": "pu",
            "websiteKey": "ts",
            "metadata": {"action": "act", "cdata": "cd"},
        },
    }


def test_capsolver_image_module() -> None:
    request = _submit_once(
        CapsolverAdapter("test-key"),
        CapsolverImageChallenge(b"img", module="number"),
    )
    assert _body(request) == {
        "clientKey": "test-key",
        "task": {"type": "ImageToTextTask", "body": "aW1n", "module": "number"},
    }


# -- response parsing at transport level ------------------------------------
# ADR-0040 (malformed -> ProviderError with raw_response + cause), ADR-0058
# (four-state ParsedTask), ADR-0075 (submit-ready fast path).


def test_solve_submit_then_poll_wire_round_trip() -> None:
    with respx.mock:
        create = respx.post("https://api.2captcha.com/createTask").mock(
            return_value=httpx.Response(200, content=_j(errorId=0, taskId=99))
        )
        poll = respx.post("https://api.2captcha.com/getTaskResult").mock(
            side_effect=[
                httpx.Response(200, content=_j(errorId=0, status="processing")),
                httpx.Response(
                    200,
                    content=_j(
                        errorId=0,
                        status="ready",
                        cost="0.00025",
                        solution={"text": "hello"},
                    ),
                ),
            ]
        )
        with Solver(
            adapters=[TwoCaptchaAdapter("test-key")],
            time=_fast_time(),
            retry=_fast_retry(),
        ) as solver:
            result = solver.solve(TwoCaptchaImageChallenge(b"png"))
        create_request = create.calls.last.request
        assert str(create_request.url) == "https://api.2captcha.com/createTask"
        assert _body(create_request) == {
            "clientKey": "test-key",
            "task": {"type": "ImageToTextTask", "body": "cG5n"},
        }
        for poll_call in poll.calls:
            request = poll_call.request
            assert str(request.url) == "https://api.2captcha.com/getTaskResult"
            assert _body(request) == {"clientKey": "test-key", "taskId": 99}
    assert result.task_id == 99
    assert result.provider == "twocaptcha"
    assert result.solution.text == "hello"
    assert result.cost == Decimal("0.00025")


def test_instant_answer_fast_path_no_poll() -> None:
    with respx.mock:
        create = respx.post("https://api.capsolver.com/createTask").mock(
            return_value=httpx.Response(
                200,
                content=_j(
                    errorId=0,
                    status="ready",
                    taskId="61138bb6-19fb-11ec-a9c8-0242ac110006",
                    solution={"text": "44795sds"},
                ),
            )
        )
        poll = respx.post("https://api.capsolver.com/getTaskResult")
        with Solver(
            adapters=[CapsolverAdapter("test-key")],
            time=_fast_time(),
            retry=_fast_retry(),
        ) as solver:
            ticket = solver.submit(CapsolverImageChallenge(b"png"))
            result = solver.wait(ticket)
        assert create.called
        assert ticket.instant_answer is not None
        assert ticket.instant_answer.state is TaskStatus.READY
        assert result.solution.text == "44795sds"
        # ADR-0075: no poll phase, no getTaskResult request.
        assert not poll.called


def test_no_solution_raises_through_poll() -> None:
    with respx.mock:
        respx.post("https://api.2captcha.com/createTask").mock(
            return_value=httpx.Response(200, content=_j(errorId=0, taskId=3))
        )
        respx.post("https://api.2captcha.com/getTaskResult").mock(
            return_value=httpx.Response(
                200, content=_j(errorId=12, errorCode="ERROR_CAPTCHA_UNSOLVABLE")
            )
        )
        with (
            Solver(
                adapters=[TwoCaptchaAdapter("test-key")],
                time=_fast_time(),
                retry=_fast_retry(),
            ) as solver,
            pytest.raises(NoSolutionError),
        ):
            solver.solve(TwoCaptchaImageChallenge(b"png"))


def test_unknown_task_fails_fast_provider_error() -> None:
    with respx.mock:
        respx.post("https://api.2captcha.com/createTask").mock(
            return_value=httpx.Response(200, content=_j(errorId=0, taskId=4))
        )
        respx.post("https://api.2captcha.com/getTaskResult").mock(
            return_value=httpx.Response(
                200, content=_j(errorId=16, errorCode="ERROR_TASK_NOT_FOUND")
            )
        )
        with (
            Solver(
                adapters=[TwoCaptchaAdapter("test-key")],
                time=_fast_time(),
                retry=_fast_retry(),
            ) as solver,
            pytest.raises(ProviderError),
        ):
            solver.solve(TwoCaptchaImageChallenge(b"png"))


def test_malformed_body_provider_error_preserves_raw() -> None:
    with respx.mock:
        respx.post("https://api.2captcha.com/createTask").mock(
            return_value=httpx.Response(200, content=b"not json")
        )
        with (
            Solver(adapters=[TwoCaptchaAdapter("test-key")]) as solver,
            pytest.raises(ProviderError) as excinfo,
        ):
            solver.submit(TwoCaptchaImageChallenge(b"png"))
    assert excinfo.value.raw_response == b"not json"
    assert isinstance(excinfo.value.__cause__, ValueError)


def test_wrong_shape_body_provider_error() -> None:
    with respx.mock:
        respx.post("https://api.2captcha.com/createTask").mock(
            return_value=httpx.Response(200, content=b"[1, 2]")
        )
        with (
            Solver(adapters=[TwoCaptchaAdapter("test-key")]) as solver,
            pytest.raises(ProviderError) as excinfo,
        ):
            solver.submit(TwoCaptchaImageChallenge(b"png"))
    assert excinfo.value.raw_response == b"[1, 2]"
    # Valid JSON that is not an object: no parse cause to chain, but the
    # verbatim body is preserved (ADR-0040).
    assert excinfo.value.__cause__ is None


def test_ready_with_empty_solution_raises_empty() -> None:
    with respx.mock:
        respx.post("https://api.2captcha.com/createTask").mock(
            return_value=httpx.Response(200, content=_j(errorId=0, taskId=7))
        )
        respx.post("https://api.2captcha.com/getTaskResult").mock(
            return_value=httpx.Response(
                200, content=_j(errorId=0, status="ready", solution={})
            )
        )
        with (
            Solver(
                adapters=[TwoCaptchaAdapter("test-key")],
                time=_fast_time(),
                retry=_fast_retry(),
            ) as solver,
            pytest.raises(EmptySolutionError),
        ):
            solver.solve(TwoCaptchaImageChallenge(b"png"))


def test_get_balance_wire() -> None:
    with respx.mock:
        route = respx.post("https://api.2captcha.com/getBalance").mock(
            return_value=httpx.Response(200, content=_j(errorId=0, balance="7.5"))
        )
        with Solver(adapters=[TwoCaptchaAdapter("test-key")]) as solver:
            balance = solver.get_balance("twocaptcha")
        request = route.calls.last.request
        assert str(request.url) == "https://api.2captcha.com/getBalance"
        assert _body(request) == {"clientKey": "test-key"}
    assert balance == Decimal("7.5")


def test_report_bad_good_wire_round_trip() -> None:
    with respx.mock:
        bad = respx.post("https://api.2captcha.com/reportIncorrect").mock(
            return_value=httpx.Response(200, content=_j(errorId=0, status="success"))
        )
        good = respx.post("https://api.2captcha.com/reportCorrect").mock(
            return_value=httpx.Response(200, content=_j(errorId=0, status="success"))
        )
        with Solver(adapters=[TwoCaptchaAdapter("test-key")]) as solver:
            ref = TaskRef(provider="twocaptcha", task_id=42)
            assert solver.report_bad_result(ref) is True
            assert solver.report_good_result(ref) is True
        assert _body(bad.calls.last.request) == {
            "clientKey": "test-key",
            "taskId": 42,
        }
        assert _body(good.calls.last.request) == {
            "clientKey": "test-key",
            "taskId": 42,
        }
        assert str(bad.calls.last.request.url) == (
            "https://api.2captcha.com/reportIncorrect"
        )
        assert str(good.calls.last.request.url) == (
            "https://api.2captcha.com/reportCorrect"
        )


def test_wait_ref_polls_with_task_id_payload() -> None:
    with respx.mock:
        route = respx.post("https://api.2captcha.com/getTaskResult").mock(
            return_value=httpx.Response(
                200,
                content=_j(
                    errorId=0,
                    status="ready",
                    solution={"gRecaptchaResponse": "tok123456"},
                ),
            )
        )
        with Solver(
            adapters=[TwoCaptchaAdapter("test-key")],
            time=_fast_time(),
            retry=_fast_retry(),
        ) as solver:
            status = solver.wait_ref(
                TaskRef(provider="twocaptcha", task_id=7), timeout=1.0
            )
        request = route.calls.last.request
        assert str(request.url) == "https://api.2captcha.com/getTaskResult"
        assert _body(request) == {"clientKey": "test-key", "taskId": 7}
    assert status.status is TaskStatus.READY


# -- error mapping at transport level (ADR-0009) ----------------------------

SUBMIT_ERROR_CASES: list[tuple[str, object, object, str, type[BaseException]]] = [
    (
        "twocaptcha",
        TwoCaptchaAdapter("test-key"),
        TwoCaptchaImageChallenge(b"png"),
        "ERROR_KEY_DOES_NOT_EXIST",
        AuthenticationError,
    ),
    (
        "anti-captcha",
        AntiCaptchaAdapter("test-key"),
        AntiCaptchaImageChallenge(b"png"),
        "ERROR_IP_NOT_ALLOWED",
        AuthenticationError,
    ),
    (
        "capmonster",
        CapMonsterAdapter("test-key"),
        CapMonsterImageChallenge(b"png"),
        "ERROR_ZERO_BALANCE",
        InsufficientBalanceError,
    ),
    (
        "capsolver",
        CapsolverAdapter("test-key"),
        CapsolverImageChallenge(b"png"),
        "ERROR_NO_SLOT_AVAILABLE",
        ServiceBusyError,
    ),
]


@pytest.mark.parametrize(
    "case", SUBMIT_ERROR_CASES, ids=[c[0] for c in SUBMIT_ERROR_CASES]
)
def test_submit_provider_error_maps_kind(case: tuple[object, ...]) -> None:
    _, adapter, challenge, code, exc_cls = case  # type: ignore[misc]
    with respx.mock:
        respx.post(f"{adapter.base_url}/createTask").mock(
            return_value=httpx.Response(
                200, content=_j(errorId=1, errorCode=code, errorDescription="boom")
            )
        )
        with (
            Solver(adapters=[adapter], retry=_fast_retry()) as solver,
            pytest.raises(exc_cls) as excinfo,
        ):
            solver.submit(challenge)
    assert excinfo.value.raw_response == _j(
        errorId=1, errorCode=code, errorDescription="boom"
    )


def test_submit_http_429_rate_limit() -> None:
    with respx.mock:
        create = respx.post("https://api.2captcha.com/createTask").mock(
            return_value=httpx.Response(429, content=b"slow down")
        )
        with (
            Solver(
                adapters=[TwoCaptchaAdapter("test-key")], retry=_fast_retry()
            ) as solver,
            pytest.raises(RateLimitError),
        ):
            solver.submit(TwoCaptchaImageChallenge(b"png"))
    assert create.call_count == 2


BALANCE_ERROR_CASES: list[tuple[str, object]] = [
    ("twocaptcha", TwoCaptchaAdapter("test-key")),
    ("anti-captcha", AntiCaptchaAdapter("test-key")),
    ("capmonster", CapMonsterAdapter("test-key")),
    ("capsolver", CapsolverAdapter("test-key")),
]


@pytest.mark.parametrize(
    "case", BALANCE_ERROR_CASES, ids=[c[0] for c in BALANCE_ERROR_CASES]
)
def test_balance_zero_raises_insufficient(case: tuple[object, ...]) -> None:
    adapter = case[1]  # type: ignore[index]
    with respx.mock:
        respx.post(f"{adapter.base_url}/getBalance").mock(
            return_value=httpx.Response(
                200, content=_j(errorId=1, errorCode="ERROR_ZERO_BALANCE")
            )
        )
        with (
            Solver(adapters=[adapter]) as solver,
            pytest.raises(InsufficientBalanceError),
        ):
            solver.get_balance(adapter.provider)


# -- support matrix (ADR-0057, ADR-0068) ------------------------------------


@pytest.mark.parametrize("provider", ["capmonster", "capsolver"])
def test_text_kind_unsupported_raises(provider: str) -> None:
    adapter_cls = CapMonsterAdapter if provider == "capmonster" else CapsolverAdapter
    with (
        Solver(adapters=[adapter_cls("test-key")]) as solver,
        pytest.raises(UnsupportedChallengeError),
    ):
        solver.solve(TextChallenge("2+2?"))


REPORT_UNSUPPORTED_CASES: list[tuple[str, object]] = [
    ("anti-captcha", AntiCaptchaAdapter("test-key")),
    ("capmonster", CapMonsterAdapter("test-key")),
    ("capsolver", CapsolverAdapter("test-key")),
]


@pytest.mark.parametrize(
    "case", REPORT_UNSUPPORTED_CASES, ids=[c[0] for c in REPORT_UNSUPPORTED_CASES]
)
def test_report_bad_unsupported_raises(case: tuple[object, ...]) -> None:
    adapter = case[1]  # type: ignore[index]
    with Solver(adapters=[adapter]) as solver, pytest.raises(UnsupportedChallengeError):
        solver.report_bad_result(TaskRef(provider=adapter.provider, task_id=1))


def test_report_good_unsupported_raises_capmonster() -> None:
    with (
        Solver(adapters=[CapMonsterAdapter("test-key")]) as solver,
        pytest.raises(UnsupportedChallengeError),
    ):
        solver.report_good_result(TaskRef(provider="capmonster", task_id=1))


# -- async tier spot checks -------------------------------------------------


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c[0] for c in GOLDEN_CASES])
@pytest.mark.asyncio
async def test_async_golden_submit_wire_payload(case: tuple[object, ...]) -> None:
    _, adapter, challenge, url, expected = case  # type: ignore[misc]
    with respx.mock:
        route = respx.post(url).mock(
            return_value=httpx.Response(200, content=_j(errorId=0, taskId=5))
        )
        async with AsyncSolver(adapters=[adapter]) as solver:
            await solver.submit(challenge)
        request = route.calls.last.request
    assert request.method == "POST"
    assert str(request.url) == url
    assert _body(request) == expected


@pytest.mark.asyncio
async def test_async_instant_answer_fast_path() -> None:
    with respx.mock:
        respx.post("https://api.capsolver.com/createTask").mock(
            return_value=httpx.Response(
                200,
                content=_j(
                    errorId=0,
                    status="ready",
                    taskId="61138bb6-19fb-11ec-a9c8-0242ac110006",
                    solution={"text": "instant"},
                ),
            )
        )
        poll = respx.post("https://api.capsolver.com/getTaskResult")
        async with AsyncSolver(
            adapters=[CapsolverAdapter("test-key")],
            time=_fast_time(),
            retry=_fast_retry(),
        ) as solver:
            result = await solver.solve(CapsolverImageChallenge(b"png"))
        assert result.solution.text == "instant"
        assert not poll.called


@pytest.mark.asyncio
async def test_async_submit_error_maps_kind() -> None:
    with respx.mock:
        respx.post("https://api.2captcha.com/createTask").mock(
            return_value=httpx.Response(
                200,
                content=_j(
                    errorId=1,
                    errorCode="ERROR_KEY_DOES_NOT_EXIST",
                    errorDescription="bad key",
                ),
            )
        )
        async with AsyncSolver(
            adapters=[TwoCaptchaAdapter("test-key")], retry=_fast_retry()
        ) as solver:
            with pytest.raises(AuthenticationError):
                await solver.submit(TwoCaptchaImageChallenge(b"png"))
