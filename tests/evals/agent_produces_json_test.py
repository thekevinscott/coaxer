"""Tier 2: Test that an agent can produce valid TUI input JSON from docs.

These tests make real LLM calls via the Agent SDK. They are slow and
cost tokens. Run with: uv run pytest tests/evals/agent_produces_json_test.py -m slow

Each test:
1. Gives the agent Phase 4 docs as context
2. Asks it to produce JSON for a specific scenario
3. Validates the JSON loads in LabelApp without error
4. Checks structural properties
"""

import json
from pathlib import Path

import pytest
from textual.widgets import DataTable

from karat.tui import LabelApp

pytestmark = pytest.mark.slow


SYSTEM_PROMPT = """\
You are producing a JSON file for the `karat label` TUI tool.
The user will describe what they want to label. You must output
ONLY valid JSON (no markdown, no explanation) following this format:

{format_docs}

Output ONLY the JSON. No markdown code fences. No explanation."""


@pytest.fixture
def _make_prompt(phase_4_docs: str):
    """Build a system prompt with the Phase 4 docs embedded."""
    return SYSTEM_PROMPT.format(format_docs=phase_4_docs)


@pytest.fixture
def ask_agent(_make_prompt: str):
    """Call the Agent SDK to produce TUI JSON."""
    from karat._internal.run_sync import run_sync
    from karat.query_assistant_text import query_assistant_text

    async def _ask(task: str) -> dict:
        response = await query_assistant_text(
            prompt=f"{_make_prompt}\n\nTask: {task}",
            tools=[],
        )
        return json.loads(response)

    def _ask_sync(task: str) -> dict:
        return run_sync(_ask(task))

    return _ask_sync


def _load_app(tmp_path: Path, data: dict) -> LabelApp:
    p = tmp_path / "agent_output.json"
    p.write_text(json.dumps(data))
    return LabelApp(input_path=p, output_path=tmp_path / "labeled.json")


class TestBinaryClassification:
    """Agent should produce valid JSON for simple binary labeling."""

    def test_produces_valid_fields_and_examples(
        self, ask_agent, tmp_path: Path,
    ):
        result = ask_agent(
            "Create a labeling file for classifying GitHub repos as "
            "'collection' or 'organic'. Display fields: repo_name, url, "
            "description. Include 3 example repos with pre-populated labels."
        )
        assert "fields" in result
        assert "examples" in result
        assert len(result["examples"]) >= 3

        label_fields = [f for f in result["fields"] if f.get("labels")]
        assert len(label_fields) >= 1

        app = _load_app(tmp_path, result)
        assert len(app.label_fields) >= 1

    async def test_loads_in_tui(self, ask_agent, tmp_path: Path):
        result = ask_agent(
            "Create a labeling file for classifying repos. "
            "Two labels: collection, organic. "
            "Display: repo_name, description. "
            "3 examples with pre-populated labels."
        )
        app = _load_app(tmp_path, result)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            assert table.row_count >= 3


class TestMultiFieldWithReasoning:
    """Agent should handle reasoning fields with table: false."""

    def test_reasoning_fields_hidden_from_table(
        self, ask_agent,
    ):
        result = ask_agent(
            "Create a labeling file for skills. Two label fields: "
            "'language' (Python, JavaScript, Rust) and "
            "'is_collection' (true, false). "
            "For each label field, include a reasoning field that "
            "explains your prediction. Reasoning should be visible "
            "in the detail panel but not in the table. "
            "Display: skill_name, url. 2 examples."
        )
        fields = result["fields"]
        reasoning_fields = [
            f for f in fields
            if "reason" in f["name"].lower() and f.get("table") is False
        ]
        assert len(reasoning_fields) >= 1, (
            f"Expected reasoning fields with table=false, got: "
            f"{[f['name'] for f in fields]}"
        )


class TestLargeLabelSet:
    """Agent should handle >9 labels correctly."""

    def test_many_labels_produces_valid_json(
        self, ask_agent,
    ):
        result = ask_agent(
            "Create a labeling file for classifying skills by "
            "programming language. Labels should include at least: "
            "Python, JavaScript, TypeScript, Ruby, Go, Rust, Java, "
            "C, C++, C#, PHP, Swift. "
            "Display: skill_name, url. 2 examples."
        )
        label_fields = [f for f in result["fields"] if f.get("labels")]
        assert len(label_fields) >= 1
        assert len(label_fields[0]["labels"]) > 9


class TestFieldVisibility:
    """Agent should use table/detail visibility correctly."""

    def test_hidden_fields(self, ask_agent):
        result = ask_agent(
            "Create a labeling file. Display: name, url. "
            "Include an internal_id field that should NOT be shown "
            "to the user (not in table, not in detail panel). "
            "Label field: category (A, B, C). 2 examples."
        )
        hidden = [
            f for f in result["fields"]
            if f.get("table") is False and f.get("detail") is False
        ]
        assert len(hidden) >= 1, (
            f"Expected a hidden field, got: {result['fields']}"
        )
