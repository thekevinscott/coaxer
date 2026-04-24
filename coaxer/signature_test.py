import dspy

from coaxer.schema import Field, Schema
from coaxer.signature import _build_instructions, build_signature


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


def test_instructions_no_double_period_when_output_desc_ends_in_period():
    # Regression: previously joined parts with ". " producing "..".
    schema = Schema(
        inputs={"repo_name": Field(type="str", desc="Repository name")},
        output=Field(
            type="str",
            desc="Classify based ONLY on the inputs provided. Do not fetch additional info.",
        ),
    )
    instructions = _build_instructions(schema, output_name="label")
    assert ".." not in instructions


def test_instructions_use_field_descriptions_header_not_inputs():
    # Disambiguate from the template's own "Inputs:" block.
    schema = Schema(
        inputs={
            "repo_name": Field(type="str", desc="Repository name"),
            "description": Field(type="str", desc="Short description"),
        },
        output=Field(type="str", desc="The label."),
    )
    instructions = _build_instructions(schema, output_name="label")
    assert "Field descriptions:" in instructions
    # The inline header must not collide with the template's `Inputs:` heading.
    assert "Inputs:" not in instructions


def test_instructions_enum_output_appends_allowed_values():
    schema = Schema(
        inputs={"x": Field(type="str", desc="Some input")},
        output=Field(type="enum", desc="A classification.", values=["true", "false"]),
    )
    instructions = _build_instructions(schema, output_name="y")
    assert "Respond with exactly one of:" in instructions
    assert "true" in instructions
    assert "false" in instructions


def test_instructions_non_enum_output_has_no_allowed_values_line():
    schema = Schema(
        inputs={"x": Field(type="str", desc="Some input")},
        output=Field(type="str", desc="Free-form answer."),
    )
    instructions = _build_instructions(schema, output_name="y")
    assert "Respond with exactly one of:" not in instructions
