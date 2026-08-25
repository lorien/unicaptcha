import pytest

from unicaptcha import InvalidConfigError, NetworkConfig, RetryConfig, TimeConfig
from unicaptcha._internal.config import merge_configs


class TestNetworkConfig:
    def test_all_none_defaults(self) -> None:
        c = NetworkConfig()
        assert c.timeout is None
        assert c.max_connections is None
        assert c.max_keepalive_connections is None

    def test_valid_values(self) -> None:
        c = NetworkConfig(timeout=20, max_connections=10, max_keepalive_connections=5)
        assert c.timeout == 20

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"timeout": 0}, "timeout"),
            ({"timeout": -1}, "timeout"),
            ({"max_connections": 0}, "max_connections"),
            ({"max_keepalive_connections": -3}, "max_keepalive_connections"),
        ],
    )
    def test_bad_values_raise(self, kwargs: dict[str, object], message: str) -> None:
        with pytest.raises(InvalidConfigError, match=message):
            NetworkConfig(**kwargs)


class TestTimeConfig:
    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"total_timeout": 0}, "total_timeout"),
            ({"poll_interval": -5}, "poll_interval"),
            ({"poll_delay": -1}, "poll_delay"),
        ],
    )
    def test_bad_values_raise(self, kwargs: dict[str, object], message: str) -> None:
        with pytest.raises(InvalidConfigError, match=message):
            TimeConfig(**kwargs)

    def test_zero_poll_delay_is_valid(self) -> None:
        assert TimeConfig(poll_delay=0).poll_delay == 0


class TestRetryConfig:
    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"max_attempts": 0}, "max_attempts"),
            ({"backoff_base": -1}, "backoff_base"),
            ({"backoff_cap": 0}, "backoff_cap"),
            ({"backoff_base": 2.0, "backoff_cap": 1.0}, "backoff_cap"),
        ],
    )
    def test_bad_values_raise(self, kwargs: dict[str, object], message: str) -> None:
        with pytest.raises(InvalidConfigError, match=message):
            RetryConfig(**kwargs)

    def test_cap_equal_to_base_is_valid(self) -> None:
        assert RetryConfig(backoff_base=1.0, backoff_cap=1.0).backoff_cap == 1.0


class TestMergeConfigs:
    def test_override_wins_fieldwise(self) -> None:
        base = TimeConfig(total_timeout=120, poll_interval=3)
        override = TimeConfig(total_timeout=60)
        merged = merge_configs(base, override)
        assert merged.total_timeout == 60
        assert merged.poll_interval == 3
        assert merged.poll_delay is None

    def test_override_with_none_only_keeps_base(self) -> None:
        base = RetryConfig(max_attempts=3, backoff_base=1.0, backoff_cap=30.0)
        merged = merge_configs(base, RetryConfig())
        assert merged == base

    def test_does_not_mutate_base(self) -> None:
        base = NetworkConfig(timeout=20, max_connections=10)
        merge_configs(base, NetworkConfig(timeout=30))
        assert base.timeout == 20

    def test_all_fields_overridden(self) -> None:
        base = TimeConfig(total_timeout=120, poll_interval=3, poll_delay=1)
        override = TimeConfig(total_timeout=60, poll_interval=5, poll_delay=2)
        assert merge_configs(base, override) == override
