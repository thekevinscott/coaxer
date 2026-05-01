"""Integration test: distill -> CoaxedPrompt.response_format -> Pydantic model.

Covers the full structured-output round-trip through the real distill
pipeline (no LM, no network — ``optimizer=None`` keeps it local):

- ``distill()`` persists ``output_name`` into ``meta.json``
- ``CoaxedPrompt.response_format`` reads ``meta.json`` and returns a
  Pydantic model class with the right field name and field type
- The model validates ``output.values`` for enum schemas (round-tripped
  from ``_schema.json``) and rejects values outside that enum
- Legacy artifacts (no ``output_name`` in ``meta.json``) still load
- The ``coax`` CLI's ``--output-name`` flows through to the model field,
  exercised as a subprocess round-trip
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from coaxer.compiler import distill
from coaxer.prompt import CoaxedPrompt

FIXTURE = Path(__file__).resolve().parents[1] / "__fixtures__" / "labels" / "demo"


def _bool_labels(root: Path) -> Path:
    """Build a minimal label folder with ``output.type = "bool"``."""
    rec = root / "0001"
    rec.mkdir(parents=True)
    (rec / "record.json").write_text(
        json.dumps({"id": "0001", "inputs": {"text": "hello"}, "output": True})
    )
    (root / "_schema.json").write_text(
        json.dumps(
            {
                "inputs": {"text": {"type": "str"}},
                "output": {"type": "bool"},
            }
        )
    )
    return root


def describe_response_format():
    def it_returns_a_pydantic_basemodel_subclass(tmp_path: Path) -> None:
        out = tmp_path / "out"
        distill(FIXTURE, out, optimizer=None)

        Model = CoaxedPrompt(out).response_format
        assert isinstance(Model, type)
        assert issubclass(Model, BaseModel)

    def describe_output_name():
        def it_defaults_to_output(tmp_path: Path) -> None:
            out = tmp_path / "out"
            distill(FIXTURE, out, optimizer=None)

            schema = CoaxedPrompt(out).response_format.model_json_schema()
            assert "output" in schema["properties"]

        def it_uses_the_distill_output_name(tmp_path: Path) -> None:
            out = tmp_path / "out"
            distill(FIXTURE, out, optimizer=None, output_name="is_curated")

            schema = CoaxedPrompt(out).response_format.model_json_schema()
            assert "is_curated" in schema["properties"]
            assert "output" not in schema["properties"]

    def describe_meta_json():
        def it_persists_a_custom_output_name(tmp_path: Path) -> None:
            """``output_name`` must round-trip through ``meta.json`` so
            ``CoaxedPrompt`` (which only sees the artifact directory) can recover it."""
            out = tmp_path / "out"
            distill(FIXTURE, out, optimizer=None, output_name="is_curated")

            meta = json.loads((out / "meta.json").read_text())
            assert meta["output_name"] == "is_curated"

        def it_persists_the_default_output_name(tmp_path: Path) -> None:
            out = tmp_path / "out"
            distill(FIXTURE, out, optimizer=None)

            meta = json.loads((out / "meta.json").read_text())
            assert meta["output_name"] == "output"

        def it_loads_legacy_artifacts_without_output_name(tmp_path: Path) -> None:
            """Older artifacts that predate the ``output_name`` field still load —
            runtime defaults to ``output``."""
            out = tmp_path / "out"
            distill(FIXTURE, out, optimizer=None)

            meta_path = out / "meta.json"
            meta = json.loads(meta_path.read_text())
            meta.pop("output_name", None)
            meta_path.write_text(json.dumps(meta))

            schema = CoaxedPrompt(out).response_format.model_json_schema()
            assert "output" in schema["properties"]

    def describe_enum_outputs():
        def it_validates_listed_values(tmp_path: Path) -> None:
            """Demo fixture has ``output.type=enum, values=["true","false"]``."""
            out = tmp_path / "out"
            distill(FIXTURE, out, optimizer=None)

            Model = CoaxedPrompt(out).response_format
            Model.model_validate({"output": "true"})
            Model.model_validate({"output": "false"})

        def it_rejects_other_values(tmp_path: Path) -> None:
            out = tmp_path / "out"
            distill(FIXTURE, out, optimizer=None)

            Model = CoaxedPrompt(out).response_format
            with pytest.raises(ValidationError):
                Model.model_validate({"output": "maybe"})

    def describe_bool_outputs():
        def it_emits_a_boolean_json_schema(tmp_path: Path) -> None:
            labels = _bool_labels(tmp_path / "labels")
            out = tmp_path / "out"
            distill(labels, out, optimizer=None)

            schema = CoaxedPrompt(out).response_format.model_json_schema()
            assert schema["properties"]["output"]["type"] == "boolean"

    def describe_via_cli_subprocess():
        def it_flows_output_name_through_to_response_format(tmp_path: Path) -> None:
            """``coax ... --output-name X`` produces an artifact whose
            ``response_format`` model has field ``X``."""
            out = tmp_path / "out"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "coaxer.cli",
                    str(FIXTURE),
                    "--out",
                    str(out),
                    "--output-name",
                    "is_curated",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stderr

            schema = CoaxedPrompt(out).response_format.model_json_schema()
            assert "is_curated" in schema["properties"]
