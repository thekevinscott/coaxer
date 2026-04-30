from pathlib import Path

import pytest

from coaxer.records import Record, load_records

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "__fixtures__" / "labels" / "demo"


def _write_schema(folder: Path, inputs: dict, output: dict | None = None) -> None:
    import json as _json

    payload = {"inputs": inputs, "output": output or {"type": "str"}}
    (folder / "_schema.json").write_text(_json.dumps(payload))


def _write_record(folder: Path, rid: str, inputs: dict, output: str = "y") -> Path:
    import json as _json

    rec = folder / rid
    rec.mkdir()
    (rec / "record.json").write_text(_json.dumps({"id": rid, "inputs": inputs, "output": output}))
    return rec


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
    _write_schema(tmp_path, {"readme": {"type": "file"}})
    with pytest.raises(FileNotFoundError):
        load_records(tmp_path)


def test_scalar_with_slash_returned_verbatim_without_schema(tmp_path: Path):
    """Scalar strings containing '/' (e.g. 'owner/repo') are not sibling files."""
    _write_record(tmp_path, "0001", {"repo_name": "expo/skills"})
    records = load_records(tmp_path)
    assert records[0].inputs["repo_name"] == "expo/skills"


def test_scalar_with_slash_returned_verbatim_when_schema_not_file_backed(tmp_path: Path):
    """Explicit non-file schema type keeps slashy scalars as-is."""
    _write_schema(tmp_path, {"repo_name": {"type": "str"}})
    _write_record(tmp_path, "0001", {"repo_name": "expo/skills"})
    records = load_records(tmp_path)
    assert records[0].inputs["repo_name"] == "expo/skills"


def test_date_string_with_slashes_returned_verbatim(tmp_path: Path):
    """YYYY/MM/DD dates are valid scalar strings, not sibling files."""
    _write_record(tmp_path, "0001", {"when": "2024/01/15"})
    records = load_records(tmp_path)
    assert records[0].inputs["when"] == "2024/01/15"


def test_extensioned_string_returned_verbatim_when_schema_not_file_backed(tmp_path: Path):
    """A string ending in .md when schema says str should not try sibling lookup."""
    _write_schema(tmp_path, {"title": {"type": "str"}})
    _write_record(tmp_path, "0001", {"title": "notes.md"})
    records = load_records(tmp_path)
    assert records[0].inputs["title"] == "notes.md"


def test_implicit_sibling_resolution_when_file_exists(tmp_path: Path):
    """Backwards-compat: if no schema and the sibling exists on disk, read it."""
    rec = _write_record(tmp_path, "0001", {"readme": "readme.md"})
    (rec / "readme.md").write_text("# hello")
    records = load_records(tmp_path)
    assert records[0].inputs["readme"] == "# hello"


def test_schema_declared_file_field_resolves(tmp_path: Path):
    """`type: file` in schema resolves sibling file contents."""
    rec = _write_record(tmp_path, "0001", {"doc": "doc.md"})
    (rec / "doc.md").write_text("# doc body")
    _write_schema(tmp_path, {"doc": {"type": "file"}})
    records = load_records(tmp_path)
    assert records[0].inputs["doc"] == "# doc body"


def test_schema_backing_file_field_resolves(tmp_path: Path):
    """`backing: file` in schema resolves sibling file contents."""
    rec = _write_record(tmp_path, "0001", {"doc": "doc.md"})
    (rec / "doc.md").write_text("# doc body")
    _write_schema(tmp_path, {"doc": {"type": "str", "backing": "file"}})
    records = load_records(tmp_path)
    assert records[0].inputs["doc"] == "# doc body"


def test_schema_file_field_missing_raises(tmp_path: Path):
    """If schema declares a file field but file is missing, raise."""
    _write_record(tmp_path, "0001", {"doc": "missing.md"})
    _write_schema(tmp_path, {"doc": {"type": "file"}})
    with pytest.raises(FileNotFoundError):
        load_records(tmp_path)


def test_schema_file_field_with_slash_in_value_is_not_treated_as_path(tmp_path: Path):
    """A schema-declared non-file field must not treat slashes as path separators."""
    _write_schema(tmp_path, {"slug": {"type": "str"}})
    _write_record(tmp_path, "0001", {"slug": "a/b/c"})
    records = load_records(tmp_path)
    assert records[0].inputs["slug"] == "a/b/c"


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
