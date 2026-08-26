"""Image challenge kind base (ADR-0048, ADR-0064, ADR-0065)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, cast

from unicaptcha._internal.repr import stub_bytes
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.image import ImageSolution


@dataclass(frozen=True, slots=True)
class ImageChallenge(BaseChallenge):
    """An image captcha. ``body`` is ``bytes | Path`` and always stores
    ``bytes`` (a ``Path`` is read at construction, ADR-0065)."""

    body: bytes | Path
    solution_type: ClassVar[type[BaseSolution]] = ImageSolution

    def __post_init__(self) -> None:
        path = self.body
        body: bytes | Path = path
        if isinstance(path, Path):
            try:
                body = path.read_bytes()
            except OSError as exc:
                raise InvalidChallengeError(
                    f"failed to read image body from {path}: {exc}"
                ) from exc
        object.__setattr__(self, "body", body)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(body={stub_bytes(cast(bytes, self.body))})"

    __str__ = __repr__


__all__ = ["ImageChallenge"]
