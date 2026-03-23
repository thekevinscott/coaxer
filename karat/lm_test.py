"""Tests for AgentLM."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from karat.lm import AgentLM

LM_MODULE = "karat.lm"


@pytest.fixture(autouse=True)
def mock_run_sync():
    with patch(f"{LM_MODULE}.run_sync") as mock:
        mock.return_value = "mocked response"
        yield mock


@pytest.fixture
def mock_query_async():
    with patch(f"{LM_MODULE}.query_assistant_text", new_callable=AsyncMock) as mock:
        mock.return_value = "async response"
        yield mock


def describe_AgentLM():
    def describe_init():
        def it_sets_default_values():
            lm = AgentLM()
            assert lm.model == "claude-agent-sdk"
            assert lm.model_type == "chat"
            assert lm.max_tokens == 4096
            assert lm.cache is None
            assert lm._cached_query is None
            assert lm.history == []

        def it_accepts_custom_values():
            lm = AgentLM(model="custom", max_tokens=2048, custom_arg="value")
            assert lm.model == "custom"
            assert lm.max_tokens == 2048
            assert lm.kwargs["custom_arg"] == "value"

        def it_wraps_query_with_cache():
            mock_cache = MagicMock()
            mock_cache.wrap.return_value = "wrapped_fn"
            lm = AgentLM(cache=mock_cache)
            assert lm.cache is mock_cache
            assert lm._cached_query == "wrapped_fn"
            mock_cache.wrap.assert_called_once()

    def describe_forward():
        def it_calls_query_assistant_text(mock_run_sync):
            mock_run_sync.return_value = "Hello world"
            lm = AgentLM()
            result = lm.forward(prompt="Test prompt")
            assert mock_run_sync.called
            assert len(result.choices) == 1
            assert result.choices[0].message.content == "Hello world"

        def it_extracts_prompt_from_messages(mock_run_sync):
            mock_run_sync.return_value = "Response"
            lm = AgentLM()
            result = lm.forward(
                messages=[
                    {"role": "system", "content": "System prompt"},
                    {"role": "user", "content": "User question"},
                ]
            )
            assert result.choices[0].message.content == "Response"

        def it_updates_history(mock_run_sync):
            mock_run_sync.return_value = "Answer"
            lm = AgentLM()
            lm.forward(prompt="Question")
            assert len(lm.history) == 1
            assert lm.history[0]["prompt"] == "Question"

        def it_handles_empty_prompt(mock_run_sync):
            mock_run_sync.return_value = ""
            lm = AgentLM()
            result = lm.forward()
            assert result.choices[0].message.content == ""

        def it_merges_kwargs(mock_run_sync):
            mock_run_sync.return_value = "ok"
            lm = AgentLM(max_turns=5)
            lm.forward(prompt="test", tools=[])
            call_args = mock_run_sync.call_args
            assert call_args is not None

        def it_uses_cached_query_when_cache_provided(mock_run_sync):
            mock_run_sync.return_value = "cached result"
            mock_cache = MagicMock()
            cached_fn = AsyncMock(return_value="cached result")
            mock_cache.wrap.return_value = cached_fn
            lm = AgentLM(cache=mock_cache)
            result = lm.forward(prompt="test")
            assert result.choices[0].message.content == "cached result"

    def describe_aforward():
        @pytest.mark.asyncio
        async def it_calls_query_assistant_text_async(mock_query_async):
            mock_query_async.return_value = "Async response"
            lm = AgentLM()
            result = await lm.aforward(prompt="Async test")
            assert result.choices[0].message.content == "Async response"

        @pytest.mark.asyncio
        async def it_extracts_prompt_from_messages_async(mock_query_async):
            mock_query_async.return_value = "Response"
            lm = AgentLM()
            result = await lm.aforward(messages=[{"role": "user", "content": "Question"}])
            assert result.choices[0].message.content == "Response"

        @pytest.mark.asyncio
        async def it_uses_cached_query_when_cache_provided(mock_query_async):
            cached_fn = AsyncMock(return_value="cached async")
            mock_cache = MagicMock()
            mock_cache.wrap.return_value = cached_fn
            lm = AgentLM(cache=mock_cache)
            result = await lm.aforward(prompt="test")
            assert result.choices[0].message.content == "cached async"
            cached_fn.assert_called_once()

    def describe_copy():
        def it_returns_new_instance():
            lm = AgentLM(max_tokens=1000)
            copied = lm.copy(extra_arg="new")
            assert copied is not lm
            assert copied.max_tokens == 1000
            assert copied.kwargs["extra_arg"] == "new"

        def it_preserves_original():
            lm = AgentLM()
            lm.copy(extra_arg="test")
            assert "extra_arg" not in lm.kwargs

        def it_preserves_cache():
            mock_cache = MagicMock()
            mock_cache.wrap.return_value = "wrapped"
            lm = AgentLM(cache=mock_cache)
            copied = lm.copy()
            assert copied.cache is mock_cache

    def describe_inspect_history():
        def it_returns_last_n_entries(mock_run_sync):
            mock_run_sync.return_value = "Response"
            lm = AgentLM()
            lm.forward(prompt="First")
            lm.forward(prompt="Second")
            lm.forward(prompt="Third")
            history = lm.inspect_history(n=2)
            assert len(history) == 2
            assert history[0]["prompt"] == "Second"
            assert history[1]["prompt"] == "Third"
