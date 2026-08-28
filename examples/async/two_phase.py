"""Two-phase batch solving: submit now, collect later (async).

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

from unicaptcha.provider.twocaptcha import (
    AsyncTwoCaptchaClient,
    TwoCaptchaImageChallenge,
)


async def main() -> None:
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

    async with AsyncTwoCaptchaClient(api_key) as client:
        # submit() returns immediately with a TaskTicket; solving continues
        # in the background of the engine.
        ticket = await client.submit(TwoCaptchaImageChallenge(image))
        print("submitted task", ticket.task_ref.task_id)

        result = await client.wait(ticket)
        print("solved:", result.solution.text)


asyncio.run(main())
