"""Solve an image captcha with the universal multi-provider client.

Also shows capability introspection: `supports`, `providers_supporting`,
and `supported_kinds` ask which registered adapters cover a challenge
kind without probing via `solve()`.

Works identically with Anti-Captcha, CapMonster Cloud, and Capsolver:
swap TwoCaptchaAdapter -> AntiCaptchaAdapter / CapMonsterAdapter /
CapsolverAdapter. Per-provider extras for a given kind are documented in
the challenge-class docstrings and spec/docs/architecture.md §2.
"""

import os
import sys
from pathlib import Path

from unicaptcha import ImageChallenge, Solver
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

if __name__ == "__main__":
    api_key = os.getenv("UNICAPTCHA_TWOCAPTCHA_API_KEY")
    if not api_key:
        sys.exit(
            "Set UNICAPTCHA_TWOCAPTCHA_API_KEY to your 2Captcha API key "
            "(https://2captcha.com/setting/devcenter)"
        )

    client = Solver(adapters=[TwoCaptchaAdapter(api_key)])

    # Capability introspection: registry-only, no network.
    print("supports image:", client.supports(ImageChallenge))
    print("supports hcaptcha:", client.supports("hcaptcha"))
    print("providers for image:", client.providers_supporting(ImageChallenge))
    print("all supported kinds:", client.supported_kinds())

    # Any path or bytes works; the value is normalized to bytes at construction.
    image = Path(__file__).resolve().parent.parent / "images" / "captcha.png"

    result = client.solve(ImageChallenge(image))
    print("solved:", result.solution.text)
    print("task id:", result.task_id, "cost:", result.cost)

    client.close()
