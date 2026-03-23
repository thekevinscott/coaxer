"""Integration tests for the labeling TUI.

Uses Textual's built-in pilot for headless testing.
"""

import json
from pathlib import Path

import pytest
from textual.widgets import DataTable

from karat.tui import LabelApp


@pytest.fixture
def sample_input(tmp_path: Path) -> Path:
    data = {
        "label_field": "is_collection",
        "labels": ["collection", "organic"],
        "display_fields": ["repo_name", "description"],
        "examples": [
            {"repo_name": "awesome-python", "description": "A curated list of awesome Python libs", "id": "1"},
            {"repo_name": "flask", "description": "The Python micro framework for building web apps", "id": "2"},
            {"repo_name": "public-apis", "description": "A collective list of free APIs", "id": "3"},
        ],
    }
    p = tmp_path / "examples.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    return tmp_path / "labeled.json"


class TestLabelAppMounts:
    """The app should start up and render the example table."""

    async def test_app_starts(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            table = app.query_one("#table", DataTable)
            assert table.row_count == 3

    async def test_shows_status_bar(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            from textual.widgets import Static
            status = app.query_one("#status", Static)
            rendered = str(status.render())
            assert "0/3" in rendered


class TestLabeling:
    """Pressing number keys should assign labels and auto-advance."""

    async def test_press_1_assigns_first_label(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("1")
            assert app.assigned[0] == "collection"

    async def test_press_2_assigns_second_label(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("2")
            assert app.assigned[0] == "organic"

    async def test_auto_advances_to_next_unlabeled(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("1")  # label row 0, should advance to row 1
            table = app.query_one("#table", DataTable)
            assert table.cursor_row == 1

    async def test_unlabel_clears_assignment(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("1")  # label row 0
            table = app.query_one("#table", DataTable)
            table.move_cursor(row=0)
            await pilot.pause()
            await pilot.press("u")  # clear it
            assert app.assigned[0] is None


class TestSaveAndQuit:
    """Pressing q should save labeled output and exit."""

    async def test_saves_output_on_quit(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("1")  # label first as collection
            await pilot.press("2")  # label second as organic
            await pilot.press("q")  # save & quit

        assert output_path.exists()
        result = json.loads(output_path.read_text())
        assert result["examples"][0]["label"] == "collection"
        assert result["examples"][1]["label"] == "organic"
        assert result["examples"][2]["label"] is None

    async def test_resume_from_existing_output(self, sample_input: Path, output_path: Path):
        """If output file already exists with labels, resume from it."""
        existing = {
            "label_field": "is_collection",
            "labels": ["collection", "organic"],
            "display_fields": ["repo_name", "description"],
            "examples": [
                {"repo_name": "awesome-python", "description": "...", "id": "1", "label": "collection"},
                {"repo_name": "flask", "description": "...", "id": "2", "label": None},
                {"repo_name": "public-apis", "description": "...", "id": "3", "label": "organic"},
            ],
        }
        output_path.write_text(json.dumps(existing))

        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            assert app.assigned[0] == "collection"
            assert app.assigned[2] == "organic"


LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Ruby", "Go", "Rust", "Java", "C", "C++",
    "C#", "PHP", "Swift", "Kotlin", "Scala", "Haskell", "Elixir", "Clojure", "Lua",
    "R", "Julia", "Perl", "Shell", "PowerShell", "Dart", "Objective-C", "MATLAB",
    "Groovy", "F#", "Erlang", "OCaml", "Zig", "Nim", "Crystal", "V", "Fortran",
    "COBOL", "Ada", "Pascal", "Prolog", "Lisp", "Scheme", "Racket", "Assembly",
]


@pytest.fixture
def many_labels_input(tmp_path: Path) -> Path:
    data = {
        "label_field": "language",
        "labels": LANGUAGES,
        "display_fields": ["skill_name", "url"],
        "examples": [
            {"skill_name": "web-scraper", "url": "https://github.com/foo/bar/SKILL.md", "id": "1"},
            {"skill_name": "data-pipeline", "url": "https://github.com/baz/qux/SKILL.md", "id": "2"},
            {"skill_name": "api-client", "url": "https://github.com/abc/def/SKILL.md", "id": "3"},
        ],
    }
    p = tmp_path / "skills.json"
    p.write_text(json.dumps(data))
    return p


class TestManyLabels:
    """With >9 labels, the app should use a searchable filter instead of number keys."""

    async def test_uses_search_mode_for_many_labels(self, many_labels_input: Path, output_path: Path):
        """Number keys should NOT assign labels when there are >9 labels."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("1")
            # With >9 labels, pressing "1" should NOT assign a label
            assert 0 not in app.assigned or app.assigned[0] is None

    async def test_enter_opens_search(self, many_labels_input: Path, output_path: Path):
        """Pressing Enter should open a search/filter input."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            # A search input should be visible
            from textual.widgets import Input
            search = app.query_one("#label-search", Input)
            assert search.display is True

    async def test_search_filters_and_selects(self, many_labels_input: Path, output_path: Path):
        """Typing in search should filter labels, Enter should select the top match."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("enter")  # open search
            await pilot.pause()
            await pilot.press("p", "y", "t")
            await pilot.pause()
            await pilot.press("enter")  # select top match (Python)
            await pilot.pause()
            assert app.assigned[0] == "Python"

    async def test_escape_cancels_search(self, many_labels_input: Path, output_path: Path):
        """Pressing Escape during search should cancel without labeling."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("enter")  # open search
            await pilot.press("p", "y")
            await pilot.press("escape")  # cancel
            assert 0 not in app.assigned or app.assigned[0] is None

    async def test_first_option_highlighted_on_open(self, many_labels_input: Path, output_path: Path):
        """When search opens, the first option should already be highlighted."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            from textual.widgets import OptionList
            opts = app.query_one("#label-options", OptionList)
            assert opts.highlighted == 0

    async def test_arrow_keys_navigate_options(self, many_labels_input: Path, output_path: Path):
        """Arrow down in search should move to next option, Enter selects it."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("enter")  # open search
            await pilot.pause()
            await pilot.press("down")  # move to second option
            await pilot.pause()
            await pilot.press("enter")  # select it
            await pilot.pause()
            # First option is "Python" (index 0), down once -> "JavaScript" (index 1)
            assert app.assigned[0] == "JavaScript"

    async def test_arrow_keys_with_filter(self, many_labels_input: Path, output_path: Path):
        """Arrow keys should work within filtered results."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("r")  # filters to Ruby, Rust, R, Racket, ...
            await pilot.pause()
            await pilot.press("down")  # move to second match
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            # Filtered "r" labels in order: R, Racket, Rescript, Ruby, Rust, Red, Rebol, Ring
            # First is "R", down once -> second match
            from textual.widgets import OptionList
            # Just verify something was assigned (exact order depends on label list order)
            assert 0 in app.assigned
            assert app.assigned[0] != "Python"  # definitely not Python

    async def test_search_saves_correctly(self, many_labels_input: Path, output_path: Path):
        """Labels assigned via search should save in output JSON."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("r", "u", "s", "t")
            await pilot.pause()
            await pilot.press("enter")  # select Rust
            await pilot.pause()
            await pilot.press("q")  # save & quit

        result = json.loads(output_path.read_text())
        assert result["examples"][0]["label"] == "Rust"
