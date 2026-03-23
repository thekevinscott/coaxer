"""Iterate over blocks from a Claude query with optional type filtering."""

import sys
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, query


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

    With no type filters, yields every block from every message. Typical
    usage filters to AssistantMessage + TextBlock for plain text, or
    AssistantMessage + ToolUseBlock for structured output.
    """
    opts = ClaudeAgentOptions(**options, stderr=lambda line: print(line, file=sys.stderr))
    async for message in query(prompt=prompt, options=opts):
        if message_type and not isinstance(message, message_type):
            continue
        if not hasattr(message, "content"):
            continue
        for block in message.content:  # type: ignore[union-attr]
            if block_type and not isinstance(block, block_type):
                continue
            yield block
