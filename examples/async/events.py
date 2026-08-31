"""Observe the task lifecycle via on_event (async).

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

from unicaptcha.events import TaskEvent
from unicaptcha.provider.twocaptcha import AsyncTwoCaptchaClient


async def on_event(event: TaskEvent) -> None:
    print(f"{event.kind.value:>18}  attempt={event.attempt}  {event.detail or ''}")


async def main() -> None:
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

    async with AsyncTwoCaptchaClient(api_key, on_event=on_event) as client:
        result = await client.solve_image(image)
        print("solved:", result.solution.text)


if __name__ == "__main__":
    asyncio.run(main())
