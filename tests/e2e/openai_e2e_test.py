"""E2E: distilled prompt round-trips through OpenAI's structured-output API.

Verifies the *contract* — that an artifact produced by the real ``coax``
CLI is accepted by OpenAI's ``response_format=json_schema`` path and that
the parsed response conforms to the schema we shipped (specifically: the
demo fixture's enum is honored).

We assert on schema conformance, not response content. Whether the model
classifies a given README as "curated" or not is model-dependent and not
what this test guards.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from coaxer.prompt import CoaxedPrompt

from .conftest import OUTPUT_FIELD_NAME, output_json_schema

OPENAI_MODEL = "gpt-4o-mini"


@pytest.fixture
def openai_client():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    openai = pytest.importorskip("openai")
    return openai.OpenAI()


def test_openai_round_trip_honors_enum(
    openai_client,
    demo_artifact: Path,
    demo_meta: dict,
    demo_inputs: dict,
) -> None:
    rendered = CoaxedPrompt(demo_artifact)(**demo_inputs)
    schema = output_json_schema(demo_meta)
    enum_values = demo_meta["fields"]["output"]["values"]

    resp = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": rendered}],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "Output", "schema": schema, "strict": True},
        },
    )

    raw = resp.choices[0].message.content
    parsed = json.loads(raw)
    assert OUTPUT_FIELD_NAME in parsed
    assert parsed[OUTPUT_FIELD_NAME] in enum_values
