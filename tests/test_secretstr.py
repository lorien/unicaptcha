import pickle

import pytest

from unicaptcha import SecretStr


class TestSecretStr:
    def test_masked_repr_and_str(self) -> None:
        s = SecretStr("super-secret-key")
        assert repr(s) == "***"
        assert str(s) == "***"
        assert "super-secret-key" not in repr(s)
        assert "super-secret-key" not in str(s)

    def test_get_secret_value(self) -> None:
        assert SecretStr("abc").get_secret_value() == "abc"

    def test_value_equality(self) -> None:
        assert SecretStr("abc") == SecretStr("abc")
        assert SecretStr("abc") != SecretStr("abd")

    def test_compare_to_str_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            SecretStr("abc") == "abc"  # noqa: B015
        with pytest.raises(TypeError):
            "abc" == SecretStr("abc")  # noqa: B015, SIM300
        with pytest.raises(TypeError):
            SecretStr("abc") != "abc"  # noqa: B015

    def test_compare_to_none_is_false(self) -> None:
        assert (SecretStr("abc") == None) is False  # noqa: E711
        assert (SecretStr("abc") != None) is True  # noqa: E711

    def test_hash_is_hash_of_value(self) -> None:
        assert hash(SecretStr("abc")) == hash("abc")
        assert hash(SecretStr("abc")) == hash(SecretStr("abc"))

    def test_hashable_in_set(self) -> None:
        s = {SecretStr("a"), SecretStr("a"), SecretStr("b")}
        assert len(s) == 2

    def test_pickle_round_trip(self) -> None:
        s = SecretStr("round-trip-me")
        restored = pickle.loads(pickle.dumps(s))
        assert restored == s
        assert restored.get_secret_value() == "round-trip-me"
        assert repr(restored) == "***"
