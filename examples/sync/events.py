"""Observe the task lifecycle via on_event.

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaClient -> AntiCaptchaClient / CapMonsterClient /
CapsolverClient. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import os
import sys
from pathlib import Path

from unicaptcha.events import TaskEvent
from unicaptcha.provider.twocaptcha import TwoCaptchaClient

api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
if not api_key:
    sys.exit(
        "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
        "(https://2captcha.com/setting/devcenter)"
    )


def on_event(event: TaskEvent) -> None:
    print(f"{event.kind.value:>18}  attempt={event.attempt}  {event.detail or ''}")


image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

with TwoCaptchaClient(api_key, on_event=on_event) as client:
    result = client.solve_image(image)
    print("solved:", result.solution.text)
