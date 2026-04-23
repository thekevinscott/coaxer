"""Integration test: ``distill(..., optimizer='gepa', lm=...)`` writes
``dspy.json`` with non-empty program state.

DSPy's GEPA runs many internal LM calls against a real optimizer loop --
well outside the integration scope. We stub ``dspy.GEPA`` so its ``.compile()``
returns a program stub whose ``dump_state()`` emits a small dict, then verify
that the stubbed program state lands on disk via the real
``_dump_program``/``distill`` path. The AgentLM is pointed at a mocked
``run_sync`` so nothing ever reaches the Claude Agent SDK.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from coaxer.compiler import distill
from coaxer.lm import AgentLM

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "labels" / "demo"


class _StubProgram:
    """Minimal object that mimics a compiled DSPy program for serialization."""

    def dump_state(self) -> dict:
        return {
            "signature": "stub",
            "demos": [],
            "predictors": {"output": {"prompt": "stub-prompt"}},
        }


class _StubOptimizer:
    def __init__(self, *_: object, **__: object) -> None:
        self.compile_calls: list[tuple[object, object]] = []

    def compile(self, program, *, trainset):
        self.compile_calls.append((program, trainset))
        return _StubProgram()


def test_distill_with_gepa_writes_dspy_json_with_program_state(tmp_path: Path) -> None:
    out = tmp_path / "out"

    with (
        patch("coaxer.lm.run_sync", return_value="true"),
        patch("dspy.GEPA", _StubOptimizer),
    ):
        lm = AgentLM()
        distill(FIXTURE, out, lm=lm, optimizer="gepa")

    assert (out / "dspy.json").is_file()
    state = json.loads((out / "dspy.json").read_text())
    # State must be non-empty and reflect our stub's shape.
    assert state
    assert state["signature"] == "stub"
    assert "predictors" in state


def test_distill_gepa_requires_lm(tmp_path: Path) -> None:
    """Missing ``lm`` must surface as a clear error, not a silent no-op."""
    out = tmp_path / "out"
    with (
        patch("dspy.GEPA", _StubOptimizer),
        pytest.raises(ValueError, match="GEPA requires an `lm`"),
    ):
        distill(FIXTURE, out, lm=None, optimizer="gepa")


def test_distill_gepa_meta_records_optimizer(tmp_path: Path) -> None:
    out = tmp_path / "out"
    with patch("coaxer.lm.run_sync", return_value="true"), patch("dspy.GEPA", _StubOptimizer):
        distill(FIXTURE, out, lm=AgentLM(), optimizer="gepa")

    meta = json.loads((out / "meta.json").read_text())
    assert meta["optimizer"] == "gepa"
    assert meta["example_count"] == 3
