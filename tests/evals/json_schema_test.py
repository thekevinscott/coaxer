"""Tier 1: Validate that well-formed and malformed JSON is handled correctly.

No LLM calls -- these test the schema validation layer that agent-produced
JSON must pass through. If these fail, the docs are misleading.
"""

import json
from pathlib import Path

import pytest
from textual.widgets import DataTable

from karat.tui import LabelApp


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    return tmp_path / "labeled.json"


def _write_and_load(tmp_path: Path, data: dict) -> LabelApp:
    p = tmp_path / "input.json"
    p.write_text(json.dumps(data))
    return LabelApp(input_path=p, output_path=tmp_path / "out.json")


class TestValidUnifiedFormat:
    """JSON matching the documented unified format should load."""

    async def test_minimal_valid(self, tmp_path: Path):
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

    async def test_with_visibility_flags(self, tmp_path: Path):
        data = {
            "fields": [
                {"name": "url", "table": True, "detail": True},
                {"name": "reasoning", "table": False, "detail": True},
                {"name": "label", "labels": ["yes", "no"]},
            ],
            "examples": [
                {"url": "https://example.com", "reasoning": "because"},
            ],
        }
        app = _write_and_load(tmp_path, data)
        async with app.run_test():
            assert len(app.label_fields) == 1

    async def test_with_prepopulated_values(self, tmp_path: Path):
        data = {
            "fields": [
                {"name": "name"},
                {"name": "category", "labels": ["A", "B", "C"]},
            ],
            "examples": [
                {"name": "first", "category": "A"},
                {"name": "second"},
            ],
        }
        app = _write_and_load(tmp_path, data)
        async with app.run_test():
            assert app.assigned[(0, "category")] == "A"
            assert (1, "category") not in app.assigned

    async def test_multi_label_fields(self, tmp_path: Path):
        data = {
            "fields": [
                {"name": "name"},
                {"name": "color", "labels": ["red", "blue"]},
                {"name": "size", "labels": ["small", "large"]},
            ],
            "examples": [{"name": "item"}],
        }
        app = _write_and_load(tmp_path, data)
        async with app.run_test():
            assert len(app.label_fields) == 2

    async def test_large_label_set(self, tmp_path: Path):
        labels = [f"lang_{i}" for i in range(50)]
        data = {
            "fields": [
                {"name": "name"},
                {"name": "language", "labels": labels},
            ],
            "examples": [{"name": "test"}],
        }
        app = _write_and_load(tmp_path, data)
        async with app.run_test():
            assert not app._use_number_keys


class TestLegacyFormats:
    """Old formats from the docs should still work."""

    async def test_label_fields_format(self, tmp_path: Path):
        data = {
            "label_fields": [
                {"name": "label", "labels": ["yes", "no"]},
            ],
            "display_fields": ["name"],
            "examples": [{"name": "test"}],
        }
        app = _write_and_load(tmp_path, data)
        async with app.run_test():
            assert len(app.label_fields) == 1

    async def test_single_label_field_format(self, tmp_path: Path):
        data = {
            "label_field": "is_good",
            "labels": ["true", "false"],
            "display_fields": ["name"],
            "examples": [{"name": "test"}],
        }
        app = _write_and_load(tmp_path, data)
        async with app.run_test():
            assert app.label_fields[0]["name"] == "is_good"


class TestMalformedInput:
    """Bad JSON should produce clear errors, not cryptic crashes."""

    def test_missing_fields_key(self, tmp_path: Path):
        data = {"examples": [{"name": "test"}]}
        with pytest.raises(KeyError):
            _write_and_load(tmp_path, data)

    def test_missing_examples_key(self, tmp_path: Path):
        data = {"fields": [{"name": "label", "labels": ["A"]}]}
        with pytest.raises(KeyError):
            _write_and_load(tmp_path, data)

    def test_empty_fields(self, tmp_path: Path):
        data = {"fields": [], "examples": [{"name": "test"}]}
        app = _write_and_load(tmp_path, data)
        assert len(app.label_fields) == 0
