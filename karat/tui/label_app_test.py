"""Unit tests for label_app input parsing and error handling."""

import json
from pathlib import Path

import pytest
from textual.widgets import DataTable

from karat.tui import LabelApp


def _write_and_load(tmp_path: Path, data: dict) -> LabelApp:
    p = tmp_path / "input.json"
    p.write_text(json.dumps(data))
    return LabelApp(input_path=p, output_path=tmp_path / "out.json")


class TestParseInput:
    """_parse_input handles valid and invalid JSON."""

    async def test_minimal_unified_format(self, tmp_path: Path):
        data = {
            "fields": [
                {"name": "text"},
                {"name": "label", "labels": ["A", "B"]},
            ],
            "examples": [{"text": "hello"}],
        }
        app = _write_and_load(tmp_path, data)
        async with app.run_test():
            table = app.query_one("#table", DataTable)
            assert table.row_count == 1

    async def test_legacy_single_label_field(self, tmp_path: Path):
        data = {
            "label_field": "is_good",
            "labels": ["true", "false"],
            "display_fields": ["name"],
            "examples": [{"name": "test"}],
        }
        app = _write_and_load(tmp_path, data)
        async with app.run_test():
            assert app.label_fields[0]["name"] == "is_good"

    def test_missing_fields_key_raises(self, tmp_path: Path):
        data = {"examples": [{"name": "test"}]}
        with pytest.raises(KeyError):
            _write_and_load(tmp_path, data)

    def test_missing_examples_key_raises(self, tmp_path: Path):
        data = {"fields": [{"name": "label", "labels": ["A"]}]}
        with pytest.raises(KeyError):
            _write_and_load(tmp_path, data)

    def test_empty_fields_does_not_crash(self, tmp_path: Path):
        data = {"fields": [], "examples": [{"name": "test"}]}
        app = _write_and_load(tmp_path, data)
        assert len(app.label_fields) == 0
