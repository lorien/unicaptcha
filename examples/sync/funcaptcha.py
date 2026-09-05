"""Solve FunCaptcha (Arkose Labs) with the 2Captcha provider.

Illustrative: Arkose's public demo blob is not worker-solvable, so a
live solve is expected to end in ``NoSolutionError``.

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

    # Arkose Labs' public demo public-key (as used in 2Captcha's own examples).
    public_key = "69A21A01-CC7B-B9C6-0F9A-E7FA06677FFC"
    pageurl = "https://client-api.arkoselabs.com"

    with TwoCaptchaClient(api_key) as client:
        result = client.solve_funcaptcha(public_key=public_key, pageurl=pageurl)
        print("token:", result.solution.token)
