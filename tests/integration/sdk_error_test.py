"""Integration test: SDK errors propagate through query_assistant_text."""

from unittest.mock import MagicMock, patch

import pytest

from coaxer.query_assistant_text import query_assistant_text


async def test_sdk_error_propagates_through_query_assistant_text():
    """ResultMessage errors should surface through the full query stack."""
    from claude_agent_sdk import ResultMessage

    error_msg = MagicMock(spec=ResultMessage)
    error_msg.is_error = True
    error_msg.result = "You've hit your limit · resets 1pm"

    async def mock_query_gen(*_args, **_kwargs):
        yield error_msg

    with (
        patch("coaxer.for_query.query", mock_query_gen),
        pytest.raises(Exception, match="You've hit your limit"),
    ):
        await query_assistant_text("test")
