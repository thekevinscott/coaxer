"""Shared fixtures for agent-effectiveness evals."""

import json
import re
from pathlib import Path

import pytest

SKILL_MD_PATH = Path(__file__).parent.parent.parent / "karat" / "skills" / "optimize" / "SKILL.md"


@pytest.fixture(scope="session")
def skill_md() -> str:
    """Full SKILL.md content."""
    return SKILL_MD_PATH.read_text()


@pytest.fixture(scope="session")
def phase_4_docs(skill_md: str) -> str:
    """Extract just Phase 4 (TUI docs) from SKILL.md."""
    match = re.search(
        r"(## Phase 4: Collect Labels via TUI.*?)(?=## Phase 5:)",
        skill_md,
        re.DOTALL,
    )
    assert match, "Could not find Phase 4 in SKILL.md"
    return match.group(1).strip()


def _extract_json_from_response(text: str) -> dict:
    """Extract JSON from an LLM response that may contain markdown."""
    # Try to find JSON in code blocks first
    code_block = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if code_block:
        return json.loads(code_block.group(1))
    # Try the whole response as JSON
    return json.loads(text)


@pytest.fixture
def extract_json():
    """Fixture exposing JSON extraction from LLM responses."""
    return _extract_json_from_response
