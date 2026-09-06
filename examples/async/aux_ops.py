"""Auxiliary operations: balance, task status, good/bad reports (async).

Money values carry their currency: `get_balance()` returns a `Money`,
and the facade forwards a `currency=` override (the default follows the
`base_url` host — `api.rucaptcha.com` bills in RUB, everything else
USD).

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
        balance = await client.get_balance()
        print("balance:", balance)
        print("balance amount:", balance.amount, "currency:", balance.currency)

        ticket = await client.submit(TwoCaptchaImageChallenge(image))
        status = await client.get_task_status(ticket.task_ref)
        print("status:", status.status)

        result = await client.wait(ticket)
        print("solved:", result.solution.text)
        print("cost:", result.cost)

        if await client.report_good_result(result.task_ref):
            print("reported good")


if __name__ == "__main__":
    asyncio.run(main())
