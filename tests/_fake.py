"""Shared test fakes. Not collected by pytest (filename not test_*)."""

from dataclasses import dataclass

from unicaptcha.solution.base import BaseSolution


@dataclass(frozen=True, slots=True)
class FakeSolution(BaseSolution):
    """Concrete BaseSolution subclass for tests (its repr will be
    token-truncating per policy once solution kinds land, task 6)."""

    text: str = "token1234"
