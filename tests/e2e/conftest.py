"""E2E shared fixtures.

E2E tests hit a real LLM endpoint (Anthropic via ``claude_agent_sdk``)
with real credentials and real money. They live under ``tests/e2e/``
and CI never points pytest at this directory — running them is the
agent's call (``uv run just test-e2e`` or ``uv run pytest tests/e2e/``)
when a change touches the SDK-contract surface. ``ANTHROPIC_API_KEY``
must be set; absent credentials surface as the SDK's auth error so
misconfiguration is loud rather than silently skipped.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

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
