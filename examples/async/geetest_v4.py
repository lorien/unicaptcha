"""Solve GeeTest v4 with the 2Captcha provider (async).

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap AsyncTwoCaptchaClient -> AsyncAntiCaptchaClient /
AsyncCapMonsterClient / AsyncCapsolverClient. Per-provider extras for a
given kind are documented in the challenge-class docstrings and
spec/docs/architecture.md §2.
"""

import asyncio
import os
import sys

from unicaptcha.provider.twocaptcha import AsyncTwoCaptchaClient


async def main() -> None:
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    # Public demo values from the 2Captcha GeeTest v4 demo page.
    captcha_id = "e392e1d7fd421dc63325744d5a2b9c73"
    pageurl = "https://2captcha.com/demo/geetest-v4"

    async with AsyncTwoCaptchaClient(api_key) as client:
        result = await client.solve_geetest_v4(captcha_id=captcha_id, pageurl=pageurl)
        print("captcha_output:", result.solution.captcha_output)


asyncio.run(main())
