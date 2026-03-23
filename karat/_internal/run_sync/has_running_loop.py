"""Check whether an asyncio event loop is currently running."""

import asyncio


def has_running_loop() -> bool:
    """Return True if there is an active asyncio event loop in this thread."""
    try:
        loop = asyncio.get_running_loop()
        return loop.is_running()
    except RuntimeError:
        return False
