"""Capsolver provider package: challenges, solutions, adapter, facades.

Import model (architecture §9): eager subpackage imports; the root
``unicaptcha`` package does not preload providers.
"""

from unicaptcha.provider.capsolver.adapter import CapsolverAdapter
from unicaptcha.provider.capsolver.challenge import (
    CapsolverFunCaptchaChallenge,
    CapsolverGeeTestV3Challenge,
    CapsolverGeeTestV4Challenge,
    CapsolverHCaptchaChallenge,
    CapsolverImageChallenge,
    CapsolverRecaptchaV2Challenge,
    CapsolverRecaptchaV3Challenge,
    CapsolverTurnstileChallenge,
)
from unicaptcha.provider.capsolver.client import (
    AsyncCapsolverClient,
    CapsolverClient,
)
from unicaptcha.provider.capsolver.solution import (
    CapsolverFunCaptchaSolution,
    CapsolverGeeTestV3Solution,
    CapsolverGeeTestV4Solution,
    CapsolverHCaptchaSolution,
    CapsolverImageSolution,
    CapsolverRecaptchaV2Solution,
    CapsolverRecaptchaV3Solution,
    CapsolverTurnstileSolution,
)

__all__ = [
    "AsyncCapsolverClient",
    "CapsolverAdapter",
    "CapsolverClient",
    "CapsolverFunCaptchaChallenge",
    "CapsolverFunCaptchaSolution",
    "CapsolverGeeTestV3Challenge",
    "CapsolverGeeTestV3Solution",
    "CapsolverGeeTestV4Challenge",
    "CapsolverGeeTestV4Solution",
    "CapsolverHCaptchaChallenge",
    "CapsolverHCaptchaSolution",
    "CapsolverImageChallenge",
    "CapsolverImageSolution",
    "CapsolverRecaptchaV2Challenge",
    "CapsolverRecaptchaV2Solution",
    "CapsolverRecaptchaV3Challenge",
    "CapsolverRecaptchaV3Solution",
    "CapsolverTurnstileChallenge",
    "CapsolverTurnstileSolution",
]
