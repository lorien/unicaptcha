"""Solved-value → DOM selector mapping for auto-solve (ADR-0077).

Each detectable kind has a conventional place where the page expects the
solved value. ``build_fill`` maps a solved solution object to that
field's selector. GeeTest v4 field names follow the official
integration convention (``geetest_<solution key>`` hidden inputs,
verified against the GeeTest v4 docs during implementation).

FunCaptcha has no standard injectable field: the token is handed to the
page's Arkose callback by the caller, so its map is empty.
"""

from __future__ import annotations

from collections.abc import Mapping

from unicaptcha.solution.base import BaseSolution
from unicaptcha.solution.funcaptcha import FunCaptchaSolution
from unicaptcha.solution.geetest import GeeTestV3Solution, GeeTestV4Solution
from unicaptcha.solution.hcaptcha import HCaptchaSolution
from unicaptcha.solution.recaptcha_v2 import RecaptchaV2Solution
from unicaptcha.solution.recaptcha_v3 import RecaptchaV3Solution
from unicaptcha.solution.turnstile import TurnstileSolution

__all__ = ["build_fill"]


def build_fill(solution: BaseSolution) -> Mapping[str, str]:
    """Return the DOM selector → value map for a solved solution.

    Kinds without a standard injectable field (FunCaptcha) — or an
    unrecognized solution type — produce an empty map.
    """
    if isinstance(solution, (RecaptchaV2Solution, RecaptchaV3Solution)):
        return {"#g-recaptcha-response": solution.token}
    if isinstance(solution, HCaptchaSolution):
        return {"textarea[name=h-captcha-response]": solution.token}
    if isinstance(solution, TurnstileSolution):
        return {"input[name=cf-turnstile-response]": solution.token}
    if isinstance(solution, FunCaptchaSolution):
        return {}
    if isinstance(solution, GeeTestV3Solution):
        return {
            "#geetest_challenge": solution.challenge,
            "#geetest_validate": solution.validate,
            "#geetest_seccode": solution.seccode,
        }
    if isinstance(solution, GeeTestV4Solution):
        return {
            "#geetest_lot_number": solution.lot_number,
            "#geetest_pass_token": solution.pass_token,
            "#geetest_gen_time": solution.gen_time,
            "#geetest_captcha_output": solution.captcha_output,
        }
    return {}
