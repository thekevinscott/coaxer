"""Integration test: a rendered ``CoaxedPrompt`` travels through ``AgentLM``
to the Claude Agent SDK boundary unchanged.

Contract: distill → CoaxedPrompt → lm.forward(prompt=...) must hand the
exact rendered string to ``query_assistant_text`` (the SDK boundary). We
mock the boundary so no subprocess is spawned, assert the prompt survived
the round-trip, and parse the mocked response back into a CompletionResponse.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from coaxer.compiler import distill
from coaxer.lm import AgentLM
from coaxer.prompt import CoaxedPrompt

FIXTURE = Path(__file__).resolve().parents[1] / "__fixtures__" / "labels" / "demo"


def test_rendered_coaxed_prompt_reaches_agent_sdk_unchanged(tmp_path: Path) -> None:
    out = tmp_path / "out"
    distill(FIXTURE, out, optimizer=None)

    prompt = CoaxedPrompt(out)
    rendered = prompt(
        readme="# my-repo\nContent here.",
        description="A sample repo",
        stars=1234,
    )

    with (
        patch("coaxer.lm.query_assistant_text", new_callable=AsyncMock) as mock_query,
        patch("coaxer.lm.run_sync") as mock_run_sync,
    ):
        # run_sync calls the coroutine; simulate it completing with a reply.
        mock_run_sync.return_value = "true"
        mock_query.return_value = "true"

        lm = AgentLM()
        result = lm.forward(prompt=rendered)

    # The SDK boundary must have been called with the rendered string
    # verbatim -- no truncation, no re-wrapping.
    assert mock_query.called
    sdk_args, _ = mock_query.call_args
    assert sdk_args[0] == rendered
    assert "# my-repo" in sdk_args[0]
    assert "A sample repo" in sdk_args[0]
    assert "1234" in sdk_args[0]

    # The mocked response is parsed into a CompletionResponse.
    assert result.choices[0].message.content == "true"
    assert result.choices[0].message.role == "assistant"


@pytest.mark.asyncio
async def test_rendered_coaxed_prompt_reaches_agent_sdk_async(tmp_path: Path) -> None:
    out = tmp_path / "out"
    distill(FIXTURE, out, optimizer=None)
    prompt = CoaxedPrompt(out)
    rendered = prompt(readme="# r", description="d", stars=7)

    with patch("coaxer.lm.query_assistant_text", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = "false"
        lm = AgentLM()
        result = await lm.aforward(prompt=rendered)

    mock_query.assert_awaited_once()
    sdk_args, _ = mock_query.call_args
    assert sdk_args[0] == rendered
    assert result.choices[0].message.content == "false"


def test_coaxed_prompt_is_str_subclass_for_drop_in_use(tmp_path: Path) -> None:
    """The string-subclass guarantee is what makes ``lm.forward(prompt=p)``
    work when ``p`` is a freshly-constructed, *unrendered* CoaxedPrompt.
    Guard that this stays true end-to-end."""
    out = tmp_path / "out"
    distill(FIXTURE, out, optimizer=None)
    prompt = CoaxedPrompt(out)

    assert isinstance(prompt, str)

    with (
        patch("coaxer.lm.query_assistant_text", new_callable=AsyncMock) as mock_query,
        patch("coaxer.lm.run_sync") as mock_run_sync,
    ):
        mock_query.return_value = "ok"
        mock_run_sync.return_value = "ok"

        lm = AgentLM()
        lm.forward(prompt=prompt)

    sdk_args, _ = mock_query.call_args
    # The raw template (unrendered) should still pass through verbatim --
    # str(prompt) is its template text.
    assert sdk_args[0] == str(prompt)
