from pathlib import Path

import pytest

from coaxer.records import Record, load_records

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "labels" / "demo"


def test_loads_all_records_from_folder():
    records = load_records(FIXTURE)
    assert len(records) == 3
    assert {r.id for r in records} == {"0001", "0002", "0003"}


def test_resolves_sibling_markdown_as_text():
    records = load_records(FIXTURE)
    by_id = {r.id: r for r in records}
    assert by_id["0001"].inputs["readme"].startswith("# awesome-skills")


def test_passes_through_scalar_inputs():
    records = load_records(FIXTURE)
    by_id = {r.id: r for r in records}
    assert by_id["0001"].inputs["stars"] == 521
    assert by_id["0001"].inputs["description"] == "A curated list of awesome Claude skills"


def test_output_preserved():
    records = load_records(FIXTURE)
    by_id = {r.id: r for r in records}
    assert by_id["0001"].output == "true"
    assert by_id["0002"].output == "false"


def test_ignores_schema_file(tmp_path: Path):
    (tmp_path / "_schema.json").write_text("{}")
    (tmp_path / "0001").mkdir()
    (tmp_path / "0001" / "record.json").write_text(
        '{"id": "0001", "inputs": {"x": 1}, "output": "y"}'
    )
    records = load_records(tmp_path)
    assert len(records) == 1
    assert records[0].id == "0001"


def test_missing_sibling_file_raises(tmp_path: Path):
    rec = tmp_path / "0001"
    rec.mkdir()
    (rec / "record.json").write_text(
        '{"id": "0001", "inputs": {"readme": "missing.md"}, "output": "y"}'
    )
    with pytest.raises(FileNotFoundError):
        load_records(tmp_path)


def test_reads_binary_sibling_as_bytes(tmp_path: Path):
    rec = tmp_path / "0001"
    rec.mkdir()
    (rec / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
    (rec / "record.json").write_text(
        '{"id": "0001", "inputs": {"logo": "logo.png"}, "output": "y"}'
    )
    records = load_records(tmp_path)
    assert records[0].inputs["logo"] == b"\x89PNG\r\n\x1a\n\x00\x00\x00"


def test_record_is_sortable_by_id(tmp_path: Path):
    for rid in ["0003", "0001", "0002"]:
        d = tmp_path / rid
        d.mkdir()
        (d / "record.json").write_text(f'{{"id": "{rid}", "inputs": {{}}, "output": "x"}}')
    records = load_records(tmp_path)
    assert [r.id for r in records] == ["0001", "0002", "0003"]


def test_record_dataclass_shape():
    r = Record(id="42", inputs={"a": 1}, output="b", meta={})
    assert r.id == "42"
    assert r.inputs == {"a": 1}
    assert r.output == "b"
