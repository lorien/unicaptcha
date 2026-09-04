"""Drift guards over the shared error-kind tables (tests/_error_kinds.py).

If an adapter's ``error_kinds`` diverges from the shared table, or maps a
kind the events layer cannot represent, these tests fail loudly.
"""

import pytest
from _error_kinds import PROVIDER_ERROR_KINDS, TERMINAL_ERROR_KINDS

from unicaptcha import TaskEventKind
from unicaptcha.provider.anticaptcha.adapter import AntiCaptchaAdapter
from unicaptcha.provider.capmonster.adapter import CapMonsterAdapter
from unicaptcha.provider.capsolver.adapter import CapsolverAdapter
from unicaptcha.provider.twocaptcha.adapter import TwoCaptchaAdapter

ADAPTERS = [
    TwoCaptchaAdapter,
    AntiCaptchaAdapter,
    CapMonsterAdapter,
    CapsolverAdapter,
]


@pytest.mark.parametrize("adapter_cls", ADAPTERS)
def test_adapter_error_kinds_match_shared_table(adapter_cls) -> None:
    assert adapter_cls.error_kinds == PROVIDER_ERROR_KINDS[adapter_cls.provider]


def test_mapped_kinds_are_valid_terminal_event_kinds() -> None:
    submit_failed = TERMINAL_ERROR_KINDS[TaskEventKind.SUBMIT_FAILED]
    for table in PROVIDER_ERROR_KINDS.values():
        for kind in table.values():
            assert kind in submit_failed
