"""CLI entry point for coaxer."""

import argparse
import sys
from pathlib import Path

from coaxer.compiler import distill


def main() -> None:
    parser = argparse.ArgumentParser(prog="coaxer", description="Label examples, derive prompts.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_distill = sub.add_parser("distill", help="Compile a label folder into a reusable prompt.")
    p_distill.add_argument("labels", type=Path, help="Path to the label folder.")
    p_distill.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output folder for prompt.jinja + meta.json + history.jsonl.",
    )
    p_distill.add_argument(
        "--optimizer",
        choices=["gepa", "none"],
        default="none",
        help="Optimizer to run. `gepa` requires an API key; `none` emits a raw template.",
    )
    p_distill.add_argument(
        "--output-name",
        default="output",
        help="Name of the predicted field in the rendered template (default: output).",
    )

    args = parser.parse_args()

    if args.command == "distill":
        optimizer = None if args.optimizer == "none" else args.optimizer
        lm = _build_default_lm() if optimizer else None
        out = distill(
            args.labels,
            args.out,
            lm=lm,
            optimizer=optimizer,
            output_name=args.output_name,
        )
        print(f"Wrote prompt to {out}/prompt.jinja")
        return

    parser.print_help()
    sys.exit(1)


def _build_default_lm():
    from coaxer.lm import AgentLM

    return AgentLM()
