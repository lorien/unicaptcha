"""Route solving through a proxy on the challenge (async).

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap AsyncTwoCaptchaClient -> AsyncAntiCaptchaClient /
AsyncCapMonsterClient / AsyncCapsolverClient. Per-provider extras for a
given kind are documented in the challenge-class docstrings and
spec/docs/architecture.md §2.
"""

import asyncio
import os
import sys
from pathlib import Path

from unicaptcha.provider.twocaptcha import AsyncTwoCaptchaClient
from unicaptcha.types import Proxy, ProxyKind


async def main() -> None:
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    proxy = Proxy(
        host="203.0.113.1",
        port=8080,
        kind=ProxyKind.HTTP,
        username="user",
        password="pass",
    )

    image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

    async with AsyncTwoCaptchaClient(api_key) as client:
        # Per-challenge proxy: workers visit the target through it.
        result = await client.solve_image(image, proxy=proxy)
        print("solved:", result.solution.text)

        # A client-level default also exists:
        # AsyncTwoCaptchaClient(api_key, proxy=proxy).


asyncio.run(main())
