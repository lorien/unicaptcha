"""Universal-client routing (ADR-0064, ADR-0012, ADR-0045).

Dispatch a challenge to its adapter, upcasting kind-base instances to the
adapter's concrete class before payload building. Raises pre-flight errors
(``TypeError`` / ``UnsupportedChallengeError``) with no network traffic.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Callable, Iterable, Mapping
from dataclasses import fields, replace
from typing import Any, NoReturn, cast

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
from unicaptcha.errors import ErrorKind, UnsupportedChallengeError
from unicaptcha.types import Proxy

_logger = logging.getLogger("unicaptcha")

KIND_BASES = frozenset(
    {
        ImageChallenge,
        TextChallenge,
        RecaptchaV2Challenge,
        RecaptchaV3Challenge,
        HCaptchaChallenge,
        FunCaptchaChallenge,
        GeeTestV3Challenge,
        GeeTestV4Challenge,
        TurnstileChallenge,
    }
)


def uniform_choice(candidates: Iterable[BaseAdapter]) -> BaseAdapter:
    """Uniform random selection (ADR-0064). Module hook: tests monkeypatch
    this for deterministic provider picks."""
    return random.choice(list(candidates))


def supports_kind(adapter: BaseAdapter, kind_base: type[BaseChallenge]) -> bool:
    """Whether the adapter's ``challenges`` include a subclass of the kind."""
    return any(issubclass(c, kind_base) for c in adapter.challenges)


def concrete_member(
    adapter: BaseAdapter, kind_base: type[BaseChallenge]
) -> type[BaseChallenge]:
    """The unique concrete class in ``challenges`` subclassing the kind."""
    for cls in adapter.challenges:
        if issubclass(cls, kind_base):
            return cls
    raise LookupError(f"{adapter.provider!r} declares no {kind_base.__name__} class")


def _upcast(
    challenge: BaseChallenge, concrete_cls: type[BaseChallenge]
) -> BaseChallenge:
    """Construct the concrete class from the universal fields (ADR-0064)."""
    kwargs = {
        f.name: getattr(challenge, f.name)
        for f in fields(type(challenge))
        if f.name in {g.name for g in fields(concrete_cls)}
    }
    return concrete_cls(**kwargs)


def apply_default_proxy(
    challenge: BaseChallenge, default_proxy: Proxy | None
) -> BaseChallenge:
    """Apply the client-level default proxy when applicable (ADR-0012):
    only proxy-capable concrete challenges (a ``proxy`` field), and only
    when the challenge does not carry its own."""
    if default_proxy is None:
        return challenge
    field_names = {f.name for f in fields(type(challenge))}
    if "proxy" not in field_names:
        _logger.warning(
            "client default proxy ignored: %s carries no proxy field",
            type(challenge).__name__,
        )
        return challenge
    if getattr(challenge, "proxy", None) is not None:
        return challenge  # challenge's own proxy wins
    # The guard above proved the concrete class carries ``proxy``; the cast
    # satisfies strict ``dataclasses.replace`` typing.
    upgraded = replace(cast(Any, challenge), proxy=default_proxy)
    return cast(BaseChallenge, upgraded)


def dispatch(
    registry: Mapping[str, BaseAdapter],
    challenge: BaseChallenge,
    provider: str | None,
    default_proxy: Proxy | None,
    on_pre_flight: Callable[[str | None, ErrorKind | None, str], None] | None = None,
) -> tuple[BaseAdapter, BaseChallenge]:
    """Resolve ``(adapter, prepared_challenge)`` or raise pre-flight.

    - Concrete challenge class -> its adapter; a contradicting
      ``provider=`` raises ``TypeError`` naming both parties.
    - Kind-base instance + ``provider="name"`` -> that adapter
      (unknown -> ``TypeError``; kind unsupported ->
      ``UnsupportedChallengeError``).
    - Kind-base instance + ``provider=None`` -> uniform random choice
      among supporting adapters.

    Before each raise, ``on_pre_flight(provider_hint, error_kind)`` fires
    with the best-known provider string (``None`` when unresolvable); the
    caller turns it into a PRE_FLIGHT_FAILED event.
    """

    def fail(
        provider_hint: str | None, error_kind: ErrorKind | None, message: str
    ) -> NoReturn:
        if on_pre_flight is not None:
            on_pre_flight(provider_hint, error_kind, message)
        if error_kind is not None:
            raise UnsupportedChallengeError(message)
        raise TypeError(message)

    cls = type(challenge)
    if cls in KIND_BASES:
        kind = cls
        if provider is not None:
            adapter = registry.get(provider)
            if adapter is None:
                fail(provider, None, f"provider {provider!r} is not registered")
            if not supports_kind(adapter, kind):
                fail(
                    provider,
                    ErrorKind.UNSUPPORTED_CHALLENGE,
                    f"provider {provider!r} does not support {kind.__name__}",
                )
            concrete = concrete_member(adapter, kind)
            prepared = _upcast(challenge, concrete)
            return adapter, apply_default_proxy(prepared, default_proxy)
        candidates = [a for a in registry.values() if supports_kind(a, kind)]
        if not candidates:
            fail(
                None,
                ErrorKind.UNSUPPORTED_CHALLENGE,
                f"no registered provider supports {kind.__name__}",
            )
        chosen = uniform_choice(candidates)
        concrete = concrete_member(chosen, kind)
        prepared = _upcast(challenge, concrete)
        return chosen, apply_default_proxy(prepared, default_proxy)
    owners = [a for a in registry.values() if cls in a.challenges]
    if not owners:
        fail(None, None, f"challenge {cls.__name__} matches no registered adapter")
    owner = owners[0]
    if provider is not None and provider != owner.provider:
        fail(
            owner.provider,
            None,
            f"challenge {cls.__name__} belongs to provider "
            f"{owner.provider!r}, but provider={provider!r} was requested",
        )
    return owner, apply_default_proxy(challenge, default_proxy)


__all__ = [
    "KIND_BASES",
    "apply_default_proxy",
    "concrete_member",
    "dispatch",
    "supports_kind",
    "uniform_choice",
]
