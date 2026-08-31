"""Solve an image captcha with the universal multi-provider client.

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaAdapter -> AntiCaptchaAdapter / CapMonsterAdapter /
CapsolverAdapter. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import os
import sys
from pathlib import Path

from unicaptcha import ImageChallenge, Solver
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

if __name__ == "__main__":
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    client = Solver(adapters=[TwoCaptchaAdapter(api_key)])

    # Any path or bytes works; the value is normalized to bytes at construction.
    image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

    result = client.solve(ImageChallenge(image))
    print("solved:", result.solution.text)
    print("task id:", result.task_id, "cost:", result.cost)

    client.close()
