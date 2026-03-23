"""E2E tests for the labeling TUI using curtaincall.

These tests spawn the actual `karat label` command in a real PTY and
verify the terminal output the user sees.
"""

import json
from collections.abc import Callable
from pathlib import Path

from curtaincall import Terminal, expect


def _write_input(tmp_path: Path, data: dict) -> tuple[Path, Path]:
    """Write input JSON and return (input_path, output_path)."""
    inp = tmp_path / "input.json"
    inp.write_text(json.dumps(data))
    out = tmp_path / "labeled.json"
    return inp, out


def describe_karat_label():
    """Tests for `karat label` CLI command."""

    def it_launches_and_shows_table(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = {
            "fields": [
                {"name": "repo_name"},
                {"name": "is_collection", "labels": ["true", "false"]},
            ],
            "examples": [
                {"repo_name": "awesome-python", "is_collection": "true"},
                {"repo_name": "flask"},
            ],
        }
        inp, out = _write_input(tmp_path, data)
        term = terminal(f"uv run karat label {inp} --output {out}")
        expect(term.get_by_text("awesome-python")).to_be_visible(timeout=30)
        expect(term.get_by_text("flask")).to_be_visible()

    def it_shows_prepopulated_labels(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = {
            "fields": [
                {"name": "name"},
                {"name": "label", "labels": ["A", "B"]},
            ],
            "examples": [
                {"name": "first", "label": "A"},
                {"name": "second"},
            ],
        }
        inp, out = _write_input(tmp_path, data)
        term = terminal(f"uv run karat label {inp} --output {out}")
        expect(term.get_by_text("first")).to_be_visible(timeout=30)
        # Pre-populated "A" should be visible
        expect(term.get_by_text("A")).to_be_visible()

    def it_saves_on_quit(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = {
            "fields": [
                {"name": "name"},
                {"name": "label", "labels": ["yes", "no"]},
            ],
            "examples": [
                {"name": "example1"},
            ],
        }
        inp, out = _write_input(tmp_path, data)
        term = terminal(f"uv run karat label {inp} --output {out}")
        expect(term.get_by_text("example1")).to_be_visible(timeout=30)
        term.write("1")  # label as "yes"
        term.write("q")  # save & quit
        expect(term).to_have_exited(timeout=10)

        result = json.loads(out.read_text())
        assert result["examples"][0]["label"] == "yes"

    def it_exits_1_for_missing_file(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        term = terminal(
            f"uv run karat label {tmp_path / 'nope.json'}"
        )
        expect(term).to_have_exited(timeout=15)
        assert term.exit_code == 1

    def it_hides_table_false_fields(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = {
            "fields": [
                {"name": "name"},
                {"name": "reasoning", "table": False, "detail": False},
                {"name": "label", "labels": ["A", "B"]},
            ],
            "examples": [
                {
                    "name": "test",
                    "reasoning": "because reasons",
                },
            ],
        }
        inp, out = _write_input(tmp_path, data)
        term = terminal(f"uv run karat label {inp} --output {out}")
        expect(term.get_by_text("test")).to_be_visible(timeout=30)
        # "reasoning" column header should not be in the table
        # (the text may appear in the detail panel, so check the column header)
        assert not term.get_by_text("reasoning").is_visible()
