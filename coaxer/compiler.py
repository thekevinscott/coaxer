"""Distill pipeline: label folder → compiled prompt artifact.

```
coaxer distill labels/foo --out prompts/foo
```

Reads records + schema, builds a DSPy signature, optionally runs an
optimizer (GEPA), renders a Jinja2 template, and writes
`prompt.jinja`, `meta.json`, `dspy.json` (if optimized), and appends
to `history.jsonl`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from coaxer.records import load_records
from coaxer.schema import Schema, infer_schema, load_schema
from coaxer.signature import build_signature

if TYPE_CHECKING:
    import dspy

_VALID_OPTIMIZERS = {None, "gepa"}


def distill(
    labels_dir: str | Path,
    out_dir: str | Path,
    *,
    lm: Any = None,
    optimizer: str | None = None,
    output_name: str = "output",
) -> Path:
    if optimizer not in _VALID_OPTIMIZERS:
        raise ValueError(f"Unknown optimizer: {optimizer!r}. Expected one of {_VALID_OPTIMIZERS}")

    labels = Path(labels_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records = load_records(labels)
    schema = load_schema(labels) or infer_schema(records)
    signature = build_signature(schema, output_name=output_name)

    program = _optimize(signature, records, output_name=output_name, lm=lm, optimizer=optimizer)

    template = _render_template(signature, schema)
    (out / "prompt.jinja").write_text(template)

    if program is not None:
        (out / "dspy.json").write_text(_dump_program(program))

    meta = {
        "compiled_at": datetime.now(UTC).isoformat(),
        "optimizer": optimizer,
        "example_count": len(records),
        "label_hash": _hash_labels(labels),
        "fields": {
            "inputs": {n: asdict(f) for n, f in schema.inputs.items()},
            "output": asdict(schema.output),
        },
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2))

    with (out / "history.jsonl").open("a") as f:
        f.write(json.dumps(meta) + "\n")

    return out


def _optimize(
    signature: type[dspy.Signature],
    records: list,
    *,
    output_name: str,
    lm: Any,
    optimizer: str | None,
) -> Any:
    if optimizer is None:
        return None
    if optimizer == "gepa":
        return _run_gepa(signature, records, output_name=output_name, lm=lm)
    raise ValueError(f"Unknown optimizer: {optimizer!r}")


def _run_gepa(
    signature: type[dspy.Signature],
    records: list,
    *,
    output_name: str,
    lm: Any,
) -> Any:
    import dspy

    if lm is None:
        raise ValueError("GEPA requires an `lm` argument (AgentLM, OpenAILM, or any dspy.LM)")

    program = dspy.Predict(signature)
    trainset = [
        dspy.Example(**r.inputs, **{output_name: r.output}).with_inputs(*r.inputs) for r in records
    ]

    def metric(example: Any, pred: Any, trace: Any = None) -> float:  # noqa: ARG001
        return 1.0 if getattr(pred, output_name, None) == getattr(example, output_name) else 0.0

    with dspy.context(lm=lm):
        optimizer = dspy.GEPA(metric=metric, auto="light")  # type: ignore[arg-type]
        return optimizer.compile(program, trainset=trainset)


def _render_template(signature: type[dspy.Signature], schema: Schema) -> str:
    instructions = signature.instructions or ""
    lines = [instructions.strip(), "", "Inputs:"]
    for name in schema.inputs:
        lines.append(f"- {name}: {{{{ {name} }}}}")
    lines.append("")
    lines.append("Respond with the predicted output.")
    return "\n".join(lines) + "\n"


def _dump_program(program: Any) -> str:
    if hasattr(program, "dump_state"):
        state = program.dump_state()
        return json.dumps(state, indent=2, default=str)
    return json.dumps({"repr": repr(program)}, indent=2)


def _hash_labels(labels_dir: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(labels_dir.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(labels_dir).as_posix().encode())
            h.update(b"\0")
            h.update(p.read_bytes())
    return h.hexdigest()[:16]
