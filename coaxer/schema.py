"""Schema for a label folder.

`_schema.json` is optional. When present, its descriptions feed the DSPy
signature builder (and eventually GEPA reflection). When absent, we infer
field names + types from the records themselves.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from coaxer.records import Record


@dataclass
class Field:
    type: str = "str"
    desc: str | None = None
    values: list[str] | None = None
    backing: str | None = None


@dataclass
class Schema:
    inputs: dict[str, Field]
    output: Field


def load_schema(folder: str | Path) -> Schema | None:
    path = Path(folder) / "_schema.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text())
    inputs = {name: _field_from_dict(d) for name, d in data.get("inputs", {}).items()}
    output = _field_from_dict(data.get("output", {}))
    return Schema(inputs=inputs, output=output)


def _field_from_dict(d: dict) -> Field:
    return Field(
        type=d.get("type", "str"),
        desc=d.get("desc"),
        values=d.get("values"),
        backing=d.get("backing"),
    )


def infer_schema(records: list[Record]) -> Schema:
    if not records:
        raise ValueError("Cannot infer schema from empty record list")
    first = records[0]
    inputs = {name: Field(type=_py_type(value)) for name, value in first.inputs.items()}
    output = Field(type=_py_type(first.output))
    return Schema(inputs=inputs, output=output)


def _py_type(value: object) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, bytes):
        return "bytes"
    return "str"
