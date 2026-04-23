"""Run an async coroutine synchronously, even from within an async context."""

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any

from .has_running_loop import has_running_loop


def run_sync[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine synchronously, even from within an async context.

    Detects whether we're already inside an async event loop. If so, runs the
    coroutine in a separate thread with its own event loop to avoid
    "RuntimeError: This event loop is already running".
    """
    if has_running_loop():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()  # type: ignore[return-value]
    else:
        return asyncio.run(coro)
