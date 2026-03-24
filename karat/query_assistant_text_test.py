"""Tests for query_assistant_text module."""

from unittest.mock import MagicMock, patch

import pytest

from karat.query_assistant_text import query_assistant_text


def describe_query_assistant_text():
    @pytest.mark.asyncio
    async def it_returns_concatenated_text():
        from claude_agent_sdk import AssistantMessage, TextBlock

        mock_text1 = MagicMock(spec=TextBlock)
        mock_text1.text = "Hello "
        mock_text2 = MagicMock(spec=TextBlock)
        mock_text2.text = "World"

        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text1, mock_text2]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("karat.for_query.query", mock_query_gen):
            result = await query_assistant_text("test prompt")
            assert result == "Hello World"

    @pytest.mark.asyncio
    async def it_raises_on_sdk_error():
        from claude_agent_sdk import ResultMessage

        error_msg = MagicMock(spec=ResultMessage)
        error_msg.is_error = True
        error_msg.result = "You've hit your limit · resets 1pm"

        async def mock_query_gen(*_args, **_kwargs):
            yield error_msg

        with patch("karat.for_query.query", mock_query_gen):
            with pytest.raises(Exception, match="You've hit your limit"):
                await query_assistant_text("test")

    @pytest.mark.asyncio
    async def it_strips_whitespace():
        from claude_agent_sdk import AssistantMessage, TextBlock

        mock_text = MagicMock(spec=TextBlock)
        mock_text.text = "  response  "

        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text]

        async def mock_query_gen(*_args, **_kwargs):
            yield mock_message

        with patch("karat.for_query.query", mock_query_gen):
            result = await query_assistant_text("test")
            assert result == "response"
