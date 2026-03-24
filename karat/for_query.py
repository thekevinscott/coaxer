"""Iterate over blocks from a Claude query with optional type filtering."""

import sys
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query


async def for_query[T](
    prompt: str,
    message_type: type[T] | None = None,
    block_type: type[T] | None = None,
    **options: Any,
):
    """Async generator that yields content blocks from a Claude SDK query.

    Wraps claude_agent_sdk.query() and filters the stream by message type
    and block type. Messages without a content attribute (e.g. SystemMessage,
    TaskProgressMessage) are silently skipped.

    If a ResultMessage with is_error=True is received (e.g. usage limit),
    raises an Exception with the error text instead of silently dropping it.
    """
    opts = ClaudeAgentOptions(**options, stderr=lambda line: print(line, file=sys.stderr))
    async for message in query(prompt=prompt, options=opts):
        if isinstance(message, ResultMessage) and message.is_error:
            raise Exception(message.result)
        if message_type and not isinstance(message, message_type):
            continue
        if not hasattr(message, "content"):
            continue
        for block in message.content:  # type: ignore[union-attr]
            if block_type and not isinstance(block, block_type):
                continue
            yield block
