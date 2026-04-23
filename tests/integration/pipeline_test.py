"""Integration test: label folder → compiled prompt → rendered string.

Covers the full ``distill()`` pipeline end-to-end: records loading with
text + binary sibling resolution, schema loading (explicit and inferred),
signature building, template rendering, and the ``CoaxedPrompt`` round-trip
that users consume. Externals (SDK, network) aren't in this path --
``optimizer=None`` keeps the whole pipeline local and deterministic.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from coaxer.compiler import distill
from coaxer.prompt import CoaxedPrompt

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "labels" / "demo"


def test_explicit_schema_flows_through_to_rendered_prompt(tmp_path: Path) -> None:
    """With an explicit ``_schema.json``, field descriptions and types must
    make it into the compiled artifact and the Jinja template."""
    out = tmp_path / "out"
    distill(FIXTURE, out, optimizer=None)

    meta = json.loads((out / "meta.json").read_text())
    assert meta["fields"]["inputs"]["stars"]["type"] == "int"
    assert meta["fields"]["output"]["type"] == "enum"
    assert meta["fields"]["output"]["values"] == ["true", "false"]

    p = CoaxedPrompt(out)
    rendered = p(
        readme="# my-repo\nHello.",
        description="Test description",
        stars=999,
    )
    assert "# my-repo" in rendered
    assert "Test description" in rendered
    assert "999" in rendered


def test_inferred_schema_flows_through_to_rendered_prompt(tmp_path: Path) -> None:
    """Without ``_schema.json``, types are inferred from the first record.
    The rendered template should still accept the same variables."""
    labels = tmp_path / "labels"
    shutil.copytree(FIXTURE, labels)
    (labels / "_schema.json").unlink()

    out = tmp_path / "out"
    distill(labels, out, optimizer=None)

    meta = json.loads((out / "meta.json").read_text())
    # Inference path preserves field names and infers ``stars`` as int.
    assert set(meta["fields"]["inputs"]) == {"readme", "description", "stars"}
    assert meta["fields"]["inputs"]["stars"]["type"] == "int"
    # Enum info is unavailable without a schema -- output should fall back
    # to the scalar type of the first record's output (a string).
    assert meta["fields"]["output"]["type"] == "str"

    p = CoaxedPrompt(out)
    rendered = p(readme="# hi", description="x", stars=1)
    assert "# hi" in rendered


def test_text_sibling_files_are_resolved_into_records(tmp_path: Path) -> None:
    """``readme.md`` sibling should be substituted into inputs.readme and
    survive to render time through the example pipeline."""
    # Records are loaded inside distill(), but to verify sibling resolution
    # end-to-end we re-exercise load_records here against the same fixture
    # distill() consumed, then confirm the template rendered with the
    # actual readme content.
    from coaxer.records import load_records

    records = load_records(FIXTURE)
    by_id = {r.id: r for r in records}
    assert "awesome-skills" in by_id["0001"].inputs["readme"]

    out = tmp_path / "out"
    distill(FIXTURE, out, optimizer=None)
    p = CoaxedPrompt(out)
    rendered = p(**by_id["0001"].inputs)
    assert "awesome-skills" in rendered
    assert str(by_id["0001"].inputs["stars"]) in rendered


def test_binary_sibling_survives_distill_and_render(tmp_path: Path) -> None:
    """Byte-valued inputs should pass through the pipeline unchanged and
    render without crashing Jinja."""
    labels = tmp_path / "labels"
    rec = labels / "0001"
    rec.mkdir(parents=True)
    # Minimal PNG magic bytes + junk -- not valid UTF-8, forces the bytes path.
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00rest"
    (rec / "logo.png").write_bytes(png_bytes)
    (rec / "record.json").write_text(
        json.dumps({"id": "0001", "inputs": {"logo": "logo.png"}, "output": "yes"})
    )

    from coaxer.records import load_records

    records = load_records(labels)
    assert records[0].inputs["logo"] == png_bytes

    out = tmp_path / "out"
    distill(labels, out, optimizer=None)
    p = CoaxedPrompt(out)
    rendered = p(logo=png_bytes)
    # Jinja str()-coerces bytes; the point is that the pipeline accepted
    # the binary input without raising.
    assert "PNG" in rendered or "b'" in rendered


def test_history_jsonl_is_append_only_across_invocations(tmp_path: Path) -> None:
    out = tmp_path / "out"
    distill(FIXTURE, out, optimizer=None)
    distill(FIXTURE, out, optimizer=None)
    distill(FIXTURE, out, optimizer=None)

    lines = (out / "history.jsonl").read_text().strip().splitlines()
    assert len(lines) == 3
    for line in lines:
        entry = json.loads(line)
        assert "compiled_at" in entry
        assert entry["example_count"] == 3


def test_dspy_json_is_absent_when_optimizer_is_none(tmp_path: Path) -> None:
    out = tmp_path / "out"
    distill(FIXTURE, out, optimizer=None)
    assert not (out / "dspy.json").exists()
