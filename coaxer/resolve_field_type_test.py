"""Strict unit tests for ``resolve_field_type``.

Covers the full type-mapping surface — primitives, enum, error paths —
with the function exercised in isolation (no Pydantic, no CoaxedPrompt,
no meta.json).
"""

from __future__ import annotations

import pytest

from coaxer.resolve_field_type import resolve_field_type
from coaxer.schema import Field


def describe_resolve_field_type():
    @pytest.mark.parametrize(
        "type_name,expected",
        [
            ("bool", bool),
            ("int", int),
            ("float", float),
            ("str", str),
        ],
    )
    def it_maps_primitives_to_python_types(type_name: str, expected: type):
        assert resolve_field_type(Field(type=type_name)) is expected

    def describe_enum():
        def it_returns_literal_of_listed_values():
            from typing import Literal, get_args, get_origin

            result = resolve_field_type(Field(type="enum", values=["yes", "no"]))
            assert get_origin(result) is Literal
            assert set(get_args(result)) == {"yes", "no"}

        def it_supports_a_single_value():
            from typing import Literal, get_args, get_origin

            result = resolve_field_type(Field(type="enum", values=["only"]))
            assert get_origin(result) is Literal
            assert get_args(result) == ("only",)

        def it_rejects_empty_values():
            with pytest.raises(ValueError, match="non-empty"):
                resolve_field_type(Field(type="enum", values=[]))

        def it_rejects_missing_values():
            with pytest.raises(ValueError, match="non-empty"):
                resolve_field_type(Field(type="enum", values=None))

    def describe_unsupported_types():
        @pytest.mark.parametrize("type_name", ["bytes", "list", "dict", "unknown"])
        def it_raises_value_error(type_name: str):
            with pytest.raises(ValueError, match="Unsupported field type"):
                resolve_field_type(Field(type=type_name))
