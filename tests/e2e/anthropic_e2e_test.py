"""E2E: distilled prompt round-trips through Anthropic's tool-use API.

Verifies the *contract* — that the JSON Schema derived from a real
``coax``-produced artifact is accepted as a tool ``input_schema`` and that
the model's forced tool call returns input parsing cleanly under that
schema (specifically: the demo fixture's enum is honored).

We assert on schema conformance, not response content.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from coaxer.prompt import CoaxedPrompt

from .conftest import OUTPUT_FIELD_NAME, output_json_schema

ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
TOOL_NAME = "respond"


@pytest.fixture
def anthropic_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    anthropic = pytest.importorskip("anthropic")
    return anthropic.Anthropic()


def test_anthropic_round_trip_honors_enum(
    anthropic_client,
    demo_artifact: Path,
    demo_meta: dict,
    demo_inputs: dict,
) -> None:
    rendered = CoaxedPrompt(demo_artifact)(**demo_inputs)
    schema = output_json_schema(demo_meta)
    enum_values = demo_meta["fields"]["output"]["values"]

    resp = anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": rendered}],
        tools=[
            {
                "name": TOOL_NAME,
                "description": "Return the predicted output for the input.",
                "input_schema": schema,
            }
        ],
        tool_choice={"type": "tool", "name": TOOL_NAME},
    )

    tool_uses = [block for block in resp.content if getattr(block, "type", None) == "tool_use"]
    assert tool_uses, f"expected a tool_use block, got: {resp.content!r}"
    parsed = tool_uses[0].input
    assert OUTPUT_FIELD_NAME in parsed
    assert parsed[OUTPUT_FIELD_NAME] in enum_values
