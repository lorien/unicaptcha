import unicaptcha


class TestRootExports:
    def test_core_vocabulary_exported(self) -> None:
        expected = {
            "BaseSolution",
            "ErrorKind",
            "InvalidConfigError",
            "NetworkConfig",
            "ParsedTask",
            "Proxy",
            "ProxyKind",
            "RetryConfig",
            "SecretStr",
            "SubmitAccepted",
            "TaskEvent",
            "TaskEventKind",
            "TaskRef",
            "TaskResult",
            "TaskStatus",
            "TaskStatusResult",
            "TaskTicket",
            "TimeConfig",
            "UnicaptchaError",
            "__version__",
        }
        assert expected <= set(unicaptcha.__all__)
        for name in expected:
            assert hasattr(unicaptcha, name), name

    def test_version(self) -> None:
        assert unicaptcha.__version__ == "0.1.0"
