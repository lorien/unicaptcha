"""HTML captcha detection and the auto-solve result (ADR-0077).

``detect(html, pageurl)`` parses a page's source with the stdlib-only
scanner in ``unicaptcha._internal._html`` and returns the captchas it
finds as ready-to-solve kind-base challenges (DOM order). ``Solver`` /
``AsyncSolver`` expose ``auto_solve`` which detects, solves the first
match via the existing dispatch (ADR-0064), and wraps the outcome in an
``AutoSolveResult`` whose ``fill`` map tells the caller which DOM field
each solved value belongs to.

Image/text captchas are API-driven, not HTML-detectable, and are out of
scope; FunCaptcha has no standard injectable field and yields an empty
``fill`` (the token is delivered via the page's Arkose callback).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from unicaptcha._internal._html import Signal, scan
from unicaptcha._internal.repr import truncate_token
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.challenge.funcaptcha import FunCaptchaChallenge
from unicaptcha.challenge.geetest import GeeTestV3Challenge, GeeTestV4Challenge
from unicaptcha.challenge.hcaptcha import HCaptchaChallenge
from unicaptcha.challenge.recaptcha_v2 import RecaptchaV2Challenge
from unicaptcha.challenge.recaptcha_v3 import RecaptchaV3Challenge
from unicaptcha.challenge.turnstile import TurnstileChallenge
from unicaptcha.errors import InvalidChallengeError
from unicaptcha.solution.base import BaseSolution
from unicaptcha.types import TaskResult

__all__ = ["AutoSolveResult", "DetectedChallenge", "detect"]


@dataclass(frozen=True, slots=True)
class DetectedChallenge:
    """A captcha found in a page's HTML.

    ``challenge`` is a kind-base challenge ready to pass to
    ``Solver.solve`` / ``AsyncSolver.solve``; ``signals`` is the
    human-readable evidence that led to the detection.
    """

    kind: str
    challenge: BaseChallenge
    page: str
    signals: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AutoSolveResult:
    """Outcome of an ``auto_solve`` call.

    ``result`` is the typed solve result; ``fill`` maps DOM selectors to
    the solved values for the caller to inject into the live page (no
    browser built in). ``detected`` records what was solved and why.
    """

    detected: DetectedChallenge
    result: TaskResult[BaseSolution]
    fill: Mapping[str, str]

    def __repr__(self) -> str:
        fill = ", ".join(
            f"{selector}: {truncate_token(value)}"
            for selector, value in self.fill.items()
        )
        return (
            f"{type(self).__name__}(detected={self.detected!r}, "
            f"result={self.result!r}, fill={{{fill}}})"
        )


def _build_challenge(signal: Signal, pageurl: str) -> BaseChallenge | None:
    fields = signal.fields
    kind = signal.kind
    if kind == "recaptcha-v2":
        sitekey = fields.get("sitekey")
        if not sitekey:
            return None
        return RecaptchaV2Challenge(
            sitekey=sitekey,
            pageurl=pageurl,
            invisible=fields.get("invisible") == "1",
        )
    if kind == "recaptcha-v3":
        sitekey = fields.get("sitekey")
        if not sitekey:
            return None
        return RecaptchaV3Challenge(
            sitekey=sitekey,
            pageurl=pageurl,
            action=fields.get("action"),
        )
    if kind == "hcaptcha":
        sitekey = fields.get("sitekey")
        if not sitekey:
            return None
        return HCaptchaChallenge(
            sitekey=sitekey,
            pageurl=pageurl,
            is_invisible=fields.get("is_invisible") == "1",
            rqdata=fields.get("rqdata"),
        )
    if kind == "turnstile":
        sitekey = fields.get("sitekey")
        if not sitekey:
            return None
        return TurnstileChallenge(
            sitekey=sitekey,
            pageurl=pageurl,
            action=fields.get("action"),
            c_data=fields.get("c_data"),
            chl_page_data=fields.get("chl_page_data"),
        )
    if kind == "funcaptcha":
        public_key = fields.get("public_key")
        if not public_key:
            return None
        return FunCaptchaChallenge(public_key=public_key, pageurl=pageurl)
    if kind == "geetest-v3":
        gt_key = fields.get("gt_key")
        challenge = fields.get("challenge")
        if not gt_key or not challenge:
            return None
        return GeeTestV3Challenge(gt_key=gt_key, challenge=challenge, pageurl=pageurl)
    if kind == "geetest-v4":
        captcha_id = fields.get("captcha_id")
        if not captcha_id:
            return None
        return GeeTestV4Challenge(captcha_id=captcha_id, pageurl=pageurl)
    return None


def detect(html: str, pageurl: str) -> tuple[DetectedChallenge, ...]:
    """Detect the captchas present in a page's HTML source.

    Returns kind-base challenges in document order; an empty tuple when
    no supported captcha is found. ``pageurl`` is required — the solved
    token is bound to that domain.
    """
    if not isinstance(html, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(f"html must be str, got {type(html).__name__}")
    if not pageurl:
        raise InvalidChallengeError("pageurl must be a non-empty string")
    out: list[DetectedChallenge] = []
    for signal in scan(html):
        challenge = _build_challenge(signal, pageurl)
        if challenge is not None:
            out.append(
                DetectedChallenge(
                    kind=signal.kind,
                    challenge=challenge,
                    page=pageurl,
                    signals=(signal.evidence,),
                )
            )
    return tuple(out)
