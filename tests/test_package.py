import importlib

import pytest

import unicaptcha
from unicaptcha import AntiCaptchaCompatAdapterBase
from unicaptcha.provider.anticaptcha.adapter import AntiCaptchaAdapter
from unicaptcha.provider.capmonster.adapter import CapMonsterAdapter
from unicaptcha.provider.capsolver.adapter import CapsolverAdapter
from unicaptcha.provider.twocaptcha.adapter import TwoCaptchaAdapter

SUBPACKAGES = [
    "unicaptcha.challenge",
    "unicaptcha.solution",
    "unicaptcha._internal",
    "unicaptcha.provider",
    "unicaptcha.provider.twocaptcha",
    "unicaptcha.provider.anticaptcha",
    "unicaptcha.provider.capmonster",
    "unicaptcha.provider.capsolver",
]


def test_version() -> None:
    assert unicaptcha.__version__ == "0.1.0"


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackages_importable(name: str) -> None:
    importlib.import_module(name)


def test_compat_adapters_share_the_compat_family_base() -> None:
    for adapter in (
        TwoCaptchaAdapter,
        AntiCaptchaAdapter,
        CapMonsterAdapter,
        CapsolverAdapter,
    ):
        assert issubclass(adapter, AntiCaptchaCompatAdapterBase)


def test_compat_adapter_base_is_abstract() -> None:
    with pytest.raises(TypeError):
        AntiCaptchaCompatAdapterBase("key")  # type: ignore[abstract]
