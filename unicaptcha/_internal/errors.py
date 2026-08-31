"""Re-export shim: ``error_from_kind`` now lives in the public
``unicaptcha.errors`` module (ADR-0041 boundary — third-party adapters may
use it without importing ``_internal``). Kept so the engines and tests that
import ``unicaptcha._internal.errors`` keep working.
"""

from unicaptcha.errors import error_from_kind

__all__ = ["error_from_kind"]
