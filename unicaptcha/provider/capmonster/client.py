"""Provider facades over CapMonster (ADR-0007 peers model).

``CapMonsterClient`` / ``AsyncCapMonsterClient`` own their adapter
statically and delegate to an internal TaskEngine each — no universal
client appears in the object graph (peers, not nesting). Constructors have
full parity with ``Solver`` minus ``adapters`` (ADR-0061); every solving
method carries full per-call parity (``time=``/``retry=``/``on_event=``,
ADR-0051). Aux operations mirror the universal client names.
"""

from __future__ import annotations

import threading
import time as _time_module
from collections.abc import Callable, Mapping
from dataclasses import fields
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import TypeVar, cast

import httpx

from unicaptcha._internal.async_engine import AsyncTaskEngine
from unicaptcha._internal.engine import TaskEngine
from unicaptcha._internal.handlers import check_sync_handler, emit_async, emit_sync
from unicaptcha._internal.http import AsyncHttpTransport, HttpTransport
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.challenge.funcaptcha import FunCaptchaChallenge
from unicaptcha.challenge.geetest import GeeTestV3Challenge, GeeTestV4Challenge
from unicaptcha.challenge.hcaptcha import HCaptchaChallenge
from unicaptcha.challenge.image import ImageChallenge
from unicaptcha.challenge.recaptcha_v2 import RecaptchaV2Challenge
from unicaptcha.challenge.recaptcha_v3 import RecaptchaV3Challenge
from unicaptcha.challenge.turnstile import TurnstileChallenge
from unicaptcha.errors import ClientClosedError, ErrorKind, InvalidChallengeError
from unicaptcha.events import (
    AsyncEventHandler,
    SyncEventHandler,
    TaskEvent,
    TaskEventKind,
)
from unicaptcha.provider.capmonster.adapter import CapMonsterAdapter
from unicaptcha.provider.capmonster.challenge import (
    CapMonsterFunCaptchaChallenge,
    CapMonsterGeeTestV3Challenge,
    CapMonsterGeeTestV4Challenge,
    CapMonsterHCaptchaChallenge,
    CapMonsterImageChallenge,
    CapMonsterRecaptchaV2Challenge,
    CapMonsterRecaptchaV3Challenge,
    CapMonsterTurnstileChallenge,
)
from unicaptcha.provider.capmonster.solution import (
    CapMonsterFunCaptchaSolution,
    CapMonsterGeeTestV3Solution,
    CapMonsterGeeTestV4Solution,
    CapMonsterHCaptchaSolution,
    CapMonsterImageSolution,
    CapMonsterRecaptchaV2Solution,
    CapMonsterRecaptchaV3Solution,
    CapMonsterTurnstileSolution,
)
from unicaptcha.solution.base import BaseSolution
from unicaptcha.types import (
    NetworkConfig,
    Proxy,
    RetryConfig,
    SecretStr,
    TaskRef,
    TaskResult,
    TaskStatusResult,
    TaskTicket,
    TimeConfig,
)

PROVIDER = CapMonsterAdapter.provider

_ResultT = TypeVar("_ResultT", bound=BaseSolution)

_PROVIDER_CHALLENGES: tuple[type[BaseChallenge], ...] = (
    CapMonsterImageChallenge,
    CapMonsterRecaptchaV2Challenge,
    CapMonsterRecaptchaV3Challenge,
    CapMonsterHCaptchaChallenge,
    CapMonsterFunCaptchaChallenge,
    CapMonsterGeeTestV3Challenge,
    CapMonsterGeeTestV4Challenge,
    CapMonsterTurnstileChallenge,
)


def _pre_flight_event(detail: str, start: float) -> TaskEvent:
    return TaskEvent(
        kind=TaskEventKind.PRE_FLIGHT_FAILED,
        provider=PROVIDER,
        elapsed=timedelta(seconds=_time_module.monotonic() - start),
        attempt=1,
        task_id=None,
        detail=detail,
        error_kind=ErrorKind.INVALID_CHALLENGE,
    )


def _ref_of(task: TaskRef | int) -> TaskRef:
    if isinstance(task, int):
        return TaskRef(provider=PROVIDER, task_id=task)
    if task.provider != PROVIDER:
        raise TypeError(
            f"TaskRef belongs to provider {task.provider!r}, "
            f"but this client serves {PROVIDER!r}"
        )
    return task


_KIND_TO_CONCRETE: tuple[tuple[type[BaseChallenge], type[BaseChallenge]], ...] = (
    (ImageChallenge, CapMonsterImageChallenge),
    (RecaptchaV2Challenge, CapMonsterRecaptchaV2Challenge),
    (RecaptchaV3Challenge, CapMonsterRecaptchaV3Challenge),
    (HCaptchaChallenge, CapMonsterHCaptchaChallenge),
    (FunCaptchaChallenge, CapMonsterFunCaptchaChallenge),
    (GeeTestV3Challenge, CapMonsterGeeTestV3Challenge),
    (GeeTestV4Challenge, CapMonsterGeeTestV4Challenge),
    (TurnstileChallenge, CapMonsterTurnstileChallenge),
)


def _upcast(challenge: BaseChallenge) -> BaseChallenge:
    """Return the challenge as-is, or upcast a kind-base instance to its
    CapMonster concrete class (kind bases are instantiable, ADR-0064)."""
    for concrete in _PROVIDER_CHALLENGES:
        if isinstance(challenge, concrete):
            return challenge
    names = {f.name for f in fields(type(challenge))}
    for kind_base, concrete_cls in _KIND_TO_CONCRETE:
        if isinstance(challenge, kind_base):
            kwargs = {
                f.name: getattr(challenge, f.name)
                for f in fields(concrete_cls)
                if f.name in names
            }
            return concrete_cls(**kwargs)
    raise TypeError(f"{type(challenge).__name__} is not supported by {PROVIDER!r}")


class CapMonsterClient:
    """Blocking facade over the CapMonster JSON API."""

    __slots__ = (
        "_adapter",
        "_closed",
        "_default_proxy",
        "_engine",
        "_name",
        "_on_event",
    )

    def __init__(
        self,
        api_key: SecretStr | str,
        *,
        base_url: str | None = None,
        referral: bool | str = True,
        name: str | None = None,
        user_agent: str | None = None,
        proxy: Proxy | None = None,
        abandoned_registry_limit: int | None = 1000,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        network: NetworkConfig | None = None,
        network_client: httpx.Client | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> None:
        check_sync_handler(on_event, what="CapMonsterClient(on_event)")
        self._adapter = CapMonsterAdapter(api_key, base_url, referral=referral)
        self._default_proxy = proxy
        self._on_event = on_event
        self._closed = False
        transport = HttpTransport(
            network=network, network_client=network_client, user_agent=user_agent
        )
        self._engine: TaskEngine[BaseSolution] = TaskEngine(
            transport,
            shutdown=threading.Event(),
            time=time,
            retry=retry,
            on_event=on_event,
            abandoned_registry_limit=abandoned_registry_limit,
        )
        self._name = name  # context-only identity (ADR-0018)

    # -- lifecycle --------------------------------------------------------

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._engine.close()

    def __enter__(self) -> CapMonsterClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get_abandoned_tasks(self) -> tuple[TaskRef, ...]:
        return self._engine.get_abandoned_tasks()

    # -- internal plumbing --------------------------------------------------

    def _handler_for(
        self, on_event: SyncEventHandler | None
    ) -> SyncEventHandler | None:
        if on_event is not None:
            check_sync_handler(on_event, what="CapMonsterClient(on_event=)")
            return on_event
        return self._on_event

    def _proxy_for(self, proxy: Proxy | None) -> Proxy | None:
        """ADR-0012 chain: per-call value, then the client default."""
        return proxy if proxy is not None else self._default_proxy

    def _checked_open(self) -> None:
        if self._closed:
            raise ClientClosedError("client is closed")

    def _solve(
        self,
        build: Callable[[], BaseChallenge],
        *,
        result_type: type[_ResultT],
        time: TimeConfig | None,
        retry: RetryConfig | None,
        on_event: SyncEventHandler | None,
    ) -> TaskResult[_ResultT]:
        self._checked_open()
        handler = self._handler_for(on_event)
        start = _time_module.monotonic()
        try:
            challenge = build()
        except InvalidChallengeError as exc:
            if handler is not None:
                emit_sync(handler, _pre_flight_event(str(exc), start))
            raise
        return cast(
            "TaskResult[_ResultT]",
            self._engine.solve(
                self._adapter, challenge, time=time, retry=retry, on_event=handler
            ),
        )

    # -- solving (kind convenience methods) ---------------------------------

    def solve_image(
        self,
        body: bytes | str,
        *,
        case: bool = False,
        numeric: int = 0,
        math: bool = False,
        module_name: str | None = None,
        threshold: int | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterImageSolution]:
        def build() -> BaseChallenge:
            return CapMonsterImageChallenge(
                body if isinstance(body, bytes) else Path(body),
                case=case,
                numeric=numeric,
                math=math,
                module_name=module_name,
                threshold=threshold,
            )

        return self._solve(
            build,
            result_type=CapMonsterImageSolution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    def solve_recaptcha_v2(
        self,
        *,
        sitekey: str,
        pageurl: str,
        invisible: bool = False,
        is_enterprise: bool = False,
        data_s: Mapping[str, str] | None = None,
        action: str | None = None,
        api_domain: str | None = None,
        user_agent: str | None = None,
        cookies: Mapping[str, str] | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterRecaptchaV2Solution]:
        def build() -> BaseChallenge:
            return CapMonsterRecaptchaV2Challenge(
                sitekey=sitekey,
                pageurl=pageurl,
                invisible=invisible,
                is_enterprise=is_enterprise,
                data_s=data_s,
                action=action,
                api_domain=api_domain,
                user_agent=user_agent,
                cookies=cookies,
            )

        return self._solve(
            build,
            result_type=CapMonsterRecaptchaV2Solution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    def solve_recaptcha_v3(
        self,
        *,
        sitekey: str,
        pageurl: str,
        action: str | None = None,
        min_score: float | None = None,
        is_enterprise: bool = False,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterRecaptchaV3Solution]:
        def build() -> BaseChallenge:
            return CapMonsterRecaptchaV3Challenge(
                sitekey=sitekey,
                pageurl=pageurl,
                action=action,
                min_score=min_score,
                is_enterprise=is_enterprise,
            )

        return self._solve(
            build,
            result_type=CapMonsterRecaptchaV3Solution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    def solve_hcaptcha(
        self,
        *,
        sitekey: str,
        pageurl: str,
        is_invisible: bool = False,
        rqdata: str | None = None,
        fallback_to_actual_ua: bool | None = None,
        user_agent: str | None = None,
        cookies: Mapping[str, str] | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterHCaptchaSolution]:
        def build() -> BaseChallenge:
            return CapMonsterHCaptchaChallenge(
                sitekey=sitekey,
                pageurl=pageurl,
                is_invisible=is_invisible,
                rqdata=rqdata,
                fallback_to_actual_ua=fallback_to_actual_ua,
                user_agent=user_agent,
                cookies=cookies,
            )

        return self._solve(
            build,
            result_type=CapMonsterHCaptchaSolution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    def solve_funcaptcha(
        self,
        *,
        public_key: str,
        pageurl: str,
        data: str | None = None,
        service_url: str | None = None,
        user_agent: str | None = None,
        cookies: Mapping[str, str] | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterFunCaptchaSolution]:
        def build() -> BaseChallenge:
            return CapMonsterFunCaptchaChallenge(
                public_key=public_key,
                pageurl=pageurl,
                data=data,
                service_url=service_url,
                user_agent=user_agent,
                cookies=cookies,
            )

        return self._solve(
            build,
            result_type=CapMonsterFunCaptchaSolution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    def solve_geetest_v3(
        self,
        *,
        gt_key: str,
        challenge: str,
        pageurl: str,
        api_server: str | None = None,
        geetest_lib: str | None = None,
        user_agent: str | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterGeeTestV3Solution]:
        def build() -> BaseChallenge:
            return CapMonsterGeeTestV3Challenge(
                gt_key=gt_key,
                challenge=challenge,
                pageurl=pageurl,
                api_server=api_server,
                geetest_lib=geetest_lib,
                user_agent=user_agent,
            )

        return self._solve(
            build,
            result_type=CapMonsterGeeTestV3Solution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    def solve_geetest_v4(
        self,
        *,
        captcha_id: str,
        pageurl: str,
        risk_type: str | None = None,
        api_server: str | None = None,
        geetest_lib: str | None = None,
        user_agent: str | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterGeeTestV4Solution]:
        def build() -> BaseChallenge:
            return CapMonsterGeeTestV4Challenge(
                captcha_id=captcha_id,
                pageurl=pageurl,
                risk_type=risk_type,
                api_server=api_server,
                geetest_lib=geetest_lib,
                user_agent=user_agent,
            )

        return self._solve(
            build,
            result_type=CapMonsterGeeTestV4Solution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    def solve_turnstile(
        self,
        *,
        sitekey: str,
        pageurl: str,
        action: str | None = None,
        c_data: str | None = None,
        chl_page_data: str | None = None,
        cloudflare_task_type: str | None = None,
        html_page_base64: str | None = None,
        api_js_url: str | None = None,
        user_agent: str | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterTurnstileSolution]:
        def build() -> BaseChallenge:
            return CapMonsterTurnstileChallenge(
                sitekey=sitekey,
                pageurl=pageurl,
                action=action,
                c_data=c_data,
                chl_page_data=chl_page_data,
                cloudflare_task_type=cloudflare_task_type,
                html_page_base64=html_page_base64,
                api_js_url=api_js_url,
                user_agent=user_agent,
            )

        return self._solve(
            build,
            result_type=CapMonsterTurnstileSolution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    def submit(
        self,
        challenge: BaseChallenge,
        *,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskTicket[BaseSolution]:
        self._checked_open()
        prepared = _upcast(challenge)
        handler = self._handler_for(on_event)
        return self._engine.submit(
            self._adapter, prepared, retry=retry, on_event=handler
        )

    def wait(
        self, ticket: TaskTicket[BaseSolution], timeout: float | None = None
    ) -> TaskResult[BaseSolution]:
        self._checked_open()
        if ticket.task_ref.provider != PROVIDER:
            raise TypeError(
                f"ticket belongs to provider {ticket.task_ref.provider!r}, "
                f"but this client serves {PROVIDER!r}"
            )
        return self._engine.wait(self._adapter, ticket, timeout=timeout)

    def wait_ref(self, ref: TaskRef, timeout: float | None = None) -> TaskStatusResult:
        self._checked_open()
        checked = _ref_of(ref)
        return self._engine.wait_ref(self._adapter, checked, timeout=timeout)

    # -- auxiliary operations ------------------------------------------------

    def get_task_status(self, task: TaskRef | int) -> TaskStatusResult:
        self._checked_open()
        return self._engine.get_task_status(self._adapter, _ref_of(task))

    def get_balance(self) -> Decimal:
        self._checked_open()
        return self._engine.get_balance(self._adapter)

    def report_bad_result(self, task: TaskRef | int) -> bool:
        self._checked_open()
        return self._engine.report_bad_result(self._adapter, _ref_of(task))

    def report_good_result(self, task: TaskRef | int) -> bool:
        self._checked_open()
        return self._engine.report_good_result(self._adapter, _ref_of(task))


class AsyncCapMonsterClient:
    """Asyncio-native facade over the CapMonster JSON API."""

    __slots__ = (
        "_adapter",
        "_closed",
        "_default_proxy",
        "_engine",
        "_name",
        "_on_event",
    )

    def __init__(
        self,
        api_key: SecretStr | str,
        *,
        base_url: str | None = None,
        referral: bool | str = True,
        name: str | None = None,
        user_agent: str | None = None,
        proxy: Proxy | None = None,
        abandoned_registry_limit: int | None = 1000,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        network: NetworkConfig | None = None,
        network_client: httpx.AsyncClient | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> None:
        self._adapter = CapMonsterAdapter(api_key, base_url, referral=referral)
        self._default_proxy = proxy
        self._on_event = on_event
        self._closed = False
        transport = AsyncHttpTransport(
            network=network, network_client=network_client, user_agent=user_agent
        )
        self._engine: AsyncTaskEngine[BaseSolution] = AsyncTaskEngine(
            transport,
            time=time,
            retry=retry,
            on_event=on_event,
            abandoned_registry_limit=abandoned_registry_limit,
        )
        self._name = name  # context-only identity (ADR-0018)

    # -- lifecycle --------------------------------------------------------

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self._engine.aclose()

    async def __aenter__(self) -> AsyncCapMonsterClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    def get_abandoned_tasks(self) -> tuple[TaskRef, ...]:
        return self._engine.get_abandoned_tasks()

    # -- internal plumbing --------------------------------------------------

    def _handler_for(
        self, on_event: AsyncEventHandler | None
    ) -> AsyncEventHandler | None:
        return on_event if on_event is not None else self._on_event

    def _proxy_for(self, proxy: Proxy | None) -> Proxy | None:
        return proxy if proxy is not None else self._default_proxy

    def _checked_open(self) -> None:
        if self._closed:
            raise ClientClosedError("client is closed")

    async def _solve(
        self,
        build: Callable[[], BaseChallenge],
        *,
        result_type: type[_ResultT],
        time: TimeConfig | None,
        retry: RetryConfig | None,
        on_event: AsyncEventHandler | None,
    ) -> TaskResult[_ResultT]:
        self._checked_open()
        handler = self._handler_for(on_event)
        start = _time_module.monotonic()
        try:
            challenge = build()
        except InvalidChallengeError as exc:
            if handler is not None:
                await emit_async(handler, _pre_flight_event(str(exc), start))
            raise
        result = await self._engine.solve(
            self._adapter, challenge, time=time, retry=retry, on_event=handler
        )
        return cast("TaskResult[_ResultT]", result)

    # -- solving (kind convenience methods) ---------------------------------
    # Signatures mirror CapMonsterClient exactly; bodies are async twins.

    async def solve_image(
        self,
        body: bytes | str,
        *,
        case: bool = False,
        numeric: int = 0,
        math: bool = False,
        module_name: str | None = None,
        threshold: int | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterImageSolution]:
        def build() -> BaseChallenge:
            return CapMonsterImageChallenge(
                body if isinstance(body, bytes) else Path(body),
                case=case,
                numeric=numeric,
                math=math,
                module_name=module_name,
                threshold=threshold,
            )

        return await self._solve(
            build,
            result_type=CapMonsterImageSolution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    async def solve_recaptcha_v2(
        self,
        *,
        sitekey: str,
        pageurl: str,
        invisible: bool = False,
        is_enterprise: bool = False,
        data_s: Mapping[str, str] | None = None,
        action: str | None = None,
        api_domain: str | None = None,
        user_agent: str | None = None,
        cookies: Mapping[str, str] | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterRecaptchaV2Solution]:
        def build() -> BaseChallenge:
            return CapMonsterRecaptchaV2Challenge(
                sitekey=sitekey,
                pageurl=pageurl,
                invisible=invisible,
                is_enterprise=is_enterprise,
                data_s=data_s,
                action=action,
                api_domain=api_domain,
                user_agent=user_agent,
                cookies=cookies,
            )

        return await self._solve(
            build,
            result_type=CapMonsterRecaptchaV2Solution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    async def solve_recaptcha_v3(
        self,
        *,
        sitekey: str,
        pageurl: str,
        action: str | None = None,
        min_score: float | None = None,
        is_enterprise: bool = False,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterRecaptchaV3Solution]:
        def build() -> BaseChallenge:
            return CapMonsterRecaptchaV3Challenge(
                sitekey=sitekey,
                pageurl=pageurl,
                action=action,
                min_score=min_score,
                is_enterprise=is_enterprise,
            )

        return await self._solve(
            build,
            result_type=CapMonsterRecaptchaV3Solution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    async def solve_hcaptcha(
        self,
        *,
        sitekey: str,
        pageurl: str,
        is_invisible: bool = False,
        rqdata: str | None = None,
        fallback_to_actual_ua: bool | None = None,
        user_agent: str | None = None,
        cookies: Mapping[str, str] | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterHCaptchaSolution]:
        def build() -> BaseChallenge:
            return CapMonsterHCaptchaChallenge(
                sitekey=sitekey,
                pageurl=pageurl,
                is_invisible=is_invisible,
                rqdata=rqdata,
                fallback_to_actual_ua=fallback_to_actual_ua,
                user_agent=user_agent,
                cookies=cookies,
            )

        return await self._solve(
            build,
            result_type=CapMonsterHCaptchaSolution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    async def solve_funcaptcha(
        self,
        *,
        public_key: str,
        pageurl: str,
        data: str | None = None,
        service_url: str | None = None,
        user_agent: str | None = None,
        cookies: Mapping[str, str] | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterFunCaptchaSolution]:
        def build() -> BaseChallenge:
            return CapMonsterFunCaptchaChallenge(
                public_key=public_key,
                pageurl=pageurl,
                data=data,
                service_url=service_url,
                user_agent=user_agent,
                cookies=cookies,
            )

        return await self._solve(
            build,
            result_type=CapMonsterFunCaptchaSolution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    async def solve_geetest_v3(
        self,
        *,
        gt_key: str,
        challenge: str,
        pageurl: str,
        api_server: str | None = None,
        geetest_lib: str | None = None,
        user_agent: str | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterGeeTestV3Solution]:
        def build() -> BaseChallenge:
            return CapMonsterGeeTestV3Challenge(
                gt_key=gt_key,
                challenge=challenge,
                pageurl=pageurl,
                api_server=api_server,
                geetest_lib=geetest_lib,
                user_agent=user_agent,
            )

        return await self._solve(
            build,
            result_type=CapMonsterGeeTestV3Solution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    async def solve_geetest_v4(
        self,
        *,
        captcha_id: str,
        pageurl: str,
        risk_type: str | None = None,
        api_server: str | None = None,
        geetest_lib: str | None = None,
        user_agent: str | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterGeeTestV4Solution]:
        def build() -> BaseChallenge:
            return CapMonsterGeeTestV4Challenge(
                captcha_id=captcha_id,
                pageurl=pageurl,
                risk_type=risk_type,
                api_server=api_server,
                geetest_lib=geetest_lib,
                user_agent=user_agent,
            )

        return await self._solve(
            build,
            result_type=CapMonsterGeeTestV4Solution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    async def solve_turnstile(
        self,
        *,
        sitekey: str,
        pageurl: str,
        action: str | None = None,
        c_data: str | None = None,
        chl_page_data: str | None = None,
        cloudflare_task_type: str | None = None,
        html_page_base64: str | None = None,
        api_js_url: str | None = None,
        user_agent: str | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[CapMonsterTurnstileSolution]:
        def build() -> BaseChallenge:
            return CapMonsterTurnstileChallenge(
                sitekey=sitekey,
                pageurl=pageurl,
                action=action,
                c_data=c_data,
                chl_page_data=chl_page_data,
                cloudflare_task_type=cloudflare_task_type,
                html_page_base64=html_page_base64,
                api_js_url=api_js_url,
                user_agent=user_agent,
            )

        return await self._solve(
            build,
            result_type=CapMonsterTurnstileSolution,
            time=time,
            retry=retry,
            on_event=on_event,
        )

    async def submit(
        self,
        challenge: BaseChallenge,
        *,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskTicket[BaseSolution]:
        self._checked_open()
        prepared = _upcast(challenge)
        handler = self._handler_for(on_event)
        return await self._engine.submit(
            self._adapter, prepared, retry=retry, on_event=handler
        )

    async def wait(
        self, ticket: TaskTicket[BaseSolution], timeout: float | None = None
    ) -> TaskResult[BaseSolution]:
        self._checked_open()
        if ticket.task_ref.provider != PROVIDER:
            raise TypeError(
                f"ticket belongs to provider {ticket.task_ref.provider!r}, "
                f"but this client serves {PROVIDER!r}"
            )
        return await self._engine.wait(self._adapter, ticket, timeout=timeout)

    async def wait_ref(
        self, ref: TaskRef, timeout: float | None = None
    ) -> TaskStatusResult:
        self._checked_open()
        checked = _ref_of(ref)
        return await self._engine.wait_ref(self._adapter, checked, timeout=timeout)

    # -- auxiliary operations ------------------------------------------------

    async def get_task_status(self, task: TaskRef | int) -> TaskStatusResult:
        self._checked_open()
        return await self._engine.get_task_status(self._adapter, _ref_of(task))

    async def get_balance(self) -> Decimal:
        self._checked_open()
        return await self._engine.get_balance(self._adapter)

    async def report_bad_result(self, task: TaskRef | int) -> bool:
        self._checked_open()
        return await self._engine.report_bad_result(self._adapter, _ref_of(task))

    async def report_good_result(self, task: TaskRef | int) -> bool:
        self._checked_open()
        return await self._engine.report_good_result(self._adapter, _ref_of(task))


__all__ = ["AsyncCapMonsterClient", "CapMonsterClient"]
