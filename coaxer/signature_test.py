import dspy

from coaxer.schema import Field, Schema
from coaxer.signature import _build_instructions, build_signature


def describe_build_signature():
    def it_returns_a_dspy_signature():
        schema = Schema(
            inputs={"readme": Field(type="str", desc="Project README")},
            output=Field(type="str", desc="Classification"),
        )
        sig = build_signature(schema, output_name="is_collection")
        assert issubclass(sig, dspy.Signature)

    def it_has_input_and_output_fields_matching_schema():
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

    def it_renders_enum_output_as_literal_type():
        schema = Schema(
            inputs={"x": Field(type="str")},
            output=Field(type="enum", values=["true", "false"]),
        )
        sig = build_signature(schema, output_name="y")
        annotation = sig.output_fields["y"].annotation
        # Literal["true", "false"]
        assert str(annotation).startswith("typing.Literal") or "Literal" in str(annotation)

    def it_preserves_bool_and_int_types():
        schema = Schema(
            inputs={"x": Field(type="bool")},
            output=Field(type="int"),
        )
        sig = build_signature(schema, output_name="y")
        assert sig.input_fields["x"].annotation is bool
        assert sig.output_fields["y"].annotation is int


def describe_build_instructions():
    def it_has_no_double_period_when_output_desc_ends_in_period():
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

    def it_uses_field_descriptions_header_not_inputs():
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

    def it_appends_allowed_values_for_enum_output():
        schema = Schema(
            inputs={"x": Field(type="str", desc="Some input")},
            output=Field(type="enum", desc="A classification.", values=["true", "false"]),
        )
        instructions = _build_instructions(schema, output_name="y")
        assert "Respond with exactly one of:" in instructions
        assert "true" in instructions
        assert "false" in instructions

    def it_omits_allowed_values_line_for_non_enum_output():
        schema = Schema(
            inputs={"x": Field(type="str", desc="Some input")},
            output=Field(type="str", desc="Free-form answer."),
        )
        instructions = _build_instructions(schema, output_name="y")
        assert "Respond with exactly one of:" not in instructions
