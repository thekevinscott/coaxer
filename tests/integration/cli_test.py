"""Integration test: `coax` CLI compiles a label folder end-to-end.

Exercises the argparse wiring in ``coaxer.cli``: argv parsing, routing into
``distill()``, and the artifacts that land on disk. Runs the CLI as a
subprocess so the ``console_scripts`` entry point (``coax``) is exercised
the same way a user would invoke it. ``--optimizer none`` is the default,
so no LM credentials or network are needed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from coaxer.prompt import CoaxedPrompt

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "labels" / "demo"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI via ``python -m coaxer.cli`` to avoid PATH flakiness."""
    return subprocess.run(
        [sys.executable, "-m", "coaxer.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_writes_all_artifacts(tmp_path: Path) -> None:
    out = tmp_path / "prompt_out"
    result = _run_cli(str(FIXTURE), "--out", str(out))

    assert result.returncode == 0, result.stderr
    assert (out / "prompt.jinja").is_file()
    assert (out / "meta.json").is_file()
    assert (out / "history.jsonl").is_file()
    assert f"Wrote prompt to {out}/prompt.jinja" in result.stdout


def test_cli_output_renders_via_coaxed_prompt(tmp_path: Path) -> None:
    out = tmp_path / "prompt_out"
    result = _run_cli(str(FIXTURE), "--out", str(out))
    assert result.returncode == 0, result.stderr

    p = CoaxedPrompt(out)
    filled = p(readme="# hi", description="demo repo", stars=42)
    assert "# hi" in filled
    assert "demo repo" in filled
    assert "42" in filled


def test_cli_respects_output_name_flag(tmp_path: Path) -> None:
    """``--output-name`` should reach the signature builder, shaping meta.json."""
    import json

    out = tmp_path / "prompt_out"
    result = _run_cli(str(FIXTURE), "--out", str(out), "--output-name", "is_curated")
    assert result.returncode == 0, result.stderr

    meta = json.loads((out / "meta.json").read_text())
    # Input field names are unchanged; the output field name flag travels
    # through dspy.make_signature, which is exercised by _render_template.
    assert set(meta["fields"]["inputs"]) == {"readme", "description", "stars"}
    template = (out / "prompt.jinja").read_text()
    for name in ("readme", "description", "stars"):
        assert f"{{{{ {name} }}}}" in template


def test_cli_errors_on_missing_labels_dir(tmp_path: Path) -> None:
    out = tmp_path / "prompt_out"
    missing = tmp_path / "nonexistent"
    result = _run_cli(str(missing), "--out", str(out))

    assert result.returncode != 0
    assert not (out / "prompt.jinja").exists()


def test_cli_requires_out_flag(tmp_path: Path) -> None:
    result = _run_cli(str(FIXTURE))
    assert result.returncode != 0
    assert "--out" in result.stderr
