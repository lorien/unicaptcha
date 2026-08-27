"""Shared test fixtures (task 15 scaffold)."""

from __future__ import annotations

import pytest
from _myservice import MyServiceAdapter

from unicaptcha.types import RetryConfig, TimeConfig


@pytest.fixture
def myservice_adapter() -> MyServiceAdapter:
    return MyServiceAdapter("test-key")


@pytest.fixture
def fast_time() -> TimeConfig:
    return TimeConfig(poll_delay=0.0, poll_interval=0.01, total_timeout=1.0)


@pytest.fixture
def fast_retry() -> RetryConfig:
    return RetryConfig(max_attempts=2, backoff_base=0.001, backoff_cap=0.001)
