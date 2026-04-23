from pathlib import Path

from coaxer.records import Record
from coaxer.schema import Field, infer_schema, load_schema

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "labels" / "demo"


def test_load_schema_from_folder():
    schema = load_schema(FIXTURE)
    assert schema is not None
    assert set(schema.inputs) == {"readme", "description", "stars"}
    assert schema.inputs["stars"].type == "int"
    assert schema.output.type == "enum"
    assert schema.output.values == ["true", "false"]


def test_load_schema_returns_none_when_absent(tmp_path: Path):
    assert load_schema(tmp_path) is None


def test_infer_schema_from_records():
    records = [
        Record(id="1", inputs={"readme": "abc", "stars": 10}, output="true"),
        Record(id="2", inputs={"readme": "def", "stars": 20}, output="false"),
    ]
    schema = infer_schema(records)
    assert set(schema.inputs) == {"readme", "stars"}
    assert schema.inputs["readme"].type == "str"
    assert schema.inputs["stars"].type == "int"
    assert schema.output.type == "str"


def test_infer_detects_bytes_field():
    records = [Record(id="1", inputs={"logo": b"\x89PNG"}, output="x")]
    schema = infer_schema(records)
    assert schema.inputs["logo"].type == "bytes"


def test_schema_field_defaults():
    f = Field(type="str")
    assert f.desc is None
    assert f.values is None
