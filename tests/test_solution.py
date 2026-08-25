import pytest
from _fake import FakeSolution

from unicaptcha import BaseSolution


class TestBaseSolution:
    def test_not_directly_instantiable(self) -> None:
        with pytest.raises(TypeError):
            BaseSolution()

    def test_subclass_instantiable(self) -> None:
        assert isinstance(FakeSolution(), BaseSolution)
