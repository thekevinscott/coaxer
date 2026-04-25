"""Tests for AgentLM."""

from unittest.mock import AsyncMock, patch

import pytest

from coaxer.lm import AgentLM

LM_MODULE = "coaxer.lm"


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
            assert lm.history == []

        def it_accepts_custom_values():
            lm = AgentLM(model="custom", max_tokens=2048, custom_arg="value")
            assert lm.model == "custom"
            assert lm.max_tokens == 2048
            assert lm.kwargs["custom_arg"] == "value"

        def it_defaults_env_to_clear_claudecode():
            """Default env strips CLAUDECODE so nested-session launches work."""
            lm = AgentLM()
            assert lm.kwargs["env"] == {"CLAUDECODE": ""}

        def it_merges_default_claudecode_into_caller_env():
            """Caller-supplied env still gets CLAUDECODE="" added."""
            lm = AgentLM(env={"FOO": "bar"})
            assert lm.kwargs["env"] == {"FOO": "bar", "CLAUDECODE": ""}

        def it_respects_explicit_claudecode_override():
            """Caller wins if they set CLAUDECODE explicitly."""
            lm = AgentLM(env={"CLAUDECODE": "1"})
            assert lm.kwargs["env"] == {"CLAUDECODE": "1"}

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

        def it_routes_system_message_into_system_prompt_option(mock_run_sync, mock_query_async):
            """System turn must land in ClaudeAgentOptions.system_prompt, not be dropped."""
            lm = AgentLM()
            lm.forward(
                messages=[
                    {"role": "system", "content": "You are a classifier."},
                    {"role": "user", "content": "Classify this."},
                ]
            )
            mock_query_async.assert_called_once()
            args, kwargs = mock_query_async.call_args
            assert args[0] == "Classify this."
            assert kwargs.get("system_prompt") == "You are a classifier."

        def it_preserves_demo_turns_in_user_prompt(mock_run_sync, mock_query_async):
            """Few-shot demo turns must be flattened into user text, not dropped."""
            lm = AgentLM()
            lm.forward(
                messages=[
                    {"role": "system", "content": "Sys"},
                    {"role": "user", "content": "ex1 input"},
                    {"role": "assistant", "content": "ex1 output"},
                    {"role": "user", "content": "final input"},
                ]
            )
            prompt_arg = mock_query_async.call_args.args[0]
            assert "ex1 input" in prompt_arg
            assert "ex1 output" in prompt_arg
            assert "final input" in prompt_arg

        def it_does_not_overwrite_caller_system_prompt(mock_run_sync, mock_query_async):
            """If caller passed system_prompt via kwargs, don't clobber it."""
            lm = AgentLM(system_prompt="caller-set")
            lm.forward(
                messages=[
                    {"role": "system", "content": "from-messages"},
                    {"role": "user", "content": "Q"},
                ]
            )
            kwargs = mock_query_async.call_args.kwargs
            assert kwargs.get("system_prompt") == "caller-set"

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
