import json
from pathlib import Path

import pytest

from coaxer.compiler import distill

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "labels" / "demo"


def test_distill_writes_all_artifacts(tmp_path: Path):
    out = tmp_path / "prompt_out"
    distill(FIXTURE, out, optimizer=None)
    assert (out / "prompt.jinja").is_file()
    assert (out / "meta.json").is_file()
    assert (out / "history.jsonl").is_file()


def test_meta_json_records_compile_info(tmp_path: Path):
    out = tmp_path / "prompt_out"
    distill(FIXTURE, out, optimizer=None)
    meta = json.loads((out / "meta.json").read_text())
    assert meta["example_count"] == 3
    assert "compiled_at" in meta
    assert "label_hash" in meta
    assert "fields" in meta
    assert set(meta["fields"]["inputs"]) == {"readme", "description", "stars"}


def test_template_has_input_slots(tmp_path: Path):
    out = tmp_path / "prompt_out"
    distill(FIXTURE, out, optimizer=None)
    template = (out / "prompt.jinja").read_text()
    assert "{{ readme }}" in template
    assert "{{ description }}" in template
    assert "{{ stars }}" in template


def test_history_jsonl_appends(tmp_path: Path):
    out = tmp_path / "prompt_out"
    distill(FIXTURE, out, optimizer=None)
    distill(FIXTURE, out, optimizer=None)
    lines = (out / "history.jsonl").read_text().strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        entry = json.loads(line)
        assert "compiled_at" in entry


def test_template_is_valid_jinja(tmp_path: Path):
    from coaxer.prompt import CoaxedPrompt

    out = tmp_path / "prompt_out"
    distill(FIXTURE, out, optimizer=None)
    p = CoaxedPrompt(out)
    filled = p(readme="# hi", description="demo", stars=42)
    assert "# hi" in filled
    assert "42" in filled


def test_unknown_optimizer_raises(tmp_path: Path):
    out = tmp_path / "prompt_out"
    with pytest.raises(ValueError, match="optimizer"):
        distill(FIXTURE, out, optimizer="nonesuch")
