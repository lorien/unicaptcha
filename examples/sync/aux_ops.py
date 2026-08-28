"""Auxiliary operations: balance, task status, good/bad reports.

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
    print("balance:", client.get_balance())

    ticket = client.submit(TwoCaptchaImageChallenge(image))
    status = client.get_task_status(ticket.task_ref)
    print("status:", status.status)

    result = client.wait(ticket)
    print("solved:", result.solution.text)

    if client.report_good_result(result.task_ref):
        print("reported good")
