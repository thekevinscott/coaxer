"""E2E test: SDK errors surface with readable messages.

Requires a real Claude Code session. Run when usage limit is active:
    uv run pytest tests/e2e/sdk_error_test.py -v

Delete this file after confirming -- it only passes when rate-limited.
"""

import pytest

from karat.query_assistant_text import query_assistant_text


@pytest.mark.slow
async def test_usage_limit_surfaces_readable_error():
    """When rate-limited, the error message should contain the limit text."""
    with pytest.raises(Exception, match="limit|resets|error"):
        await query_assistant_text("say hello", tools=[])
