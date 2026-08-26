"""2Captcha provider package: challenges, solutions, adapter, facades.

Import model (architecture §9): eager subpackage imports; the root
``unicaptcha`` package does not preload providers.
"""

from unicaptcha.provider.twocaptcha.adapter import TwoCaptchaAdapter
from unicaptcha.provider.twocaptcha.challenge import (
    TwoCaptchaFunCaptchaChallenge,
    TwoCaptchaGeeTestV3Challenge,
    TwoCaptchaGeeTestV4Challenge,
    TwoCaptchaHCaptchaChallenge,
    TwoCaptchaImageChallenge,
    TwoCaptchaRecaptchaV2Challenge,
    TwoCaptchaRecaptchaV3Challenge,
    TwoCaptchaTextChallenge,
    TwoCaptchaTurnstileChallenge,
)
from unicaptcha.provider.twocaptcha.client import (
    AsyncTwoCaptchaClient,
    TwoCaptchaClient,
)
from unicaptcha.provider.twocaptcha.solution import (
    TwoCaptchaFunCaptchaSolution,
    TwoCaptchaGeeTestV3Solution,
    TwoCaptchaGeeTestV4Solution,
    TwoCaptchaHCaptchaSolution,
    TwoCaptchaImageSolution,
    TwoCaptchaRecaptchaV2Solution,
    TwoCaptchaRecaptchaV3Solution,
    TwoCaptchaTextSolution,
    TwoCaptchaTurnstileSolution,
)

__all__ = [
    "AsyncTwoCaptchaClient",
    "TwoCaptchaAdapter",
    "TwoCaptchaClient",
    "TwoCaptchaFunCaptchaChallenge",
    "TwoCaptchaFunCaptchaSolution",
    "TwoCaptchaGeeTestV3Challenge",
    "TwoCaptchaGeeTestV3Solution",
    "TwoCaptchaGeeTestV4Challenge",
    "TwoCaptchaGeeTestV4Solution",
    "TwoCaptchaHCaptchaChallenge",
    "TwoCaptchaHCaptchaSolution",
    "TwoCaptchaImageChallenge",
    "TwoCaptchaImageSolution",
    "TwoCaptchaRecaptchaV2Challenge",
    "TwoCaptchaRecaptchaV2Solution",
    "TwoCaptchaRecaptchaV3Challenge",
    "TwoCaptchaRecaptchaV3Solution",
    "TwoCaptchaTextChallenge",
    "TwoCaptchaTextSolution",
    "TwoCaptchaTurnstileChallenge",
    "TwoCaptchaTurnstileSolution",
]
