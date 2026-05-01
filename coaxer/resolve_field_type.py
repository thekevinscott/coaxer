"""Map a coaxer ``Field`` to the Python type used for a Pydantic model.

Used by ``CoaxedPrompt.response_format`` to build a Pydantic model class
from the compiled output schema. Lives as its own module so the
type-mapping rules can evolve (or grow new cases) under tight unit tests
without dragging in the rest of ``prompt.py``.
"""

from __future__ import annotations

from typing import Any, Literal

from coaxer.schema import Field

_PRIMITIVE_TYPES: dict[str, type] = {
    "bool": bool,
    "int": int,
    "float": float,
    "str": str,
}


def resolve_field_type(field: Field) -> Any:
    if field.type == "enum":
        values = field.values or []
        if not values:
            raise ValueError("enum field requires non-empty `values`")
        # Literal subscription with a runtime list is dynamic by nature; ty
        # can't statically verify the values, but pydantic accepts it.
        return Literal[*values]  # ty: ignore[invalid-type-form]
    if field.type in _PRIMITIVE_TYPES:
        return _PRIMITIVE_TYPES[field.type]
    raise ValueError(f"Unsupported field type for response_format: {field.type!r}")
