"""Read a label folder into `Record` objects.

One directory per record. `record.json` inside the dir maps input fields to
scalar values or sibling-file names. When a value matches a file that exists
alongside `record.json`, the file's contents are substituted in -- text when
the bytes decode as UTF-8, raw bytes otherwise.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Record:
    id: str
    inputs: dict[str, Any]
    output: Any
    meta: dict[str, Any] = field(default_factory=dict)


def load_records(folder: str | Path) -> list[Record]:
    folder = Path(folder)
    records: list[Record] = []
    for entry in sorted(folder.iterdir()):
        if not entry.is_dir():
            continue
        records.append(_load_record(entry))
    return records


def _load_record(record_dir: Path) -> Record:
    data = json.loads((record_dir / "record.json").read_text())
    inputs = {k: _resolve_value(v, record_dir) for k, v in data.get("inputs", {}).items()}
    return Record(
        id=data["id"],
        inputs=inputs,
        output=data.get("output"),
        meta=data.get("meta", {}),
    )


def _resolve_value(value: Any, record_dir: Path) -> Any:
    if not isinstance(value, str):
        return value
    candidate = record_dir / value
    if not candidate.is_file():
        if "/" in value or value.endswith((".md", ".txt", ".json", ".png", ".jpg", ".pdf")):
            raise FileNotFoundError(f"Sibling file not found: {candidate}")
        return value
    raw = candidate.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
