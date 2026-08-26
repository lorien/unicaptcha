"""``on_event`` handler validation and dispatch (ADR-0018, ADR-0044).

Clients attach handlers at construction and per call; the resolution
(``call handler if not None else client handler``) is a one-liner clients
own. This module holds the shared machinery:

- sync tier rejects coroutine functions at attachment and discards
  awaitable results with a WARNING (the "pathological wrapper" case);
- async tier awaits awaitable handler results inline.
- Handler exceptions propagate raw on both tiers.
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import TYPE_CHECKING

from unicaptcha.errors import InvalidConfigError

if TYPE_CHECKING:
    from unicaptcha.events import AsyncEventHandler, SyncEventHandler, TaskEvent

_logger = logging.getLogger("unicaptcha")


def check_sync_handler(
    handler: SyncEventHandler | None,
    *,
    what: str,
) -> None:
    """Reject a coroutine function passed as a sync ``on_event`` handler.

    ``functools.partial`` wrappers are unwrapped first because
    ``inspect.iscoroutinefunction`` does not follow them (it does follow
    ``__wrapped__``). ``what`` names the attachment site in the error.
    """
    if handler is None:
        return
    fn: object = handler
    while isinstance(fn, functools.partial):
        fn = fn.func
    if inspect.iscoroutinefunction(fn):
        raise InvalidConfigError(
            f"{what}: async on_event handler passed to a sync client; "
            "use the async client or a sync handler"
        )


def emit_sync(handler: SyncEventHandler | None, event: TaskEvent) -> None:
    """Call a sync handler inline (ADR-0018).

    An awaitable returned by a pathological wrapper is logged at WARNING
    and discarded; handler exceptions propagate raw.
    """
    if handler is None:
        return
    result = handler(event)
    if inspect.isawaitable(result):
        _logger.warning(
            "sync on_event handler returned an awaitable; discarding it "
            "(handler=%r kind=%s)",
            handler,
            event.kind.value,
        )


async def emit_async(handler: AsyncEventHandler | None, event: TaskEvent) -> None:
    """Call a handler inline on the async tier, awaiting awaitable results.

    Plain (sync) handlers are called directly; handler exceptions propagate
    raw.
    """
    if handler is None:
        return
    result = handler(event)
    if inspect.isawaitable(result):
        await result


__all__ = ["check_sync_handler", "emit_async", "emit_sync"]
