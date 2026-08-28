"""Two-phase batch solving: submit now, collect later.

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaClient -> AntiCaptchaClient / CapMonsterClient /
CapsolverClient. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import os
import sys
from pathlib import Path

from unicaptcha.provider.twocaptcha import TwoCaptchaClient, TwoCaptchaImageChallenge

api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
if not api_key:
    sys.exit(
        "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
        "(https://2captcha.com/setting/devcenter)"
    )

image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

with TwoCaptchaClient(api_key) as client:
    # submit() returns immediately with a TaskTicket; solving continues in
    # the background of the engine.
    ticket = client.submit(TwoCaptchaImageChallenge(image))
    print("submitted task", ticket.task_ref.task_id)

    result = client.wait(ticket)
    print("solved:", result.solution.text)
