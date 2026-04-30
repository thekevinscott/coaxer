"""E2E: a CLI-distilled prompt round-trips through the Anthropic Agent SDK.

Pairs the real ``coax`` CLI (subprocess, no internal ``distill()`` import,
no mocks) with the same provider integration coaxer ships — ``AgentLM``
backed by ``claude_agent_sdk`` — to confirm the artifact survives the
contract end-to-end against a live model.

Asserts on schema/format conformance, never on response content.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from coaxer.lm import AgentLM
from coaxer.prompt import CoaxedPrompt


def describe_distilled_prompt_via_agent_sdk():
    @pytest.fixture
    def agent_lm():
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        return AgentLM(tools=[], max_turns=1)

    def it_returns_one_of_the_enum_values_for_the_demo_classifier(
        agent_lm: AgentLM,
        demo_artifact: Path,
        demo_meta: dict,
        demo_inputs: dict,
    ) -> None:
        rendered = CoaxedPrompt(demo_artifact)(**demo_inputs)
        enum_values = demo_meta["fields"]["output"]["values"]

        resp = agent_lm.forward(prompt=rendered)
        text = resp.choices[0].message.content.strip().lower()

        assert any(v.lower() in text for v in enum_values), (
            f"expected response to contain one of {enum_values}, got: {text!r}"
        )
