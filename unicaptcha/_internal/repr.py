"""Safe repr helpers implementing the repr policy (ADR-0034).

Bytes fields render as ``<N bytes>`` stubs; solution tokens/text render as
``***abcd`` (last 4 chars). Public model reprs in ``unicaptcha.types`` use
these; solution kind classes (task 6) use ``truncate_token`` for their
payload fields.
"""

from __future__ import annotations


def stub_bytes(raw: bytes) -> str:
    """Render a bytes field as an ``<N bytes>`` stub, never its content."""
    return f"<{len(raw)} bytes>"


def truncate_token(value: str) -> str:
    """Render a solution token as ``***abcd`` (last 4 chars)."""
    return "***" + value[-4:]


__all__ = ["stub_bytes", "truncate_token"]
