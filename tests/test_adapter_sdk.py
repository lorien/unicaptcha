import ast
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar

import pytest
from _fake import StubAdapter

from unicaptcha import (
    BaseAdapter,
    Endpoints,
    ImageChallenge,
    SecretStr,
    UnsupportedChallengeError,
)
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import ErrorKind
from unicaptcha.types import ParsedTask, SubmitAccepted, TaskRef, TaskStatus


class MinimalAdapter(BaseAdapter):
    """Minimal complete adapter asserting the base report defaults
    (reports off / raising)."""

    provider: ClassVar[str] = "myservice"
    challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset()
    default_base_url: ClassVar[str] = "https://myservice.example"

    def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
        return {}

    def parse_submit_response(self, raw: bytes) -> SubmitAccepted:
        return SubmitAccepted(task_id=1)

    def parse_task_status(self, raw: bytes) -> ParsedTask:
        return ParsedTask(state=TaskStatus.PENDING, solution=None, cost=None, raw=raw)

    def parse_balance(self, raw: bytes) -> Decimal:
        return Decimal("0")

    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]:
        return ErrorKind.PROVIDER, "provider error"


class TestEndpoints:
    def test_fields_required(self) -> None:
        with pytest.raises(TypeError):
            Endpoints(  # type: ignore[call-arg]
                submit="/a", get_task_status="/b", get_balance="/c"
            )

    def test_frozen(self) -> None:
        e = Endpoints("/a", "/b", "/c", "/d", "/e")
        with pytest.raises(FrozenInstanceError):
            e.submit = "/z"  # type: ignore[misc]

    def test_json_family_default_on_base(self) -> None:
        assert BaseAdapter.endpoints == Endpoints(
            submit="/createTask",
            get_task_status="/getTaskResult",
            get_balance="/getBalance",
            report_good_result="/reportCorrect",
            report_bad_result="/reportIncorrect",
        )


class TestBaseAdapterABC:
    def test_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            BaseAdapter("key")  # type: ignore[abstract]

    def test_subclass_missing_abstract_method_fails(self) -> None:
        class _Incomplete(BaseAdapter):
            provider: ClassVar[str] = "x"
            challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset()
            default_base_url: ClassVar[str] = "https://x"

            def build_payload(self, challenge: BaseChallenge) -> dict[str, Any]:
                return {}

        with pytest.raises(TypeError):
            _Incomplete("key")  # type: ignore[abstract]


class TestInitSubclass:
    def test_missing_provider(self) -> None:
        with pytest.raises(TypeError, match="provider"):

            class _NoProvider(BaseAdapter):
                challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset()
                default_base_url: ClassVar[str] = "https://x"

    def test_missing_challenges(self) -> None:
        with pytest.raises(TypeError, match="challenges"):

            class _NoChallenges(BaseAdapter):
                provider: ClassVar[str] = "x"
                default_base_url: ClassVar[str] = "https://x"

    def test_missing_default_base_url(self) -> None:
        with pytest.raises(TypeError, match="default_base_url"):

            class _NoBaseUrl(BaseAdapter):
                provider: ClassVar[str] = "x"
                challenges: ClassVar[frozenset[type[BaseChallenge]]] = frozenset()

    def test_complete_subclass_accepted(self) -> None:
        assert StubAdapter("key").provider == "myservice"


class TestConstructor:
    def test_plain_str_wrapped(self) -> None:
        a = StubAdapter("plain-key")
        assert isinstance(a._api_key, SecretStr)
        assert a._api_key.get_secret_value() == "plain-key"

    def test_secret_str_passthrough(self) -> None:
        key = SecretStr("already-secret")
        a = StubAdapter(key)
        assert a._api_key is key

    def test_base_url_defaults(self) -> None:
        assert StubAdapter("key").base_url == "https://myservice.example"

    def test_base_url_override(self) -> None:
        a = StubAdapter("key", base_url="https://mirror.example")
        assert a.base_url == "https://mirror.example"

    def test_referral_default_true(self) -> None:
        assert StubAdapter("key")._referral is True

    def test_referral_explicit(self) -> None:
        assert StubAdapter("key", referral=False)._referral is False
        assert StubAdapter("key", referral="4704")._referral == "4704"

    def test_referral_is_keyword_only(self) -> None:
        with pytest.raises(TypeError):
            StubAdapter("key", "https://x", False)  # type: ignore[call-arg]


class TestRepr:
    def test_key_masked(self) -> None:
        a = StubAdapter("super-secret-key")
        assert repr(a) == "StubAdapter(api_key=***)"
        assert "super-secret-key" not in repr(a)
        assert str(a) == repr(a)


class TestReportDefaults:
    def test_supported_false(self) -> None:
        a = MinimalAdapter("key")
        assert a.report_bad_supported(ImageChallenge) is False
        assert a.report_good_supported(ImageChallenge) is False

    def test_build_and_parse_raise(self) -> None:
        a = MinimalAdapter("key")
        ref = TaskRef(provider="myservice", task_id=1)
        with pytest.raises(UnsupportedChallengeError):
            a.build_report_bad(ref)
        with pytest.raises(UnsupportedChallengeError):
            a.parse_report_bad(b"{}")
        with pytest.raises(UnsupportedChallengeError):
            a.build_report_good(ref)
        with pytest.raises(UnsupportedChallengeError):
            a.parse_report_good(b"{}")


class TestRequestBuilders:
    def test_build_task_status_default(self) -> None:
        assert StubAdapter("key").build_task_status(5) == {
            "clientKey": "key",
            "taskId": 5,
        }

    def test_build_balance_default(self) -> None:
        assert StubAdapter("key").build_balance() == {"clientKey": "key"}


class TestAdapterSdkIsolation:
    def test_sdk_module_has_no_internal_imports(self) -> None:
        root = Path(__file__).resolve().parent.parent
        path = root / "unicaptcha" / "adapter.py"
        tree = ast.parse(path.read_text())

        offenders: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (
                node.module == "unicaptcha._internal"
                or (
                    node.module is not None
                    and node.module.startswith("unicaptcha._internal.")
                )
            ):
                offenders.append(f"from {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("unicaptcha._internal"):
                        offenders.append(f"import {alias.name}")
        assert not offenders, offenders
