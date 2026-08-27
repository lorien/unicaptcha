"""Anti-Captcha provider package: challenges, solutions, adapter, facades.

Import model (architecture §9): eager subpackage imports; the root
``unicaptcha`` package does not preload providers.
"""

from unicaptcha.provider.anticaptcha.adapter import AntiCaptchaAdapter
from unicaptcha.provider.anticaptcha.challenge import (
    AntiCaptchaFunCaptchaChallenge,
    AntiCaptchaGeeTestV3Challenge,
    AntiCaptchaGeeTestV4Challenge,
    AntiCaptchaHCaptchaChallenge,
    AntiCaptchaImageChallenge,
    AntiCaptchaRecaptchaV2Challenge,
    AntiCaptchaRecaptchaV3Challenge,
    AntiCaptchaTextChallenge,
    AntiCaptchaTurnstileChallenge,
)
from unicaptcha.provider.anticaptcha.client import (
    AntiCaptchaClient,
    AsyncAntiCaptchaClient,
)
from unicaptcha.provider.anticaptcha.solution import (
    AntiCaptchaFunCaptchaSolution,
    AntiCaptchaGeeTestV3Solution,
    AntiCaptchaGeeTestV4Solution,
    AntiCaptchaHCaptchaSolution,
    AntiCaptchaImageSolution,
    AntiCaptchaRecaptchaV2Solution,
    AntiCaptchaRecaptchaV3Solution,
    AntiCaptchaTextSolution,
    AntiCaptchaTurnstileSolution,
)

__all__ = [
    "AntiCaptchaAdapter",
    "AntiCaptchaClient",
    "AntiCaptchaFunCaptchaChallenge",
    "AntiCaptchaFunCaptchaSolution",
    "AntiCaptchaGeeTestV3Challenge",
    "AntiCaptchaGeeTestV3Solution",
    "AntiCaptchaGeeTestV4Challenge",
    "AntiCaptchaGeeTestV4Solution",
    "AntiCaptchaHCaptchaChallenge",
    "AntiCaptchaHCaptchaSolution",
    "AntiCaptchaImageChallenge",
    "AntiCaptchaImageSolution",
    "AntiCaptchaRecaptchaV2Challenge",
    "AntiCaptchaRecaptchaV2Solution",
    "AntiCaptchaRecaptchaV3Challenge",
    "AntiCaptchaRecaptchaV3Solution",
    "AntiCaptchaTextChallenge",
    "AntiCaptchaTextSolution",
    "AntiCaptchaTurnstileChallenge",
    "AntiCaptchaTurnstileSolution",
    "AsyncAntiCaptchaClient",
]
