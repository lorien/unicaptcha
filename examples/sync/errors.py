"""Handle provider errors: exceptions carry kind and raw response.

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaClient -> AntiCaptchaClient / CapMonsterClient /
CapsolverClient. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import os
import sys
from pathlib import Path

from unicaptcha.errors import ErrorKind, UnicaptchaError
from unicaptcha.provider.twocaptcha import TwoCaptchaClient

if __name__ == "__main__":
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

    with TwoCaptchaClient(api_key) as client:
        try:
            result = client.solve_image(image)
            print("solved:", result.solution.text)
        except UnicaptchaError as exc:
            # Every library error carries its classification...
            print(f"{type(exc).__name__} kind={exc.kind}")
            if exc.kind is ErrorKind.NO_SOLUTION:
                print("workers could not solve it; nothing was charged")
            elif exc.kind is ErrorKind.RATE_LIMIT:
                print("back off and retry later")
            else:
                print("raw provider response:", exc.raw_response[:200])
            raise SystemExit(1) from exc
