from pathlib import Path

from coaxer.records import Record
from coaxer.schema import Field, infer_schema, load_schema

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "__fixtures__" / "labels" / "demo"


def describe_load_schema():
    def it_loads_schema_from_folder():
        schema = load_schema(FIXTURE)
        assert schema is not None
        assert set(schema.inputs) == {"readme", "description", "stars"}
        assert schema.inputs["stars"].type == "int"
        assert schema.output.type == "enum"
        assert schema.output.values == ["true", "false"]

    def it_returns_none_when_schema_is_absent(tmp_path: Path):
        assert load_schema(tmp_path) is None


def describe_infer_schema():
    def it_infers_input_and_output_types_from_records():
        records = [
            Record(id="1", inputs={"readme": "abc", "stars": 10}, output="true"),
            Record(id="2", inputs={"readme": "def", "stars": 20}, output="false"),
        ]
        schema = infer_schema(records)
        assert set(schema.inputs) == {"readme", "stars"}
        assert schema.inputs["readme"].type == "str"
        assert schema.inputs["stars"].type == "int"
        assert schema.output.type == "str"

    def it_detects_bytes_field():
        records = [Record(id="1", inputs={"logo": b"\x89PNG"}, output="x")]
        schema = infer_schema(records)
        assert schema.inputs["logo"].type == "bytes"


def describe_Field():
    def it_has_expected_defaults():
        f = Field(type="str")
        assert f.desc is None
        assert f.values is None
