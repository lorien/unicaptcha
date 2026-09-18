"""Shared test fixtures (task 15 scaffold)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from _myservice import MyServiceAdapter

from unicaptcha.types import RetryConfig, TimeConfig

_CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"
_RELEASED_SECTION = re.compile(r"^## \[(\d+\.\d+\.\d+)\]", re.MULTILINE)


@pytest.fixture
def myservice_adapter() -> MyServiceAdapter:
    return MyServiceAdapter("test-key")


@pytest.fixture
def fast_time() -> TimeConfig:
    return TimeConfig(poll_delay=0.0, poll_interval=0.01, total_timeout=1.0)


@pytest.fixture
def fast_retry() -> RetryConfig:
    return RetryConfig(max_attempts=2, backoff_base=0.001, backoff_cap=0.001)


@pytest.fixture
def released_version() -> str:
    """Newest released ``## [x.y.z]`` version in CHANGELOG.md.

    Keeps the version-pin tests in sync with the release commit instead of
    hardcoding a literal that must be edited on every bump.
    """
    match = _RELEASED_SECTION.search(_CHANGELOG.read_text(encoding="utf-8"))
    if match is None:
        raise AssertionError("CHANGELOG.md has no released [x.y.z] section")
    return match.group(1)
