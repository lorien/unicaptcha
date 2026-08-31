"""Solve GeeTest v3 with the 2Captcha provider (async).

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

    # Public demo values from 2captcha.com/demo/geetest. `challenge` is
    # dynamic: fetch a fresh one per request (the demo page serves one).
    gt_key = "f3bf6dbdcf7886856696502e1d55e00c"
    challenge = "12345678abc90123d45678ef90123a456b"
    pageurl = "https://2captcha.com/demo/geetest"
    api_server = "api.geetest.com"

    async with AsyncTwoCaptchaClient(api_key) as client:
        result = await client.solve_geetest_v3(
            gt_key=gt_key,
            challenge=challenge,
            pageurl=pageurl,
            api_server=api_server,
        )
        print(
            "challenge:",
            result.solution.challenge,
            "validate:",
            result.solution.validate,
            "seccode:",
            result.solution.seccode,
        )


if __name__ == "__main__":
    asyncio.run(main())
