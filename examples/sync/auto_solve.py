"""Detect and auto-solve the captcha on a page with the 2Captcha provider.

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaAdapter -> AntiCaptchaAdapter / CapMonsterAdapter /
CapsolverAdapter. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import os
import sys

from unicaptcha import Solver, detect
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

# Public 2Captcha demo page (reCAPTCHA v2), as static HTML source.
HTML = (
    '<div class="g-recaptcha" '
    'data-sitekey="6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u"></div>'
)
PAGE_URL = "https://2captcha.com/demo/recaptcha-v2"

if __name__ == "__main__":
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    for found in detect(HTML, PAGE_URL):
        print("detected:", found.kind, found.signals)

    with Solver(adapters=[TwoCaptchaAdapter(api_key)]) as client:
        auto = client.auto_solve(HTML, PAGE_URL)
        print("kind:", auto.detected.kind)
        print("token:", auto.fill["#g-recaptcha-response"])
