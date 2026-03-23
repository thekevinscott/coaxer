"""TUI for labeling examples interactively.

Launched via `karat label <input.json> --output <output.json>`.
The agent writes unlabeled examples to a JSON file, the user labels them in this TUI,
and the TUI writes labeled results back for the agent to pick up.

Input JSON format::

    {
      "label_field": "is_collection",
      "labels": ["true", "false"],
      "display_fields": ["repo_name", "description"],
      "examples": [
        {"repo_name": "foo/bar", "description": "A curated collection", "id": "1"},
        ...
      ]
    }

Output JSON: same structure with a "label" key added to each example.

For <=9 labels, number keys (1-9) assign labels directly.
For >9 labels, press Enter to open a searchable filter, type to narrow, Enter to select.
"""

import json
import sys
from pathlib import Path
from typing import ClassVar

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Input, OptionList, Static
from textual.widgets.option_list import Option

MAX_NUMBER_KEY_LABELS = 9


class LabelApp(App):
    """Interactive labeling TUI. Presents examples in a table, user assigns labels."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit_and_save", "Save & quit"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("s", "skip", "Skip"),
        Binding("u", "unlabel", "Clear label"),
    ]

    CSS = """
    Screen { layout: vertical; }
    #status { height: 1; dock: top; padding: 0 1; }
    #detail { height: auto; max-height: 40%; padding: 1 2; border: solid $primary; }
    DataTable { height: 1fr; }
    #search-panel { height: auto; max-height: 50%; dock: bottom; padding: 1 2; border: solid $accent; }
    #label-search { margin-bottom: 1; }
    #label-options { height: auto; max-height: 10; }
    """

    current_row: reactive[int] = reactive(0)
    _search_mode: reactive[bool] = reactive(False)

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.input_path = input_path
        self.output_path = output_path

        data = json.loads(input_path.read_text())
        self.label_field: str = data["label_field"]
        self.labels: list[str] = data["labels"]
        self.display_fields: list[str] = data["display_fields"]
        self.examples: list[dict] = data["examples"]
        self.assigned: dict[int, str | None] = {}
        self._use_number_keys = len(self.labels) <= MAX_NUMBER_KEY_LABELS

        # Load existing output if resuming
        if output_path.exists():
            existing = json.loads(output_path.read_text())
            for i, ex in enumerate(existing.get("examples", [])):
                if "label" in ex and ex["label"] is not None:
                    self.assigned[i] = ex["label"]

        # Add number-key bindings only for small label sets
        if self._use_number_keys:
            for i, label in enumerate(self.labels):
                key = str(i + 1)
                self._bindings.bind(
                    key, f"label_{i}", f"[{key}] {label}", show=True
                )

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="status")
        yield DataTable(id="table", cursor_type="row")
        yield Static(id="detail")
        with Vertical(id="search-panel"):
            yield Input(id="label-search", placeholder="Type to filter labels...")
            yield OptionList(id="label-options")
        yield Footer()

    def on_mount(self) -> None:
        # Hide search panel initially
        self.query_one("#search-panel").display = False
        table = self.query_one("#table", DataTable)
        table.add_column("#", key="idx")
        table.add_column("Label", key="label")
        for field in self.display_fields:
            table.add_column(field, key=field)

        for i, ex in enumerate(self.examples):
            label_display = self.assigned.get(i, "")
            row = [str(i + 1), label_display or "---"]
            for field in self.display_fields:
                val = str(ex.get(field, ""))
                max_col_width = 60
                if len(val) > max_col_width:
                    val = val[: max_col_width - 3] + "..."
                row.append(val)
            table.add_row(*row, key=str(i))

        self._update_status()
        self._update_detail()

    def _update_status(self) -> None:
        labeled = sum(1 for v in self.assigned.values() if v is not None)
        total = len(self.examples)
        label_counts = {}
        for v in self.assigned.values():
            if v is not None:
                label_counts[v] = label_counts.get(v, 0) + 1
        counts_str = " | ".join(f"{k}: {v}" for k, v in sorted(label_counts.items()))
        status = f"Labeled: {labeled}/{total}"
        if counts_str:
            status += f"  ({counts_str})"
        if self._use_number_keys:
            keys = " ".join(f"[{i + 1}]={label}" for i, label in enumerate(self.labels))
            status += f"  |  Keys: {keys}  [s]=skip  [u]=clear  [q]=save & quit"
        else:
            status += f"  |  [Enter]=search labels  [s]=skip  [u]=clear  [q]=save & quit"
        self.query_one("#status", Static).update(status)

    def _update_detail(self) -> None:
        """Show full content of the currently selected example."""
        table = self.query_one("#table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.examples):
            ex = self.examples[table.cursor_row]
            lines = []
            for field in self.display_fields:
                val = str(ex.get(field, ""))
                lines.append(f"[bold]{field}:[/bold] {val}")
            current_label = self.assigned.get(table.cursor_row)
            if current_label:
                lines.append(f"\n[bold]Label:[/bold] {current_label}")
            self.query_one("#detail", Static).update("\n".join(lines))

    @on(DataTable.RowHighlighted)
    def _on_cursor_moved(self) -> None:
        self._update_detail()

    @on(DataTable.RowSelected)
    def _on_row_selected(self) -> None:
        if not self._use_number_keys:
            self._open_search()

    def _apply_label(self, label: str | None) -> None:
        table = self.query_one("#table", DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx >= len(self.examples):
            return

        self.assigned[row_idx] = label
        display = label or "---"
        table.update_cell(str(row_idx), "label", display)
        self._update_status()

        # Auto-advance to next unlabeled
        for offset in range(1, len(self.examples)):
            next_idx = (row_idx + offset) % len(self.examples)
            if next_idx not in self.assigned or self.assigned[next_idx] is None:
                table.move_cursor(row=next_idx)
                return
        # All labeled
        table.move_cursor(row=min(row_idx + 1, len(self.examples) - 1))

    def _save(self) -> None:
        output = {
            "label_field": self.label_field,
            "labels": self.labels,
            "display_fields": self.display_fields,
            "examples": [],
        }
        for i, ex in enumerate(self.examples):
            labeled_ex = {**ex, "label": self.assigned.get(i)}
            output["examples"].append(labeled_ex)
        self.output_path.write_text(json.dumps(output, indent=2))

    # -- Search mode for large label sets --

    def _open_search(self) -> None:
        self._search_mode = True
        panel = self.query_one("#search-panel")
        panel.display = True
        search_input = self.query_one("#label-search", Input)
        search_input.value = ""
        self._update_search_options("")
        self.set_focus(search_input)

    def _close_search(self) -> None:
        self._search_mode = False
        panel = self.query_one("#search-panel")
        panel.display = False
        self.query_one("#table", DataTable).focus()

    def _update_search_options(self, query: str) -> None:
        option_list = self.query_one("#label-options", OptionList)
        option_list.clear_options()
        q = query.lower()
        for label in self.labels:
            if not q or q in label.lower():
                option_list.add_option(Option(label, id=label))
        if option_list.option_count > 0:
            option_list.highlighted = 0

    @on(Input.Changed, "#label-search")
    def _on_search_changed(self, event: Input.Changed) -> None:
        self._update_search_options(event.value)

    @on(Input.Submitted, "#label-search")
    def _on_search_submitted(self, event: Input.Submitted) -> None:
        """Enter in search input: select the highlighted option."""
        option_list = self.query_one("#label-options", OptionList)
        if option_list.option_count > 0:
            highlighted = option_list.highlighted
            idx = highlighted if highlighted is not None else 0
            option = option_list.get_option_at_index(idx)
            self._apply_label(str(option.prompt))
            self._close_search()

    @on(OptionList.OptionSelected, "#label-options")
    def _on_option_selected(self, event: OptionList.OptionSelected) -> None:
        self._apply_label(str(event.option.prompt))
        self._close_search()

    # -- Actions --

    def action_open_search(self) -> None:
        self._open_search()

    def action_quit_and_save(self) -> None:
        self._save()
        self.exit()

    def action_cursor_down(self) -> None:
        if not self._search_mode:
            self.query_one("#table", DataTable).action_cursor_down()

    def action_cursor_up(self) -> None:
        if not self._search_mode:
            self.query_one("#table", DataTable).action_cursor_up()

    def action_skip(self) -> None:
        if not self._search_mode:
            self._apply_label(None)

    def action_unlabel(self) -> None:
        if not self._search_mode:
            self._apply_label(None)

    def on_key(self, event) -> None:
        if self._search_mode:
            if event.key == "escape":
                self._close_search()
                event.prevent_default()
                event.stop()
            elif event.key == "down":
                self.query_one("#label-options", OptionList).action_cursor_down()
                event.prevent_default()
                event.stop()
            elif event.key == "up":
                self.query_one("#label-options", OptionList).action_cursor_up()
                event.prevent_default()
                event.stop()

    # Label actions are registered dynamically in __init__ via _bindings.bind().
    # Textual resolves action_label_0, action_label_1, etc.
    def __getattr__(self, name: str):
        if name.startswith("action_label_"):
            idx = int(name.removeprefix("action_label_"))
            if idx < len(self.labels):
                def _do_label():
                    self._apply_label(self.labels[idx])
                return _do_label
        raise AttributeError(name)


def run_label_tui(input_path: str, output_path: str) -> None:
    """Entry point for the label TUI."""
    inp = Path(input_path)
    if not inp.exists():
        print(f"Input file not found: {inp}", file=sys.stderr)
        sys.exit(1)

    out = Path(output_path)
    app = LabelApp(input_path=inp, output_path=out)
    app.run()
