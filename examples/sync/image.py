"""Solve an image captcha with the 2Captcha provider facade.

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaClient -> AntiCaptchaClient / CapMonsterClient /
CapsolverClient. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import os
import sys
from pathlib import Path

from unicaptcha.provider.twocaptcha import TwoCaptchaClient

if __name__ == "__main__":
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    # Demo image from the 2Captcha normal-captcha demo page.
    image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

    with TwoCaptchaClient(api_key) as client:
        result = client.solve_image(image)
        print("solved:", result.solution.text)
        print("task id:", result.task_id, "cost:", result.cost)
