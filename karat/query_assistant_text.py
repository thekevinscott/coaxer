"""Query Claude and return just the assistant's text response."""

from typing import Any

from claude_agent_sdk import AssistantMessage, TextBlock

from .for_query import for_query


async def query_assistant_text(prompt: str, **options: Any) -> str:
    """Query Claude and return the concatenated assistant text response.

    Filters for AssistantMessage with TextBlock, concatenates all text
    blocks, and strips surrounding whitespace. This is the right extraction
    for DSPy's text-completion interface. For structured output, extract
    from ToolUseBlock(name="StructuredOutput") or ResultMessage instead.
    """
    result = ""
    async for block in for_query(prompt, AssistantMessage, TextBlock, **options):
        result += block.text
    return result.strip()
