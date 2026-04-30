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
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

E2E_FLAG = "COAXER_E2E"

if not os.environ.get(E2E_FLAG):
    collect_ignore_glob = ["*_test.py"]


DEMO_FIXTURE = Path(__file__).resolve().parents[1] / "__fixtures__" / "labels" / "demo"


def run_coax(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Invoke the real ``coax`` CLI as a subprocess. Same entry point a user runs."""
    result = subprocess.run(
        [sys.executable, "-m", "coaxer.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        pytest.fail(f"coax CLI failed:\nstdout: {result.stdout}\nstderr: {result.stderr}")
    return result


@pytest.fixture(scope="session")
def demo_artifact(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Distill the demo fixture once per session via the real ``coax`` CLI.

    Uses ``--optimizer none`` so no LM credentials are needed for the
    *compile* step — credentials only come into play when the artifact is
    fed to a real provider in the actual test.
    """
    out = tmp_path_factory.mktemp("demo_artifact")
    run_coax(str(DEMO_FIXTURE), "--out", str(out))
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


@pytest.fixture
def agent_lm():
    """The same provider integration coaxer ships — claude_agent_sdk.

    ``tools=[]`` and ``max_turns=1`` constrain the session to a single
    classification-style response with no filesystem / agent loop.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    from coaxer.lm import AgentLM

    return AgentLM(tools=[], max_turns=1)


@pytest.fixture
def make_label_folder(tmp_path: Path) -> Callable[..., Path]:
    """Build a fresh label folder on disk for the test (schema + records).

    ``records`` is a list of ``(record_id, inputs_dict, output, sibling_files)``
    tuples; ``sibling_files`` is an optional dict of ``{filename: contents}``
    written next to ``record.json`` so file-backed inputs can be exercised.
    """

    def _build(
        schema: dict,
        records: list[tuple[str, dict[str, Any], Any, dict[str, str] | None]],
    ) -> Path:
        folder = tmp_path / "labels"
        folder.mkdir()
        (folder / "_schema.json").write_text(json.dumps(schema, indent=2))
        for rid, inputs, output, siblings in records:
            rdir = folder / rid
            rdir.mkdir()
            (rdir / "record.json").write_text(
                json.dumps({"id": rid, "inputs": inputs, "output": output}, indent=2)
            )
            for name, content in (siblings or {}).items():
                (rdir / name).write_text(content)
        return folder

    return _build
