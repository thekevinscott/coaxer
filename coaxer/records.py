"""Read a label folder into `Record` objects.

One directory per record. `record.json` inside the dir maps input fields to
scalar values or sibling-file names. When a value matches a file that exists
alongside `record.json`, the file's contents are substituted in -- text when
the bytes decode as UTF-8, raw bytes otherwise.

Whether a field is file-backed is driven by `_schema.json`:

- `{"type": "file"}` or `{"backing": "file"}` marks the field as file-backed
  (the value must name a sibling file, otherwise `FileNotFoundError`).
- Otherwise the value is treated as a scalar string. For backwards compat,
  if the value happens to name an existing sibling file, it is still read
  from disk -- but slashes in the value are NOT treated as a path hint.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from coaxer.schema import Field, Schema, load_schema


@dataclass
class Record:
    id: str
    inputs: dict[str, Any]
    output: Any
    meta: dict[str, Any] = field(default_factory=dict)


def load_records(folder: str | Path) -> list[Record]:
    folder = Path(folder)
    schema = load_schema(folder)
    records: list[Record] = []
    for entry in sorted(folder.iterdir()):
        if not entry.is_dir():
            continue
        records.append(_load_record(entry, schema))
    return records


def _load_record(record_dir: Path, schema: Schema | None) -> Record:
    data = json.loads((record_dir / "record.json").read_text())
    inputs = {
        k: _resolve_value(v, record_dir, _field_for(schema, k))
        for k, v in data.get("inputs", {}).items()
    }
    return Record(
        id=data["id"],
        inputs=inputs,
        output=data.get("output"),
        meta=data.get("meta", {}),
    )


def _field_for(schema: Schema | None, name: str) -> Field | None:
    if schema is None:
        return None
    return schema.inputs.get(name)


def _is_file_backed(field: Field | None) -> bool:
    if field is None:
        return False
    if field.type == "file":
        return True
    backing = getattr(field, "backing", None)
    return backing == "file"


def _resolve_value(value: Any, record_dir: Path, field: Field | None) -> Any:
    if not isinstance(value, str):
        return value
    file_backed = _is_file_backed(field)
    candidate = record_dir / value
    exists = _is_safe_sibling(value, candidate, record_dir)
    if file_backed:
        if not exists:
            raise FileNotFoundError(f"Sibling file not found: {candidate}")
        return _read_sibling(candidate)
    # Not marked file-backed: only resolve implicitly when the value
    # unambiguously names an existing sibling file. Slashes in the value
    # never trigger path resolution.
    if exists:
        return _read_sibling(candidate)
    return value


def _is_safe_sibling(value: str, candidate: Path, record_dir: Path) -> bool:
    """True iff `value` names an existing file directly inside `record_dir`.

    Rejects values containing path separators so we don't accidentally
    descend into subdirectories or escape the record dir.
    """
    if "/" in value or "\\" in value:
        return False
    if not candidate.is_file():
        return False
    try:
        candidate.resolve().relative_to(record_dir.resolve())
    except ValueError:
        return False
    return True


def _read_sibling(path: Path) -> str | bytes:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
