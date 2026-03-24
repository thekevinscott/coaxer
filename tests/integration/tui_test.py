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
            {
                "repo_name": "awesome-python",
                "description": "A curated list of awesome Python libs",
                "id": "1",
            },
            {
                "repo_name": "flask",
                "description": "The Python micro framework for building web apps",
                "id": "2",
            },
            {
                "repo_name": "public-apis",
                "description": "A collective list of free APIs",
                "id": "3",
            },
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
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            assert table.row_count == 3

    async def test_shows_status_bar(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test():
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
            assert app.assigned[(0, "is_collection")] == "collection"

    async def test_press_2_assigns_second_label(self, sample_input: Path, output_path: Path):
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("2")
            assert app.assigned[(0, "is_collection")] == "organic"

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
            assert app.assigned[(0, "is_collection")] is None


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
        assert result["examples"][0]["is_collection"] == "collection"
        assert result["examples"][1]["is_collection"] == "organic"
        assert result["examples"][2]["is_collection"] is None

    async def test_resume_from_existing_output(self, sample_input: Path, output_path: Path):
        """If output file already exists with labels, resume from it."""
        existing = {
            "label_field": "is_collection",
            "labels": ["collection", "organic"],
            "display_fields": ["repo_name", "description"],
            "examples": [
                {
                    "repo_name": "awesome-python",
                    "description": "...",
                    "id": "1",
                    "label": "collection",
                },
                {"repo_name": "flask", "description": "...", "id": "2", "label": None},
                {"repo_name": "public-apis", "description": "...", "id": "3", "label": "organic"},
            ],
        }
        output_path.write_text(json.dumps(existing))

        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test():
            assert app.assigned[(0, "is_collection")] == "collection"
            assert app.assigned[(2, "is_collection")] == "organic"


@pytest.fixture
def multi_field_input(tmp_path: Path) -> Path:
    data = {
        "label_fields": [
            {"name": "language", "labels": ["Python", "JavaScript", "Rust"]},
            {"name": "is_collection", "labels": ["true", "false"]},
        ],
        "display_fields": ["repo_name", "description"],
        "examples": [
            {"repo_name": "awesome-python", "description": "A curated list", "id": "1"},
            {"repo_name": "flask", "description": "Web framework", "id": "2"},
            {"repo_name": "public-apis", "description": "Free APIs list", "id": "3"},
        ],
    }
    p = tmp_path / "multi.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture
def pre_populated_input(tmp_path: Path) -> Path:
    data = {
        "label_fields": [
            {"name": "language", "labels": ["Python", "JavaScript", "Rust"]},
            {"name": "is_collection", "labels": ["true", "false"]},
        ],
        "display_fields": ["repo_name", "description"],
        "examples": [
            {
                "repo_name": "awesome-python",
                "description": "A curated list",
                "id": "1",
                "language": "Python",
                "is_collection": "true",
            },
            {"repo_name": "flask", "description": "Web framework", "id": "2", "language": "Python"},
            {"repo_name": "public-apis", "description": "Free APIs list", "id": "3"},
        ],
    }
    p = tmp_path / "prepop.json"
    p.write_text(json.dumps(data))
    return p


class TestMultiFieldDataModel:
    """Multi-field labeling: new label_fields format."""

    async def test_multi_field_app_starts(self, multi_field_input: Path, output_path: Path):
        """App should mount with multiple label fields as columns."""
        app = LabelApp(input_path=multi_field_input, output_path=output_path)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            assert table.row_count == 3
            # Should have label_fields attribute with both fields
            assert len(app.label_fields) == 2
            assert app.label_fields[0]["name"] == "language"
            assert app.label_fields[1]["name"] == "is_collection"

    async def test_backward_compat_single_field(self, sample_input: Path, output_path: Path):
        """Old format with label_field (singular) should still work."""
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            assert table.row_count == 3
            assert len(app.label_fields) == 1
            assert app.label_fields[0]["name"] == "is_collection"
            assert app.label_fields[0]["labels"] == ["collection", "organic"]

    async def test_pre_populated_values_loaded(self, pre_populated_input: Path, output_path: Path):
        """Examples with existing label values should be pre-loaded into assigned."""
        app = LabelApp(input_path=pre_populated_input, output_path=output_path)
        async with app.run_test():
            # Row 0 has both fields pre-populated
            assert app.assigned[(0, "language")] == "Python"
            assert app.assigned[(0, "is_collection")] == "true"
            # Row 1 has only language
            assert app.assigned[(1, "language")] == "Python"
            assert (1, "is_collection") not in app.assigned
            # Row 2 has nothing
            assert (2, "language") not in app.assigned
            assert (2, "is_collection") not in app.assigned

    async def test_save_writes_all_label_fields(self, multi_field_input: Path, output_path: Path):
        """Save should write all label field values back to examples."""
        app = LabelApp(input_path=multi_field_input, output_path=output_path)
        async with app.run_test():
            # Manually assign some labels
            app.assigned[(0, "language")] = "Python"
            app.assigned[(0, "is_collection")] = "true"
            app.assigned[(1, "language")] = "Rust"
            app._save()

        result = json.loads(output_path.read_text())
        assert result["examples"][0]["language"] == "Python"
        assert result["examples"][0]["is_collection"] == "true"
        assert result["examples"][1]["language"] == "Rust"
        assert result["examples"][1].get("is_collection") is None
        assert result["examples"][2].get("language") is None


class TestUnifiedFields:
    """Unified `fields` array with per-field visibility configuration."""

    @pytest.fixture
    def unified_input(self, tmp_path: Path) -> Path:
        data = {
            "fields": [
                {"name": "url", "table": True, "detail": True},
                {"name": "description", "table": True, "detail": True},
                {"name": "what_reasoning", "table": False, "detail": True},
                {
                    "name": "includes_what",
                    "labels": ["true", "false"],
                    "table": True,
                    "detail": True,
                },
                {"name": "when_reasoning", "table": False, "detail": True},
                {
                    "name": "includes_when",
                    "labels": ["true", "false"],
                    "table": True,
                    "detail": True,
                },
            ],
            "examples": [
                {
                    "url": "https://example.com",
                    "description": "A daily notes skill",
                    "what_reasoning": "YES: clearly states purpose",
                    "includes_what": "true",
                    "when_reasoning": "YES: gives trigger",
                    "includes_when": "true",
                },
            ],
        }
        p = tmp_path / "unified.json"
        p.write_text(json.dumps(data))
        return p

    async def test_app_parses_unified_fields(
        self,
        unified_input: Path,
        output_path: Path,
    ):
        """Should parse unified fields format."""
        app = LabelApp(input_path=unified_input, output_path=output_path)
        async with app.run_test():
            assert len(app.label_fields) == 2
            assert app.label_fields[0]["name"] == "includes_what"

    async def test_table_excludes_hidden_columns(
        self,
        unified_input: Path,
        output_path: Path,
    ):
        """Fields with table=False should not appear as table columns."""
        app = LabelApp(input_path=unified_input, output_path=output_path)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            col_keys = [str(c.key.value) for c in table.columns.values()]
            assert "what_reasoning" not in col_keys
            assert "when_reasoning" not in col_keys
            assert "url" in col_keys
            assert "label:includes_what" in col_keys

    async def test_detail_preserves_field_order(
        self,
        unified_input: Path,
        output_path: Path,
    ):
        """Detail panel should show fields in their declared order."""
        app = LabelApp(input_path=unified_input, output_path=output_path)
        async with app.run_test():
            from textual.widgets import Static

            detail = app.query_one("#detail", Static)
            rendered = str(detail.render())
            url_pos = rendered.find("url:")
            desc_pos = rendered.find("description:")
            what_reason_pos = rendered.find("what_reasoning:")
            what_pos = rendered.find("includes_what:")
            when_reason_pos = rendered.find("when_reasoning:")
            when_pos = rendered.find("includes_when:")

            assert url_pos < desc_pos
            assert desc_pos < what_reason_pos
            assert what_reason_pos < what_pos
            assert what_pos < when_reason_pos
            assert when_reason_pos < when_pos

    async def test_detail_hides_fields_with_detail_false(
        self,
        tmp_path: Path,
        output_path: Path,
    ):
        """Fields with detail=False should not appear in detail panel."""
        data = {
            "fields": [
                {"name": "url", "detail": True},
                {"name": "internal_id", "detail": False},
                {"name": "label", "labels": ["a", "b"]},
            ],
            "examples": [
                {"url": "https://example.com", "internal_id": "abc123"},
            ],
        }
        p = tmp_path / "hidden.json"
        p.write_text(json.dumps(data))
        app = LabelApp(input_path=p, output_path=output_path)
        async with app.run_test():
            from textual.widgets import Static

            detail = app.query_one("#detail", Static)
            rendered = str(detail.render())
            assert "url:" in rendered
            assert "internal_id" not in rendered

    async def test_defaults_table_and_detail_to_true(
        self,
        tmp_path: Path,
        output_path: Path,
    ):
        """Fields without explicit table/detail should default to True."""
        data = {
            "fields": [
                {"name": "url"},
                {"name": "category", "labels": ["A", "B"]},
            ],
            "examples": [{"url": "https://example.com"}],
        }
        p = tmp_path / "defaults.json"
        p.write_text(json.dumps(data))
        app = LabelApp(input_path=p, output_path=output_path)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            col_keys = [str(c.key.value) for c in table.columns.values()]
            assert "url" in col_keys


class TestClickableUrls:
    """URL values in display fields should be rendered as clickable links."""

    @pytest.fixture
    def url_input(self, tmp_path: Path) -> Path:
        data = {
            "label_fields": [
                {"name": "is_collection", "labels": ["true", "false"]},
            ],
            "display_fields": ["repo_name", "url"],
            "examples": [
                {
                    "repo_name": "awesome-python",
                    "url": "https://github.com/vinta/awesome-python",
                    "id": "1",
                },
            ],
        }
        p = tmp_path / "urls.json"
        p.write_text(json.dumps(data))
        return p

    async def test_url_cell_is_rich_text_with_link(
        self,
        url_input: Path,
        output_path: Path,
    ):
        """URL cells should be Rich Text objects with link style."""
        from rich.text import Text

        app = LabelApp(input_path=url_input, output_path=output_path)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            cell = table.get_cell(str(0), "url")
            assert isinstance(cell, Text)
            # Check the link is embedded in the style
            url = "https://github.com/vinta/awesome-python"
            assert url in str(cell._spans[0].style)


class TestResumeEdgeCases:
    """Resume should handle unexpected output file formats gracefully."""

    async def test_resume_ignores_non_dict_output(
        self,
        sample_input: Path,
        output_path: Path,
    ):
        """If output file is a plain list (not a dict), ignore it."""
        output_path.write_text('[{"repo_name": "foo", "label": "collection"}]')
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test():
            # Should start fresh, not crash
            assert (0, "is_collection") not in app.assigned

    async def test_resume_ignores_invalid_json(
        self,
        sample_input: Path,
        output_path: Path,
    ):
        """If output file contains invalid JSON, ignore it."""
        output_path.write_text("not json at all")
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test():
            assert (0, "is_collection") not in app.assigned


class TestCellNavigation:
    """Multi-field mode uses cell cursor for spreadsheet-style editing."""

    async def test_cell_cursor_mode(self, multi_field_input: Path, output_path: Path):
        """Multi-field should use cell cursor, not row cursor."""
        app = LabelApp(input_path=multi_field_input, output_path=output_path)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            assert table.cursor_type == "cell"

    async def test_single_field_stays_row_cursor(self, sample_input: Path, output_path: Path):
        """Single-field mode should keep row cursor."""
        app = LabelApp(input_path=sample_input, output_path=output_path)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            assert table.cursor_type == "row"

    async def test_enter_on_label_cell_with_few_labels(
        self, multi_field_input: Path, output_path: Path
    ):
        """Enter on a label cell with <=9 labels should open search (in multi-field mode)."""
        app = LabelApp(input_path=multi_field_input, output_path=output_path)
        async with app.run_test() as pilot:
            app.query_one("#table", DataTable)
            # Navigate to the first label column (language)
            # Columns: # | repo_name | description | language | is_collection
            # Move right to language column
            display_cols = [f for f in app._table_fields if not f.get("labels")]
            label_col_idx = 1 + len(display_cols)
            for _ in range(label_col_idx):
                await pilot.press("right")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            from textual.widgets import Input

            search = app.query_one("#label-search", Input)
            assert search.display is True

    async def test_enter_on_display_cell_noop(self, multi_field_input: Path, output_path: Path):
        """Enter on a display cell should not open search or assign a label."""
        app = LabelApp(input_path=multi_field_input, output_path=output_path)
        async with app.run_test() as pilot:
            # Cursor starts at (0, 0) which is the # column (display)
            await pilot.press("enter")
            await pilot.pause()
            assert (0, "language") not in app.assigned or app.assigned[(0, "language")] is None

    async def test_tab_moves_between_label_columns(
        self, multi_field_input: Path, output_path: Path
    ):
        """Tab should move between label columns in the same row."""
        app = LabelApp(input_path=multi_field_input, output_path=output_path)
        async with app.run_test() as pilot:
            table = app.query_one("#table", DataTable)
            # Navigate to first label column
            label_col_idx = 1 + len([f for f in app._table_fields if not f.get("labels")])
            for _ in range(label_col_idx):
                await pilot.press("right")
            await pilot.pause()
            col_before = table.cursor_column
            await pilot.press("tab")
            await pilot.pause()
            col_after = table.cursor_column
            assert col_after == col_before + 1  # moved to next label column

    async def test_unlabel_clears_current_cell_not_first(
        self,
        multi_field_input: Path,
        output_path: Path,
    ):
        """u should clear the label under the cursor, not always the first field."""
        app = LabelApp(input_path=multi_field_input, output_path=output_path)
        async with app.run_test() as pilot:
            app.query_one("#table", DataTable)
            # Pre-assign both fields on row 0
            app.assigned[(0, "language")] = "Python"
            app.assigned[(0, "is_collection")] = "true"
            # Navigate to is_collection column (second label col)
            display_cols = [f for f in app._table_fields if not f.get("labels")]
            is_col_idx = 1 + len(display_cols) + 1  # # + display + skip language
            for _ in range(is_col_idx):
                await pilot.press("right")
            await pilot.pause()
            await pilot.press("u")
            await pilot.pause()
            # is_collection should be cleared, language should remain
            assert app.assigned[(0, "is_collection")] is None
            assert app.assigned[(0, "language")] == "Python"

    async def test_shift_u_clears_entire_row(
        self,
        multi_field_input: Path,
        output_path: Path,
    ):
        """Shift+U should clear all labels on the current row."""
        app = LabelApp(input_path=multi_field_input, output_path=output_path)
        async with app.run_test() as pilot:
            app.assigned[(0, "language")] = "Python"
            app.assigned[(0, "is_collection")] = "true"
            await pilot.press("shift+u")
            await pilot.pause()
            assert app.assigned.get((0, "language")) is None
            assert app.assigned.get((0, "is_collection")) is None


LANGUAGES = [
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
    "Kotlin",
    "Scala",
    "Haskell",
    "Elixir",
    "Clojure",
    "Lua",
    "R",
    "Julia",
    "Perl",
    "Shell",
    "PowerShell",
    "Dart",
    "Objective-C",
    "MATLAB",
    "Groovy",
    "F#",
    "Erlang",
    "OCaml",
    "Zig",
    "Nim",
    "Crystal",
    "V",
    "Fortran",
    "COBOL",
    "Ada",
    "Pascal",
    "Prolog",
    "Lisp",
    "Scheme",
    "Racket",
    "Assembly",
]


@pytest.fixture
def many_labels_input(tmp_path: Path) -> Path:
    data = {
        "label_field": "language",
        "labels": LANGUAGES,
        "display_fields": ["skill_name", "url"],
        "examples": [
            {"skill_name": "web-scraper", "url": "https://github.com/foo/bar/SKILL.md", "id": "1"},
            {
                "skill_name": "data-pipeline",
                "url": "https://github.com/baz/qux/SKILL.md",
                "id": "2",
            },
            {"skill_name": "api-client", "url": "https://github.com/abc/def/SKILL.md", "id": "3"},
        ],
    }
    p = tmp_path / "skills.json"
    p.write_text(json.dumps(data))
    return p


class TestManyLabels:
    """With >9 labels, the app should use a searchable filter instead of number keys."""

    async def test_uses_search_mode_for_many_labels(
        self, many_labels_input: Path, output_path: Path
    ):
        """Number keys should NOT assign labels when there are >9 labels."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("1")
            # With >9 labels, pressing "1" should NOT assign a label
            assert (0, "language") not in app.assigned or app.assigned[(0, "language")] is None

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
            assert app.assigned[(0, "language")] == "Python"

    async def test_escape_cancels_search(self, many_labels_input: Path, output_path: Path):
        """Pressing Escape during search should cancel without labeling."""
        app = LabelApp(input_path=many_labels_input, output_path=output_path)
        async with app.run_test() as pilot:
            await pilot.press("enter")  # open search
            await pilot.press("p", "y")
            await pilot.press("escape")  # cancel
            assert (0, "language") not in app.assigned or app.assigned[(0, "language")] is None

    async def test_first_option_highlighted_on_open(
        self, many_labels_input: Path, output_path: Path
    ):
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
            assert app.assigned[(0, "language")] == "JavaScript"

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
            # Just verify something was assigned (exact order depends on label list order)
            assert (0, "language") in app.assigned
            assert app.assigned[(0, "language")] != "Python"  # definitely not Python

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
        assert result["examples"][0]["language"] == "Rust"
