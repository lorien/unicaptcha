"""Reference third-party adapter contract tests (ADR-0046, task 15).

``tests/_myservice.py`` implements the public adapter SDK exactly as an
external author would; these tests prove it works through the real engine
and that it never touches ``unicaptcha._internal``.
"""

import ast
import json
from pathlib import Path

import httpx
import pytest
import respx
from _myservice import (
    MyServiceAdapter,
    MyServiceImageChallenge,
    MyServiceImageSolution,
    MyServiceRecaptchaV2Challenge,
)

from unicaptcha import AsyncSolver, Solver
from unicaptcha.errors import AuthenticationError
from unicaptcha.types import TaskRef, TaskStatus

BASE = "https://myservice.example"
CREATE = f"{BASE}/createTask"
POLL = f"{BASE}/getTaskResult"
BALANCE = f"{BASE}/getBalance"
REPORT = f"{BASE}/reportIncorrect"


def _j(**data: object) -> bytes:
    return json.dumps(data).encode()


# -- public-boundary guard ------------------------------------------------


def test_reference_adapter_never_imports_internal() -> None:
    """ADR-0046: the reference adapter is written as an external author
    would be — public imports only. If it ever imports ``_internal``,
    internal refactors could silently break third-party adapters."""
    source = Path(__file__).parent / "_myservice.py"
    tree = ast.parse(source.read_text())
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "unicaptcha._internal" or alias.name.startswith(
                    "unicaptcha._internal."
                ):
                    bad.append(alias.name)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and (
                node.module == "unicaptcha._internal"
                or node.module.startswith("unicaptcha._internal.")
            )
        ):
            bad.append(node.module)
    assert not bad, f"reference adapter must not import _internal: {bad}"


def test_reference_adapter_registers_with_provider() -> None:
    adapter = MyServiceAdapter("test-key")
    assert adapter.provider == "myservice"
    assert adapter.base_url == BASE
    solver = Solver(adapters=[adapter])
    assert solver is not None


# -- full-engine solves through the real Solver ---------------------------


@respx.mock
def test_sync_solve_through_engine(fast_time, fast_retry) -> None:
    respx.post(CREATE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, taskId=7))
    )
    respx.post(POLL).mock(
        return_value=httpx.Response(
            200,
            content=_j(
                errorId=0,
                status="ready",
                cost="0.00025",
                solution={"text": "hello"},
            ),
        )
    )
    with Solver(
        adapters=[MyServiceAdapter("test-key")],
        time=fast_time,
        retry=fast_retry,
    ) as solver:
        result = solver.solve(MyServiceImageChallenge(b"png"))
    assert result.task_id == 7
    assert result.provider == "myservice"
    assert isinstance(result.solution, MyServiceImageSolution)
    assert result.solution.text == "hello"
    assert result.task_ref == TaskRef("myservice", 7)


@respx.mock
@pytest.mark.asyncio
async def test_async_solve_through_engine(fast_time, fast_retry) -> None:
    respx.post(CREATE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, taskId=9))
    )
    respx.post(POLL).mock(
        return_value=httpx.Response(
            200,
            content=_j(
                errorId=0,
                status="ready",
                solution={"gRecaptchaResponse": "tok123456"},
            ),
        )
    )
    async with AsyncSolver(
        adapters=[MyServiceAdapter("test-key")],
        time=fast_time,
        retry=fast_retry,
    ) as solver:
        result = await solver.solve(
            MyServiceRecaptchaV2Challenge(sitekey="sk", pageurl="https://page")
        )
    assert result.task_id == 9
    assert result.solution.token == "tok123456"


@respx.mock
def test_kind_base_routing_upcasts(fast_time, fast_retry) -> None:
    from unicaptcha import ImageChallenge

    respx.post(CREATE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, taskId=3))
    )
    respx.post(POLL).mock(
        return_value=httpx.Response(
            200, content=_j(errorId=0, status="ready", solution={"text": "up"})
        )
    )
    with Solver(
        adapters=[MyServiceAdapter("test-key")],
        time=fast_time,
        retry=fast_retry,
    ) as solver:
        result = solver.solve(ImageChallenge(b"png"), provider="myservice")
    assert result.provider == "myservice"
    assert result.solution.text == "up"


# -- instant fast path ------------------------------------------------------


@respx.mock
def test_submit_ready_instant_fast_path(fast_time, fast_retry) -> None:
    respx.post(CREATE).mock(
        return_value=httpx.Response(
            200,
            content=_j(
                errorId=0,
                status="ready",
                taskId=5,
                solution={"text": "instant"},
            ),
        )
    )
    with Solver(
        adapters=[MyServiceAdapter("test-key")],
        time=fast_time,
        retry=fast_retry,
    ) as solver:
        ticket = solver.submit(MyServiceImageChallenge(b"png"))
        result = solver.wait(ticket)
    assert ticket.instant_answer is not None
    assert result.solution.text == "instant"


# -- auxiliary operations ----------------------------------------------------


@respx.mock
def test_aux_ops_balance_status_reports(fast_time, fast_retry) -> None:
    respx.post(BALANCE).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, balance="7.5"))
    )
    respx.post(POLL).mock(
        return_value=httpx.Response(
            200, content=_j(errorId=0, status="ready", solution={"text": "x"})
        )
    )
    respx.post(REPORT).mock(
        return_value=httpx.Response(200, content=_j(errorId=0, status="success"))
    )
    respx.post(f"{BASE}/reportCorrect").mock(
        return_value=httpx.Response(200, content=_j(errorId=0, status="success"))
    )
    with Solver(
        adapters=[MyServiceAdapter("test-key")],
        time=fast_time,
        retry=fast_retry,
    ) as solver:
        balance = solver.get_balance("myservice")
        assert balance == 7.5 or str(balance) == "7.5"
        status = solver.get_task_status(TaskRef("myservice", 5))
        assert status.status is TaskStatus.READY
        assert solver.report_bad_result(TaskRef("myservice", 5)) is True
        assert solver.report_good_result(TaskRef("myservice", 5)) is True


# -- error mapping -----------------------------------------------------------


@respx.mock
def test_submit_error_maps_to_public_exception(fast_time, fast_retry) -> None:
    respx.post(CREATE).mock(
        return_value=httpx.Response(
            200,
            content=_j(
                errorId=1,
                errorCode="ERROR_KEY_DOES_NOT_EXIST",
                errorDescription="bad key",
            ),
        )
    )
    with (
        pytest.raises(AuthenticationError),
        Solver(
            adapters=[MyServiceAdapter("test-key")],
            time=fast_time,
            retry=fast_retry,
        ) as solver,
    ):
        solver.solve(MyServiceImageChallenge(b"png"))


def test_map_provider_error_kinds() -> None:
    from unicaptcha.errors import ErrorKind

    a = MyServiceAdapter("test-key")
    kind, _ = a.map_provider_error(_j(errorId=1, errorCode="ERROR_TOO_MANY_REQUESTS"))
    assert kind is ErrorKind.RATE_LIMIT
    kind, _ = a.map_provider_error(_j(errorId=1, errorCode="ERROR_KEY_DOES_NOT_EXIST"))
    assert kind is ErrorKind.AUTHENTICATION
