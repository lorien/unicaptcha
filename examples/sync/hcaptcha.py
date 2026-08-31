"""Solve hCaptcha with the 2Captcha provider.

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaClient -> AntiCaptchaClient / CapMonsterClient /
CapsolverClient. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import os
import sys

from unicaptcha.provider.twocaptcha import TwoCaptchaClient

if __name__ == "__main__":
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    # hCaptcha's official always-pass test sitekey.
    sitekey = "10000000-ffff-ffff-ffff-000000000001"
    pageurl = "https://accounts.hcaptcha.com/demo"

    with TwoCaptchaClient(api_key) as client:
        result = client.solve_hcaptcha(sitekey=sitekey, pageurl=pageurl)
        print("token:", result.solution.token)
