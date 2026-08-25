import importlib

import pytest

import unicaptcha

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
