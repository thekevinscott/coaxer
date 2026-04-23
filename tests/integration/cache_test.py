"""Integration test: ``AgentLM(cache=Cachetta(...))`` skips re-invoking the
SDK on cache hits.

The README promises cache-backed LM responses. Two successive ``forward()``
calls with identical inputs must hit the underlying SDK exactly once: the
first call populates the cache, the second returns from disk. Uses a real
``Cachetta`` instance writing under ``tmp_path`` and a mocked
``query_assistant_text`` so no subprocess is spawned.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from cachetta import Cachetta

from coaxer.lm import AgentLM


def _cache(tmp_path: Path) -> Cachetta:
    """Per-prompt cache file under tmp_path, keyed by the prompt string."""
    return Cachetta(path=lambda prompt, **_: tmp_path / "cache" / f"{hash(prompt)}.pkl")


def test_second_forward_returns_cached_response(tmp_path: Path) -> None:
    mock_query = AsyncMock(return_value="true")

    with patch("coaxer.lm.query_assistant_text", mock_query):
        lm = AgentLM(cache=_cache(tmp_path))

        first = lm.forward(prompt="classify this repo")
        second = lm.forward(prompt="classify this repo")

    assert first.choices[0].message.content == "true"
    assert second.choices[0].message.content == "true"
    # The SDK boundary is invoked exactly once despite two forward() calls.
    assert mock_query.await_count == 1


def test_different_prompts_bypass_cache(tmp_path: Path) -> None:
    mock_query = AsyncMock(side_effect=["first-response", "second-response"])

    with patch("coaxer.lm.query_assistant_text", mock_query):
        lm = AgentLM(cache=_cache(tmp_path))
        first = lm.forward(prompt="prompt A")
        second = lm.forward(prompt="prompt B")

    assert first.choices[0].message.content == "first-response"
    assert second.choices[0].message.content == "second-response"
    assert mock_query.await_count == 2


def test_cache_persists_across_agent_lm_instances(tmp_path: Path) -> None:
    """A fresh ``AgentLM`` sharing the same Cachetta should see prior hits --
    demonstrating that caching is disk-backed, not per-instance memory."""
    mock_query = AsyncMock(return_value="cached value")
    cache = _cache(tmp_path)

    with patch("coaxer.lm.query_assistant_text", mock_query):
        lm1 = AgentLM(cache=cache)
        first = lm1.forward(prompt="stable prompt")

        lm2 = AgentLM(cache=cache)
        second = lm2.forward(prompt="stable prompt")

    assert first.choices[0].message.content == "cached value"
    assert second.choices[0].message.content == "cached value"
    assert mock_query.await_count == 1


@pytest.mark.asyncio
async def test_aforward_uses_cache(tmp_path: Path) -> None:
    mock_query = AsyncMock(return_value="async reply")

    with patch("coaxer.lm.query_assistant_text", mock_query):
        lm = AgentLM(cache=_cache(tmp_path))
        first = await lm.aforward(prompt="async prompt")
        second = await lm.aforward(prompt="async prompt")

    assert first.choices[0].message.content == "async reply"
    assert second.choices[0].message.content == "async reply"
    assert mock_query.await_count == 1
