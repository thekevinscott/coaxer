"""E2E test collection gate + shared fixtures.

E2E tests hit real LLM endpoints with real credentials and real money. They
are opt-in: set ``COAXER_E2E=1`` to enable collection. Without that env var,
this conftest tells pytest to skip the directory entirely so ``uv run just
ci`` never imports the modules (which would otherwise require ``openai`` /
``anthropic`` and live credentials).

Inside an enabled run, individual tests still skip cleanly when their
specific provider credential is absent.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

E2E_FLAG = "COAXER_E2E"

if not os.environ.get(E2E_FLAG):
    collect_ignore_glob = ["*_test.py"]


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "labels" / "demo"


@pytest.fixture(scope="session")
def demo_artifact(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Distill the demo fixture once per session via the real ``coax`` CLI.

    Uses ``--optimizer none`` so no LM credentials are needed for the
    *compile* step — credentials only come into play when the artifact is
    fed to a real provider in the actual test.
    """
    out = tmp_path_factory.mktemp("demo_artifact")
    result = subprocess.run(
        [sys.executable, "-m", "coaxer.cli", str(FIXTURE), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"coax CLI failed:\nstdout: {result.stdout}\nstderr: {result.stderr}")
    return out


@pytest.fixture(scope="session")
def demo_meta(demo_artifact: Path) -> dict:
    return json.loads((demo_artifact / "meta.json").read_text())


@pytest.fixture
def demo_inputs() -> dict:
    """Concrete input values for the demo fixture's three input fields."""
    return {
        "readme": (
            "# awesome-python\n\n"
            "A curated list of awesome Python frameworks, libraries, and resources."
        ),
        "description": "A curated list of awesome Python resources.",
        "stars": 200_000,
    }


OUTPUT_FIELD_NAME = "output"


def output_json_schema(meta: dict) -> dict:
    """Build a strict JSON Schema for the artifact's output field.

    Until ``CoaxedPrompt.response_format()`` lands (issue #58 dep), the e2e
    tests construct the schema themselves from ``meta.json`` so the
    wire-shape that ``response_format()`` will eventually wrap is exercised
    directly against the providers.
    """
    output = meta["fields"]["output"]
    return {
        "type": "object",
        "properties": {OUTPUT_FIELD_NAME: _field_schema(output)},
        "required": [OUTPUT_FIELD_NAME],
        "additionalProperties": False,
    }


def _field_schema(field: dict) -> dict:
    if field.get("values"):
        return {"type": "string", "enum": list(field["values"])}
    py_type = field.get("type", "str")
    if py_type == "bool":
        return {"type": "boolean"}
    if py_type == "int":
        return {"type": "integer"}
    if py_type == "float":
        return {"type": "number"}
    return {"type": "string"}
