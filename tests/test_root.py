import unicaptcha


class TestRootExports:
    def test_core_vocabulary_exported(self) -> None:
        expected = {
            "AuthenticationError",
            "BaseAdapter",
            "BaseChallenge",
            "BaseSolution",
            "ClientClosedError",
            "EmptySolutionError",
            "Endpoints",
            "ErrorKind",
            "FunCaptchaChallenge",
            "FunCaptchaSolution",
            "GeeTestV3Challenge",
            "GeeTestV3Solution",
            "GeeTestV4Challenge",
            "GeeTestV4Solution",
            "HCaptchaChallenge",
            "HCaptchaSolution",
            "ImageChallenge",
            "ImageSolution",
            "InsufficientBalanceError",
            "InvalidChallengeError",
            "InvalidConfigError",
            "NetworkConfig",
            "NetworkError",
            "NoSolutionError",
            "ParsedTask",
            "ProviderError",
            "Proxy",
            "ProxyKind",
            "RateLimitError",
            "RecaptchaV2Challenge",
            "RecaptchaV2Solution",
            "RecaptchaV3Challenge",
            "RecaptchaV3Solution",
            "RetryConfig",
            "SecretStr",
            "ServiceBusyError",
            "SubmitAccepted",
            "TaskEvent",
            "TaskEventKind",
            "TaskRef",
            "TaskResult",
            "TaskStatus",
            "TaskStatusResult",
            "TaskTimeoutError",
            "TaskTicket",
            "TextChallenge",
            "TextSolution",
            "TimeConfig",
            "TurnstileChallenge",
            "TurnstileSolution",
            "UnicaptchaError",
            "UnsupportedChallengeError",
            "__version__",
        }
        assert expected <= set(unicaptcha.__all__)
        for name in expected:
            assert hasattr(unicaptcha, name), name

    def test_version(self) -> None:
        assert unicaptcha.__version__ == "0.1.0"
