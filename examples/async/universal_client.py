"""Solve an image captcha with the universal multi-provider client (async).

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaAdapter -> AntiCaptchaAdapter / CapMonsterAdapter /
CapsolverAdapter. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import asyncio
import os
import sys
from pathlib import Path

from unicaptcha import AsyncSolver, ImageChallenge
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter


async def main() -> None:
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

    async with AsyncSolver(adapters=[TwoCaptchaAdapter(api_key)]) as client:
        result = await client.solve(ImageChallenge(image))
        print("solved:", result.solution.text)


asyncio.run(main())
