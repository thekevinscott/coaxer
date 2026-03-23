"""E2E tests for the labeling TUI.

Runs the actual `karat label` CLI subprocess to verify the full pipeline.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def sample_input(tmp_path: Path) -> Path:
    data = {
        "label_field": "is_collection",
        "labels": ["collection", "organic"],
        "display_fields": ["repo_name", "description"],
        "examples": [
            {
                "repo_name": "awesome-python",
                "description": "A curated list of awesome Python libs",
                "id": "1",
            },
            {"repo_name": "flask", "description": "The Python micro framework", "id": "2"},
        ],
    }
    p = tmp_path / "examples.json"
    p.write_text(json.dumps(data))
    return p


class TestCliLabelCommand:
    """The `karat label` command should launch and run the TUI."""

    def test_cli_import_succeeds(self):
        """The TUI module should import without errors."""
        result = subprocess.run(
            [sys.executable, "-c", "from karat.tui import LabelApp"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Import failed:\n{result.stderr}"

    def test_cli_label_missing_input_shows_usage(self):
        """Running `karat label` with no args should print usage and exit 1."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.argv = ['karat', 'label']; from karat.cli import main; main()",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "Usage" in result.stdout or "Usage" in result.stderr

    def test_cli_label_nonexistent_file_errors(self, tmp_path: Path):
        """Running `karat label` with a missing file should error."""
        nope = tmp_path / "nope.json"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.argv = ['karat', 'label', '{nope}'];"
                "from karat.cli import main; main()",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_label_app_runs_headless(self, sample_input: Path, tmp_path: Path):
        """The LabelApp should run headlessly, accept keypresses, and save output."""
        output_path = tmp_path / "labeled.json"
        # Use Textual's headless mode via run_test in a subprocess script
        script = f"""
import asyncio, json
from pathlib import Path
from karat.tui import LabelApp

async def main():
    app = LabelApp(input_path=Path("{sample_input}"), output_path=Path("{output_path}"))
    async with app.run_test() as pilot:
        await pilot.press("1")  # label first as collection
        await pilot.press("2")  # label second as organic
        await pilot.press("q")  # save & quit

asyncio.run(main())

result = json.loads(Path("{output_path}").read_text())
assert result["examples"][0]["is_collection"] == "collection"
assert result["examples"][1]["is_collection"] == "organic"
print("OK")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Headless test failed:\n{result.stderr}"
        assert "OK" in result.stdout
