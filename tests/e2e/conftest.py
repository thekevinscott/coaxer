"""E2E test collection gate + shared fixtures.

E2E tests hit a real LLM endpoint (Anthropic via ``claude_agent_sdk``)
with real credentials and real money. They are opt-in: set
``COAXER_E2E=1`` to enable collection. Without that env var, this
conftest tells pytest to skip the directory entirely so ``uv run just
ci`` never imports the modules.

Inside an enabled run, tests still skip cleanly when ``ANTHROPIC_API_KEY``
is absent.
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


FIXTURE = Path(__file__).resolve().parents[1] / "__fixtures__" / "labels" / "demo"


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
