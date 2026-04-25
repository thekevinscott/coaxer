"""Build a DSPy `Signature` dynamically from a `Schema`.

Internal. The library hides DSPy from users entirely; this is the bridge
between the label-folder shape and the optimizer.
"""

from __future__ import annotations

from typing import Any, Literal

import dspy

from coaxer.schema import Field, Schema

_TYPE_MAP: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "bytes": bytes,
}


def build_signature(schema: Schema, output_name: str = "output") -> type[dspy.Signature]:
    fields: dict[str, tuple[Any, Any]] = {}
    for name, spec in schema.inputs.items():
        fields[name] = (_annotation(spec), dspy.InputField(desc=spec.desc or ""))
    fields[output_name] = (
        _annotation(schema.output),
        dspy.OutputField(desc=schema.output.desc or ""),
    )
    instructions = _build_instructions(schema, output_name)
    return dspy.make_signature(fields, instructions=instructions)


def _annotation(field: Field) -> Any:
    if field.type == "enum" and field.values:
        return Literal[tuple(field.values)]  # type: ignore[valid-type]
    return _TYPE_MAP.get(field.type, str)


def _build_instructions(schema: Schema, output_name: str) -> str:
    # Join parts with blank lines so trailing periods in `output.desc`
    # don't collide with the next section (avoids the `information.. Inputs:`
    # artifact). The inline field-description block is titled
    # `Field descriptions:` to disambiguate from the template's own
    # `Inputs:` heading (which carries the jinja slot values).
    parts: list[str] = []
    if schema.output.desc:
        parts.append(schema.output.desc)
    input_descs = [f"`{n}`: {f.desc}" for n, f in schema.inputs.items() if f.desc]
    if input_descs:
        parts.append("Field descriptions: " + "; ".join(input_descs))
    if schema.output.type == "enum" and schema.output.values:
        allowed = ", ".join(schema.output.values)
        parts.append(f"Respond with exactly one of: {allowed}.")
    if not parts:
        parts.append(f"Predict {output_name} from the inputs")
    return "\n\n".join(parts)
