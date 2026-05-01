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


def describe_load_records():
    def describe_demo_fixture():
        def it_loads_all_records():
            records = load_records(FIXTURE)
            assert len(records) == 3
            assert {r.id for r in records} == {"0001", "0002", "0003"}

        def it_resolves_sibling_markdown_as_text():
            records = load_records(FIXTURE)
            by_id = {r.id: r for r in records}
            assert by_id["0001"].inputs["readme"].startswith("# awesome-skills")

        def it_passes_through_scalar_inputs():
            records = load_records(FIXTURE)
            by_id = {r.id: r for r in records}
            assert by_id["0001"].inputs["stars"] == 521
            assert by_id["0001"].inputs["description"] == "A curated list of awesome Claude skills"

        def it_preserves_output():
            records = load_records(FIXTURE)
            by_id = {r.id: r for r in records}
            assert by_id["0001"].output == "true"
            assert by_id["0002"].output == "false"

    def describe_filesystem_layout():
        def it_ignores_schema_file(tmp_path: Path):
            (tmp_path / "_schema.json").write_text("{}")
            (tmp_path / "0001").mkdir()
            (tmp_path / "0001" / "record.json").write_text(
                '{"id": "0001", "inputs": {"x": 1}, "output": "y"}'
            )
            records = load_records(tmp_path)
            assert len(records) == 1
            assert records[0].id == "0001"

        def it_raises_when_sibling_file_is_missing(tmp_path: Path):
            rec = tmp_path / "0001"
            rec.mkdir()
            (rec / "record.json").write_text(
                '{"id": "0001", "inputs": {"readme": "missing.md"}, "output": "y"}'
            )
            _write_schema(tmp_path, {"readme": {"type": "file"}})
            with pytest.raises(FileNotFoundError):
                load_records(tmp_path)

        def it_reads_binary_sibling_as_bytes(tmp_path: Path):
            rec = tmp_path / "0001"
            rec.mkdir()
            (rec / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
            (rec / "record.json").write_text(
                '{"id": "0001", "inputs": {"logo": "logo.png"}, "output": "y"}'
            )
            records = load_records(tmp_path)
            assert records[0].inputs["logo"] == b"\x89PNG\r\n\x1a\n\x00\x00\x00"

        def it_sorts_records_by_id(tmp_path: Path):
            for rid in ["0003", "0001", "0002"]:
                d = tmp_path / rid
                d.mkdir()
                (d / "record.json").write_text(f'{{"id": "{rid}", "inputs": {{}}, "output": "x"}}')
            records = load_records(tmp_path)
            assert [r.id for r in records] == ["0001", "0002", "0003"]

    def describe_scalar_value_handling():
        @pytest.mark.parametrize(
            "schema_inputs,record_inputs,expected_field,expected_value",
            [
                # Scalar strings containing '/' (e.g. 'owner/repo') are not sibling files.
                (None, {"repo_name": "expo/skills"}, "repo_name", "expo/skills"),
                # Explicit non-file schema type keeps slashy scalars as-is.
                (
                    {"repo_name": {"type": "str"}},
                    {"repo_name": "expo/skills"},
                    "repo_name",
                    "expo/skills",
                ),
                # YYYY/MM/DD dates are valid scalar strings, not sibling files.
                (None, {"when": "2024/01/15"}, "when", "2024/01/15"),
                # A string ending in .md when schema says str should not try sibling lookup.
                ({"title": {"type": "str"}}, {"title": "notes.md"}, "title", "notes.md"),
                # A schema-declared non-file field must not treat slashes as path separators.
                ({"slug": {"type": "str"}}, {"slug": "a/b/c"}, "slug", "a/b/c"),
            ],
            ids=[
                "slashy_scalar_no_schema",
                "slashy_scalar_str_schema",
                "date_with_slashes",
                "md_extension_str_schema",
                "schema_str_with_slashes",
            ],
        )
        def it_returns_scalar_verbatim(
            tmp_path: Path,
            schema_inputs: dict | None,
            record_inputs: dict,
            expected_field: str,
            expected_value: str,
        ):
            if schema_inputs is not None:
                _write_schema(tmp_path, schema_inputs)
            _write_record(tmp_path, "0001", record_inputs)
            records = load_records(tmp_path)
            assert records[0].inputs[expected_field] == expected_value

    def describe_sibling_file_resolution():
        def it_implicitly_resolves_when_no_schema_and_file_exists(tmp_path: Path):
            """Backwards-compat: if no schema and the sibling exists on disk, read it."""
            rec = _write_record(tmp_path, "0001", {"readme": "readme.md"})
            (rec / "readme.md").write_text("# hello")
            records = load_records(tmp_path)
            assert records[0].inputs["readme"] == "# hello"

        @pytest.mark.parametrize(
            "schema_field",
            [
                {"type": "file"},
                {"type": "str", "backing": "file"},
            ],
            ids=["type_file", "backing_file"],
        )
        def it_resolves_schema_declared_file_field(tmp_path: Path, schema_field: dict):
            rec = _write_record(tmp_path, "0001", {"doc": "doc.md"})
            (rec / "doc.md").write_text("# doc body")
            _write_schema(tmp_path, {"doc": schema_field})
            records = load_records(tmp_path)
            assert records[0].inputs["doc"] == "# doc body"

        def it_raises_when_schema_file_field_is_missing(tmp_path: Path):
            _write_record(tmp_path, "0001", {"doc": "missing.md"})
            _write_schema(tmp_path, {"doc": {"type": "file"}})
            with pytest.raises(FileNotFoundError):
                load_records(tmp_path)


def describe_Record():
    def it_has_expected_dataclass_shape():
        r = Record(id="42", inputs={"a": 1}, output="b", meta={})
        assert r.id == "42"
        assert r.inputs == {"a": 1}
        assert r.output == "b"
