"""CapMonster Cloud provider package: challenges, solutions, adapter,
facades.

Import model (architecture §9): eager subpackage imports; the root
``unicaptcha`` package does not preload providers.
"""

from unicaptcha.provider.capmonster.adapter import CapMonsterAdapter
from unicaptcha.provider.capmonster.challenge import (
    CapMonsterFunCaptchaChallenge,
    CapMonsterGeeTestV3Challenge,
    CapMonsterGeeTestV4Challenge,
    CapMonsterHCaptchaChallenge,
    CapMonsterImageChallenge,
    CapMonsterRecaptchaV2Challenge,
    CapMonsterRecaptchaV3Challenge,
    CapMonsterTurnstileChallenge,
)
from unicaptcha.provider.capmonster.client import (
    AsyncCapMonsterClient,
    CapMonsterClient,
)
from unicaptcha.provider.capmonster.solution import (
    CapMonsterFunCaptchaSolution,
    CapMonsterGeeTestV3Solution,
    CapMonsterGeeTestV4Solution,
    CapMonsterHCaptchaSolution,
    CapMonsterImageSolution,
    CapMonsterRecaptchaV2Solution,
    CapMonsterRecaptchaV3Solution,
    CapMonsterTurnstileSolution,
)

__all__ = [
    "AsyncCapMonsterClient",
    "CapMonsterAdapter",
    "CapMonsterClient",
    "CapMonsterFunCaptchaChallenge",
    "CapMonsterFunCaptchaSolution",
    "CapMonsterGeeTestV3Challenge",
    "CapMonsterGeeTestV3Solution",
    "CapMonsterGeeTestV4Challenge",
    "CapMonsterGeeTestV4Solution",
    "CapMonsterHCaptchaChallenge",
    "CapMonsterHCaptchaSolution",
    "CapMonsterImageChallenge",
    "CapMonsterImageSolution",
    "CapMonsterRecaptchaV2Challenge",
    "CapMonsterRecaptchaV2Solution",
    "CapMonsterRecaptchaV3Challenge",
    "CapMonsterRecaptchaV3Solution",
    "CapMonsterTurnstileChallenge",
    "CapMonsterTurnstileSolution",
]
