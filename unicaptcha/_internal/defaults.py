"""Per-kind timing defaults and the config resolution chain (ADR-0030,
ADR-0043). The engine resolves ``per-call -> client -> kind-default ->
generic fallback`` field-wise via ``merge_configs``; the resolved result is
concrete (no ``None`` fields) so the loops use plain floats/ints.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from unicaptcha._internal.config import merge_configs
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge import (
    FunCaptchaChallenge,
    GeeTestV3Challenge,
    GeeTestV4Challenge,
    HCaptchaChallenge,
    ImageChallenge,
    RecaptchaV2Challenge,
    RecaptchaV3Challenge,
    TextChallenge,
    TurnstileChallenge,
)
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.types import RetryConfig, TimeConfig


@dataclass(frozen=True, slots=True)
class KindTiming:
    poll_delay: float
    poll_interval: float
    total_timeout: float


@dataclass(frozen=True, slots=True)
class ResolvedTime:
    """Concrete solve-timeline values (no ``None`` fields)."""

    poll_delay: float
    poll_interval: float
    total_timeout: float

    @classmethod
    def from_config(cls, cfg: TimeConfig | None) -> ResolvedTime:
        generic = GENERIC_TIMING
        return cls(
            poll_delay=cfg.poll_delay
            if cfg and cfg.poll_delay is not None
            else generic.poll_delay,
            poll_interval=cfg.poll_interval
            if cfg and cfg.poll_interval is not None
            else generic.poll_interval,
            total_timeout=cfg.total_timeout
            if cfg and cfg.total_timeout is not None
            else generic.total_timeout,
        )

    def to_config(self) -> TimeConfig:
        return TimeConfig(
            total_timeout=self.total_timeout,
            poll_interval=self.poll_interval,
            poll_delay=self.poll_delay,
        )


@dataclass(frozen=True, slots=True)
class ResolvedRetry:
    """Concrete retry values (no ``None`` fields)."""

    max_attempts: int
    backoff_base: float
    backoff_cap: float

    @classmethod
    def from_config(cls, cfg: RetryConfig | None) -> ResolvedRetry:
        return cls(
            max_attempts=cfg.max_attempts
            if cfg and cfg.max_attempts is not None
            else 3,
            backoff_base=cfg.backoff_base
            if cfg and cfg.backoff_base is not None
            else 1.0,
            backoff_cap=cfg.backoff_cap
            if cfg and cfg.backoff_cap is not None
            else 30.0,
        )


# ADR-0030: reCAPTCHA-class 15/5/120, image/text 5/2/30, FunCaptcha/GeeTest
# 10/3/180, Turnstile 5/3/120 (delay/interval/total).
_KIND_TIMINGS: Mapping[type[BaseChallenge], KindTiming] = {
    ImageChallenge: KindTiming(5.0, 2.0, 30.0),
    TextChallenge: KindTiming(5.0, 2.0, 30.0),
    RecaptchaV2Challenge: KindTiming(15.0, 5.0, 120.0),
    RecaptchaV3Challenge: KindTiming(15.0, 5.0, 120.0),
    HCaptchaChallenge: KindTiming(15.0, 5.0, 120.0),
    FunCaptchaChallenge: KindTiming(10.0, 3.0, 180.0),
    GeeTestV3Challenge: KindTiming(10.0, 3.0, 180.0),
    GeeTestV4Challenge: KindTiming(10.0, 3.0, 180.0),
    TurnstileChallenge: KindTiming(5.0, 3.0, 120.0),
}

GENERIC_TIMING = KindTiming(10.0, 5.0, 120.0)


def kind_of(challenge: BaseChallenge) -> type[BaseChallenge] | None:
    """The challenge's kind base, derived via MRO inspection (ADR-0048)."""
    for cls in type(challenge).__mro__:
        if cls in _KIND_TIMINGS:
            return cls
    return None


def _declared_timing(
    adapter: BaseAdapter, challenge: BaseChallenge
) -> TimeConfig | None:
    declared = adapter.default_task_config
    if not declared:
        return None
    for cls, cfg in declared.items():
        if isinstance(challenge, cls):
            return cfg
    return None


def resolve_time(
    challenge: BaseChallenge,
    adapter: BaseAdapter,
    client: TimeConfig | None,
    per_call: TimeConfig | None,
) -> ResolvedTime:
    """Resolve the concrete solve-timeline config (ADR-0043 chain)."""
    kind = kind_of(challenge)
    timing = _KIND_TIMINGS[kind] if kind is not None else GENERIC_TIMING
    base = TimeConfig(
        total_timeout=timing.total_timeout,
        poll_interval=timing.poll_interval,
        poll_delay=timing.poll_delay,
    )
    declared = _declared_timing(adapter, challenge)
    if declared is not None:
        base = merge_configs(base, declared)
    if client is not None:
        base = merge_configs(base, client)
    if per_call is not None:
        base = merge_configs(base, per_call)
    return ResolvedTime.from_config(base)


def resolve_retry(
    client: RetryConfig | None,
    per_call: RetryConfig | None,
) -> ResolvedRetry:
    """Resolve the concrete retry config (defaults 3 attempts, 1/30 s)."""
    base = RetryConfig(max_attempts=3, backoff_base=1.0, backoff_cap=30.0)
    if client is not None:
        base = merge_configs(base, client)
    if per_call is not None:
        base = merge_configs(base, per_call)
    return ResolvedRetry.from_config(base)


__all__ = [
    "GENERIC_TIMING",
    "KindTiming",
    "ResolvedRetry",
    "ResolvedTime",
    "kind_of",
    "resolve_retry",
    "resolve_time",
]
