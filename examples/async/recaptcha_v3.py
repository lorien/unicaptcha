"""Solve reCAPTCHA v3 (score-based) with the 2Captcha provider (async).

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

    # Public demo page from 2captcha.com.
    sitekey = "6LfB5_IbAAAAAMCtsjEHEHKqcB9iQocwwxTiihJu"
    pageurl = "https://2captcha.com/demo/recaptcha-v3"

    async with AsyncTwoCaptchaClient(api_key) as client:
        result = await client.solve_recaptcha_v3(
            sitekey=sitekey,
            pageurl=pageurl,
            action="demo_action",
            min_score=0.9,
        )
        print("token:", result.solution.token, "score:", result.solution.score)


if __name__ == "__main__":
    asyncio.run(main())
