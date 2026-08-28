"""Solve a text captcha (a plain question) with 2Captcha (async).

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

    # Sample question from the 2Captcha text-captcha demo page.
    question = "If tomorrow is Saturday, what day is today?"

    async with AsyncTwoCaptchaClient(api_key) as client:
        result = await client.solve_text(question)
        print("solved:", result.solution.text)


asyncio.run(main())
