"""Currency-aware costs tests: Money type and adapter currency resolution."""

from __future__ import annotations

from decimal import Decimal

import pytest

from unicaptcha import Money
from unicaptcha.provider.anticaptcha import AntiCaptchaAdapter
from unicaptcha.provider.capmonster import CapMonsterAdapter
from unicaptcha.provider.capsolver import CapsolverAdapter
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter


class TestMoney:
    def test_equality_and_repr(self) -> None:
        assert Money(Decimal("0.00025"), "USD") == Money(Decimal("0.00025"), "USD")
        assert Money(Decimal("0.00025"), "USD") != Money(Decimal("0.00025"), "RUB")
        assert repr(Money(Decimal("7.5"), "USD")) == "Money(7.5, 'USD')"

    def test_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        money = Money(Decimal("1"), "USD")
        with pytest.raises(FrozenInstanceError):
            money.amount = Decimal("2")  # type: ignore[misc]

    def test_amount_and_currency_fields(self) -> None:
        money = Money(Decimal("0.002"), "RUB")
        assert money.amount == Decimal("0.002")
        assert money.currency == "RUB"


class TestAdapterCurrency:
    def test_twocaptcha_defaults_to_usd(self) -> None:
        assert TwoCaptchaAdapter("key").currency == "USD"

    def test_rucaptcha_host_defaults_to_rub(self) -> None:
        adapter = TwoCaptchaAdapter("key", base_url="https://api.rucaptcha.com")
        assert adapter.currency == "RUB"

    def test_explicit_currency_overrides_host(self) -> None:
        adapter = TwoCaptchaAdapter(
            "key", base_url="https://api.rucaptcha.com", currency="USD"
        )
        assert adapter.currency == "USD"

    def test_other_providers_default_to_usd(self) -> None:
        assert AntiCaptchaAdapter("key").currency == "USD"
        assert CapMonsterAdapter("key").currency == "USD"
        assert CapsolverAdapter("key").currency == "USD"

    def test_unknown_mirror_host_falls_through_to_usd(self) -> None:
        adapter = TwoCaptchaAdapter("key", base_url="https://example-mirror.com")
        assert adapter.currency == "USD"

    def test_currency_is_per_instance(self) -> None:
        usd = TwoCaptchaAdapter("key")
        rub = TwoCaptchaAdapter("key", base_url="https://api.rucaptcha.com")
        assert (usd.currency, rub.currency) == ("USD", "RUB")
