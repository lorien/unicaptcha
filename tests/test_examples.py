"""Examples consistency guards.

Every file under ``examples/`` must stay syntactically valid
(``compile()``), and every ``examples/`` path referenced from the READMEs
must resolve to a real file.

Examples also execute against a respx-mocked 2Captcha transport (no
credits, CI-speed): each module's ``__main__`` block is run and must
complete without an ``AttributeError`` or other API misuse. This closes
the gap where a ``compile()``-only check missed the facade misuse in
``examples/sync/proxy.py`` (caught by live smoke). Example scripts are
import-safe: executable code lives under ``if __name__ == "__main__":``.
"""

import json
import re
import runpy
from pathlib import Path

import httpx
import pytest
import respx

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"

API_KEY_ENV = "UNICAPTCHA_TWOCAPTCHA_API_KEY"
BASE = "https://api.2captcha.com"
CREATE = f"{BASE}/createTask"
POLL = f"{BASE}/getTaskResult"
BALANCE = f"{BASE}/getBalance"
REPORT_GOOD = f"{BASE}/reportCorrect"
REPORT_BAD = f"{BASE}/reportIncorrect"


def _example_sources() -> list[tuple[Path, str]]:
    return [
        (path, path.read_text(encoding="utf-8"))
        for path in sorted(EXAMPLES.rglob("*.py"))
    ]


def test_examples_compile() -> None:
    sources = _example_sources()
    assert sources, "examples/ contains no Python files"
    for path, source in sources:
        compile(source, str(path), "exec")


def test_examples_are_provider_annotated() -> None:
    for path, source in _example_sources():
        assert "Anti-Captcha" in source and "Capsolver" in source, (
            f"{path.name} must name the other providers in its header note"
        )


def test_examples_are_import_safe() -> None:
    for path in sorted(EXAMPLES.rglob("*.py")):
        namespace: dict[str, object] = {}
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
        assert "__main__" not in namespace, (
            f"{path.relative_to(EXAMPLES)} runs code at import time; "
            'wrap it in `if __name__ == "__main__":`'
        )


def test_readme_links_resolve() -> None:
    for readme in (EXAMPLES / "README.md", ROOT / "README.md"):
        for match in re.finditer(r"\((examples/[^)#\s]+)\)", readme.read_text()):
            assert (ROOT / match.group(1)).exists(), (
                f"{readme.name} links to missing {match.group(1)}"
            )


def test_sync_async_mirrors_match() -> None:
    sync = sorted(p.name for p in (EXAMPLES / "sync").glob("*.py"))
    async_names = sorted(p.name for p in (EXAMPLES / "async").glob("*.py"))
    assert sync == async_names, "sync/ and async/ examples must mirror 1:1"
    expected = {
        "aux_ops.py",
        "auto_solve.py",
        "errors.py",
        "events.py",
        "funcaptcha.py",
        "geetest_v3.py",
        "geetest_v4.py",
        "hcaptcha.py",
        "image.py",
        "proxy.py",
        "recaptcha_v2.py",
        "recaptcha_v3.py",
        "text.py",
        "turnstile.py",
        "two_phase.py",
        "universal_client.py",
    }
    assert set(sync) == expected


# -- execution (respx-mocked transport, no credits) ----------------------


# Instant-ready solution shapes per example, mirroring TwoCaptchaAdapter's
# `_solution_from` dispatch (image/text -> {"text": ...}; v2 ->
# gRecaptchaResponse; v3 -> gRecaptchaResponse + token without score;
# hCaptcha/FunCaptcha/Turnstile -> token-only; GeeTest v3 ->
# challenge/validate/seccode; GeeTest v4 -> the five-field shape).
SOLUTION = {
    "image.py": {"text": "demo-answer"},
    "text.py": {"text": "demo-answer"},
    "universal_client.py": {"text": "demo-answer"},
    "auto_solve.py": {"gRecaptchaResponse": "auto-token"},
    "proxy.py": {"text": "demo-answer"},
    "two_phase.py": {"text": "demo-answer"},
    "aux_ops.py": {"text": "demo-answer"},
    "events.py": {"text": "demo-answer"},
    "recaptcha_v2.py": {"gRecaptchaResponse": "v2-token"},
    "recaptcha_v3.py": {"gRecaptchaResponse": "v3-token", "token": "v3-token"},
    "hcaptcha.py": {"token": "hcap-token"},
    "funcaptcha.py": {"token": "fc-token"},
    "turnstile.py": {"token": "turnstile-token"},
    "geetest_v3.py": {"challenge": "ch", "validate": "val", "seccode": "sec"},
    "geetest_v4.py": {
        "captcha_id": "cid",
        "lot_number": "ln",
        "pass_token": "pt",
        "gen_time": "gt",
        "captcha_output": "co",
    },
}

# A marker each happy-path example prints on completion, so a run that
# silently short-circuits still fails the test.
EXPECTED_OUTPUT = {
    "image.py": "solved:",
    "text.py": "solved:",
    "universal_client.py": "solved:",
    "auto_solve.py": "token:",
    "proxy.py": "solved:",
    "two_phase.py": "solved:",
    "aux_ops.py": "reported good",
    "events.py": "solved:",
    "recaptcha_v2.py": "token:",
    "recaptcha_v3.py": "token:",
    "hcaptcha.py": "token:",
    "funcaptcha.py": "token:",
    "turnstile.py": "token:",
    "geetest_v3.py": "challenge:",
    "geetest_v4.py": "captcha_output:",
}


def _ok(**data: object) -> bytes:
    return json.dumps({"errorId": 0, **data}).encode()


def _ready(solution: dict[str, object]) -> bytes:
    return _ok(status="ready", taskId=1001, solution=solution)


def _install_transport(router: respx.MockRouter, solution: dict[str, object]) -> None:
    router.post(CREATE).mock(return_value=httpx.Response(200, content=_ready(solution)))
    router.post(POLL).mock(return_value=httpx.Response(200, content=_ready(solution)))
    router.post(BALANCE).mock(
        return_value=httpx.Response(200, content=_ok(balance="1.50"))
    )
    router.post(REPORT_GOOD).mock(
        return_value=httpx.Response(200, content=_ok(status="success"))
    )
    router.post(REPORT_BAD).mock(
        return_value=httpx.Response(200, content=_ok(status="success"))
    )


def _ids(path: Path) -> str:
    return str(path.relative_to(EXAMPLES))


@pytest.mark.parametrize(
    "example",
    sorted(p for p in EXAMPLES.rglob("*.py") if p.name != "errors.py"),
    ids=_ids,
)
def test_examples_execute(
    example: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    solution = SOLUTION[example.name]
    monkeypatch.setenv(API_KEY_ENV, "test-key")
    with respx.mock as router:
        _install_transport(router, solution)
        runpy.run_path(str(example), run_name="__main__")
    out = capsys.readouterr().out
    assert EXPECTED_OUTPUT[example.name] in out


@pytest.mark.parametrize(
    "example",
    sorted(p for p in EXAMPLES.rglob("*.py") if p.name == "errors.py"),
    ids=_ids,
)
def test_error_example_exercises_except_branch(
    example: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(API_KEY_ENV, "test-key")
    error_body = _ok(
        errorId=1, errorCode="ERROR_ZERO_BALANCE", errorDescription="no funds"
    )
    with respx.mock as router:
        router.post(CREATE).mock(return_value=httpx.Response(200, content=error_body))
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_path(str(example), run_name="__main__")
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "kind=" in out
