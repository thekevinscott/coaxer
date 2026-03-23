"""TUI for labeling examples interactively.

Launched via ``karat label <input.json> --output <output.json>``.

An agent writes unlabeled (or pre-labeled) examples to a JSON file, the user
labels/corrects them in this TUI, and the agent reads the results back.

See ``karat.tui.label_app`` for the full format documentation and
``README.md`` for usage examples.
"""

import sys
from pathlib import Path

from .label_app import LabelApp

__all__ = ["LabelApp", "run_label_tui"]


def run_label_tui(input_path: str, output_path: str) -> None:
    """Entry point for the label TUI."""
    inp = Path(input_path)
    if not inp.exists():
        print(f"Input file not found: {inp}", file=sys.stderr)
        sys.exit(1)

    out = Path(output_path)
    app = LabelApp(input_path=inp, output_path=out)
    app.run()
