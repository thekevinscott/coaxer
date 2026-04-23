"""E2E tests for the labeling TUI using curtaincall.

These tests spawn `coaxer label` in a real PTY and verify the terminal
output the user actually sees. For internal state tests (assigned dict,
column keys), see tests/integration/tui_test.py which uses Textual's pilot.
"""

import json
import time
from collections.abc import Callable
from pathlib import Path

from curtaincall import Terminal, expect

COAXER = "uv run coaxer"


def _write_input(tmp_path: Path, data: dict) -> tuple[Path, Path]:
    """Write input JSON and return (input_path, output_path)."""
    inp = tmp_path / "input.json"
    inp.write_text(json.dumps(data))
    out = tmp_path / "labeled.json"
    return inp, out


def _single_field_data():
    return {
        "fields": [
            {"name": "repo_name"},
            {"name": "description"},
            {"name": "is_collection", "labels": ["collection", "organic"]},
        ],
        "examples": [
            {
                "repo_name": "awesome-python",
                "description": "A curated list",
            },
            {
                "repo_name": "flask",
                "description": "Web framework",
            },
            {
                "repo_name": "public-apis",
                "description": "Free APIs list",
            },
        ],
    }


def _multi_field_data():
    return {
        "fields": [
            {"name": "repo_name"},
            {"name": "description"},
            {
                "name": "language",
                "labels": ["Python", "JavaScript", "Rust"],
            },
            {"name": "is_collection", "labels": ["true", "false"]},
        ],
        "examples": [
            {
                "repo_name": "awesome-python",
                "description": "A curated list",
            },
            {"repo_name": "flask", "description": "Web framework"},
        ],
    }


def describe_launch():
    """The TUI should start and display examples."""

    def it_shows_examples_in_table(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _single_field_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("awesome-python")).to_be_visible(
            timeout=30,
        )
        expect(term.get_by_text("flask")).to_be_visible()
        expect(term.get_by_text("public-apis")).to_be_visible()

    def it_shows_status_bar_with_counts(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _single_field_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("0/3")).to_be_visible(timeout=30)

    def it_exits_1_for_missing_file(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        term = terminal(f"{COAXER} label {tmp_path / 'nope.json'}")
        expect(term).to_have_exited(timeout=15)
        assert term.exit_code == 1

    def it_shows_prepopulated_labels(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = _single_field_data()
        data["examples"][0]["is_collection"] = "collection"
        inp, out = _write_input(tmp_path, data)
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("collection")).to_be_visible(timeout=30)


def describe_single_field_labeling():
    """Single field with <=9 labels uses number keys."""

    def it_labels_with_number_keys(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _single_field_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("awesome-python")).to_be_visible(
            timeout=30,
        )
        term.write("1")  # label first as "collection"
        # Status should update
        expect(term.get_by_text("1/3")).to_be_visible(timeout=5)

    def it_saves_on_quit(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _single_field_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("awesome-python")).to_be_visible(
            timeout=30,
        )
        term.write("1")  # collection
        term.write("2")  # organic
        term.write("q")  # save & quit
        expect(term).to_have_exited(timeout=10)

        result = json.loads(out.read_text())
        assert result["examples"][0]["is_collection"] == "collection"
        assert result["examples"][1]["is_collection"] == "organic"
        assert result["examples"][2]["is_collection"] is None

    def it_clears_label_with_u(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _single_field_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("awesome-python")).to_be_visible(
            timeout=30,
        )
        term.write("1")  # label
        expect(term.get_by_text("1/3")).to_be_visible(timeout=5)
        # Navigate back and clear
        term.write("k")  # up
        term.write("u")  # clear
        expect(term.get_by_text("0/3")).to_be_visible(timeout=5)

    def it_resumes_from_existing_output(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = _single_field_data()
        inp, out = _write_input(tmp_path, data)
        # Write existing output
        existing = {
            "fields": data["fields"],
            "examples": [
                {**data["examples"][0], "is_collection": "collection"},
                {**data["examples"][1]},
                {**data["examples"][2], "is_collection": "organic"},
            ],
        }
        out.write_text(json.dumps(existing))

        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("2/3")).to_be_visible(timeout=30)


def describe_many_labels():
    """Single field with >9 labels uses searchable filter."""

    def _many_labels_data():
        return {
            "fields": [
                {"name": "skill_name"},
                {
                    "name": "language",
                    "labels": [
                        "Python",
                        "JavaScript",
                        "TypeScript",
                        "Ruby",
                        "Go",
                        "Rust",
                        "Java",
                        "C",
                        "C++",
                        "C#",
                        "PHP",
                        "Swift",
                    ],
                },
            ],
            "examples": [
                {"skill_name": "web-scraper"},
                {"skill_name": "data-pipeline"},
            ],
        }

    def it_opens_search_on_enter(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _many_labels_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("web-scraper")).to_be_visible(timeout=30)
        term.key_enter()
        expect(term.get_by_text("Type to filter")).to_be_visible(
            timeout=5,
        )

    def it_filters_and_selects_with_search(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _many_labels_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("web-scraper")).to_be_visible(timeout=30)
        term.key_enter()
        expect(term.get_by_text("Type to filter")).to_be_visible(
            timeout=5,
        )
        term.write("pyt")
        time.sleep(0.3)
        term.key_enter()
        # Should show Python in the table after selection
        expect(term.get_by_text("Python")).to_be_visible(timeout=5)

    def it_cancels_search_with_escape(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _many_labels_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("web-scraper")).to_be_visible(timeout=30)
        term.key_enter()
        expect(term.get_by_text("Type to filter")).to_be_visible(
            timeout=5,
        )
        term.key_escape()
        # Search panel should close -- status still shows 0
        expect(term.get_by_text("0/2")).to_be_visible(timeout=5)


def describe_multi_field():
    """Multiple label fields use cell cursor mode."""

    def it_shows_multiple_label_columns(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        inp, out = _write_input(tmp_path, _multi_field_data())
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("language")).to_be_visible(timeout=30)
        expect(term.get_by_text("is_collection")).to_be_visible()

    def it_saves_multi_field_labels(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = {
            "fields": [
                {"name": "name"},
                {"name": "color", "labels": ["red", "blue"]},
                {"name": "size", "labels": ["small", "large"]},
            ],
            "examples": [
                {"name": "item1", "color": "red", "size": "small"},
            ],
        }
        inp, out = _write_input(tmp_path, data)
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("item1")).to_be_visible(timeout=30)
        term.write("q")  # save with prepopulated values
        expect(term).to_have_exited(timeout=10)

        result = json.loads(out.read_text())
        assert result["examples"][0]["color"] == "red"
        assert result["examples"][0]["size"] == "small"


def describe_field_visibility():
    """Fields with table/detail visibility config."""

    def it_hides_table_false_fields(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = {
            "fields": [
                {"name": "name"},
                {"name": "hidden", "table": False, "detail": False},
                {"name": "label", "labels": ["A", "B"]},
            ],
            "examples": [
                {"name": "test", "hidden": "secret value"},
            ],
        }
        inp, out = _write_input(tmp_path, data)
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("test")).to_be_visible(timeout=30)
        assert not term.get_by_text("secret value").is_visible()

    def it_shows_detail_only_fields_in_detail_panel(
        terminal: Callable[..., Terminal],
        tmp_path: Path,
    ):
        data = {
            "fields": [
                {"name": "name"},
                {
                    "name": "reasoning",
                    "table": False,
                    "detail": True,
                },
                {"name": "label", "labels": ["A", "B"]},
            ],
            "examples": [
                {
                    "name": "test",
                    "reasoning": "because of XYZ reasoning",
                },
            ],
        }
        inp, out = _write_input(tmp_path, data)
        term = terminal(f"{COAXER} label {inp} --output {out}")
        expect(term.get_by_text("test")).to_be_visible(timeout=30)
        # Reasoning should be visible in detail panel
        expect(term.get_by_text("XYZ reasoning")).to_be_visible()
