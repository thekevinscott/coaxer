import dspy

from coaxer.schema import Field, Schema
from coaxer.signature import build_signature


def test_build_signature_returns_dspy_signature():
    schema = Schema(
        inputs={"readme": Field(type="str", desc="Project README")},
        output=Field(type="str", desc="Classification"),
    )
    sig = build_signature(schema, output_name="is_collection")
    assert issubclass(sig, dspy.Signature)


def test_build_signature_has_correct_fields():
    schema = Schema(
        inputs={
            "readme": Field(type="str", desc="README"),
            "stars": Field(type="int", desc="star count"),
        },
        output=Field(type="str"),
    )
    sig = build_signature(schema, output_name="label")
    assert set(sig.input_fields) == {"readme", "stars"}
    assert set(sig.output_fields) == {"label"}


def test_enum_output_becomes_literal_type():
    schema = Schema(
        inputs={"x": Field(type="str")},
        output=Field(type="enum", values=["true", "false"]),
    )
    sig = build_signature(schema, output_name="y")
    annotation = sig.output_fields["y"].annotation
    # Literal["true", "false"]
    assert str(annotation).startswith("typing.Literal") or "Literal" in str(annotation)


def test_bool_type_preserved():
    schema = Schema(
        inputs={"x": Field(type="bool")},
        output=Field(type="int"),
    )
    sig = build_signature(schema, output_name="y")
    assert sig.input_fields["x"].annotation is bool
    assert sig.output_fields["y"].annotation is int
