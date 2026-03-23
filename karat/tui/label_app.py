"""LabelApp - the Textual application for interactive labeling."""

import json
from pathlib import Path
from typing import ClassVar

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Input, OptionList, Static
from textual.widgets.option_list import Option

MAX_NUMBER_KEY_LABELS = 9


def _display_width(s: str) -> int:
    """Approximate display width accounting for wide (CJK) characters."""
    import unicodedata

    width = 0
    for ch in s:
        eaw = unicodedata.east_asian_width(ch)
        width += 2 if eaw in ("W", "F") else 1
    return width


def _truncate_to_width(s: str, max_width: int) -> str:
    """Truncate a string to fit within max_width display columns."""
    import unicodedata

    width = 0
    for i, ch in enumerate(s):
        eaw = unicodedata.east_asian_width(ch)
        char_w = 2 if eaw in ("W", "F") else 1
        if width + char_w > max_width - 3:
            return s[:i] + "..."
        width += char_w
    return s


def _make_cell_value(val: str, max_width: int = 60) -> str | Text:
    """Create a cell value, making URLs clickable and truncating wide text."""
    if val.startswith(("http://", "https://")):
        display = _truncate_to_width(val, max_width)
        t = Text(display)
        t.stylize(f"link {val}")
        return t
    if _display_width(val) > max_width:
        return _truncate_to_width(val, max_width)
    return val


def _parse_input(data: dict) -> tuple[list[dict], list[dict]]:
    """Parse input JSON into (fields, examples).

    Supports three formats:
    1. Unified: {"fields": [...], "examples": [...]}
    2. Split: {"label_fields": [...], "display_fields": [...], "examples": [...]}
    3. Legacy: {"label_field": "...", "labels": [...], "display_fields": [...], ...}

    Returns normalized fields list where each field has:
      name, table (bool), detail (bool), labels (list|None)
    """
    examples = data["examples"]

    if "fields" in data:
        fields = []
        for f in data["fields"]:
            fields.append({
                "name": f["name"],
                "table": f.get("table", True),
                "detail": f.get("detail", True),
                "labels": f.get("labels"),
            })
        return fields, examples

    # Legacy formats -> convert to unified
    if "label_fields" in data:
        label_fields = data["label_fields"]
    else:
        label_fields = [
            {"name": data["label_field"], "labels": data["labels"]},
        ]
    display_fields = data.get("display_fields", [])

    fields = []
    for df in display_fields:
        fields.append({
            "name": df, "table": True, "detail": True, "labels": None,
        })
    for lf in label_fields:
        fields.append({
            "name": lf["name"],
            "table": True,
            "detail": True,
            "labels": lf["labels"],
        })
    return fields, examples


def _extract_labels(
    examples: list[dict],
    label_fields: list[dict],
    assigned: dict[tuple[int, str], str | None],
) -> None:
    """Extract label values from examples into the assigned dict."""
    for i, ex in enumerate(examples):
        for field in label_fields:
            fname = field["name"]
            if fname in ex and ex[fname] is not None:
                assigned[(i, fname)] = ex[fname]


def _load_assigned(
    examples: list[dict],
    label_fields: list[dict],
    output_path: Path,
) -> dict[tuple[int, str], str | None]:
    """Build the assigned dict from examples and optional output file."""
    assigned: dict[tuple[int, str], str | None] = {}

    _extract_labels(examples, label_fields, assigned)

    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text())
        except (json.JSONDecodeError, ValueError):
            existing = None
        if isinstance(existing, dict):
            _extract_labels(
                existing.get("examples", []), label_fields, assigned,
            )
            # Backward compat: old format uses "label" key
            if len(label_fields) == 1:
                fname = label_fields[0]["name"]
                for i, ex in enumerate(existing.get("examples", [])):
                    if "label" in ex and ex["label"] is not None:
                        assigned[(i, fname)] = ex["label"]

    return assigned


class LabelApp(App):
    """Interactive labeling TUI."""

    CSS_PATH = "label_app.tcss"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit_and_save", "Save & quit"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("s", "skip", "Skip"),
        Binding("u", "unlabel", "Clear label"),
        Binding("tab", "next_label_col", "Next field", show=False),
        Binding("shift+tab", "prev_label_col", "Prev field", show=False),
    ]

    current_row: reactive[int] = reactive(0)
    _search_mode: reactive[bool] = reactive(False)
    _search_field: str = ""

    def __init__(self, input_path: Path, output_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.input_path = input_path
        self.output_path = output_path

        data = json.loads(input_path.read_text())
        self._fields, self.examples = _parse_input(data)

        # Derived views
        self.label_fields = [f for f in self._fields if f.get("labels")]
        self._table_fields = [f for f in self._fields if f.get("table", True)]
        self._detail_fields = [
            f for f in self._fields if f.get("detail", True)
        ]

        self.labels: list[str] = (
            self.label_fields[0]["labels"] if self.label_fields else []
        )
        self._use_number_keys = (
            len(self.label_fields) == 1
            and len(self.labels) <= MAX_NUMBER_KEY_LABELS
        )
        self.assigned = _load_assigned(
            self.examples, self.label_fields, output_path,
        )

        if self._use_number_keys:
            for i, label in enumerate(self.labels):
                key = str(i + 1)
                self._bindings.bind(
                    key, f"label_{i}", f"[{key}] {label}", show=True,
                )

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="status")
        cursor = "cell" if len(self.label_fields) > 1 else "row"
        yield DataTable(id="table", cursor_type=cursor)
        yield Static(id="detail")
        with Vertical(id="search-panel"):
            yield Input(
                id="label-search", placeholder="Type to filter labels...",
            )
            yield OptionList(id="label-options")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search-panel").display = False
        table = self.query_one("#table", DataTable)
        table.add_column("#", key="idx")
        for f in self._table_fields:
            if f.get("labels"):
                key = "label" if len(self.label_fields) == 1 else f"label:{f['name']}"
                table.add_column(f["name"], key=key)
            else:
                table.add_column(f["name"], key=f["name"])

        for i, ex in enumerate(self.examples):
            row = [str(i + 1)]
            for f in self._table_fields:
                if f.get("labels"):
                    row.append(
                        self.assigned.get((i, f["name"]), "") or "---",
                    )
                else:
                    val = str(ex.get(f["name"], ""))
                    row.append(_make_cell_value(val))
            table.add_row(*row, key=str(i))

        self._update_status()
        self._update_detail()

    # -- Status and detail --

    def _active_field_name(self) -> str:
        return self.label_fields[0]["name"]

    def _update_status(self) -> None:
        parts = []
        for field in self.label_fields:
            fname = field["name"]
            labeled = sum(
                1
                for i in range(len(self.examples))
                if self.assigned.get((i, fname)) is not None
            )
            parts.append(f"{fname}: {labeled}/{len(self.examples)}")
        status = " | ".join(parts)
        if self._use_number_keys:
            keys = " ".join(
                f"[{i + 1}]={label}"
                for i, label in enumerate(self.labels)
            )
            status += (
                f"  |  Keys: {keys}  [s]=skip  [u]=clear  [q]=save & quit"
            )
        else:
            status += (
                "  |  [Enter]=search labels  [s]=skip  [u]=clear"
                "  [q]=save & quit"
            )
        self.query_one("#status", Static).update(status)

    def _update_detail(self) -> None:
        table = self.query_one("#table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(
            self.examples
        ):
            ex = self.examples[table.cursor_row]
            lines = []
            for f in self._detail_fields:
                fname = f["name"]
                if f.get("labels"):
                    current = self.assigned.get((table.cursor_row, fname))
                    if current:
                        lines.append(f"[bold]{fname}:[/bold] {current}")
                else:
                    val = str(ex.get(fname, ""))
                    if val:
                        lines.append(f"[bold]{fname}:[/bold] {val}")

            self.query_one("#detail", Static).update("\n".join(lines))

    # -- Events --

    @on(DataTable.RowHighlighted)
    def _on_cursor_moved(self) -> None:
        self._update_detail()

    @on(DataTable.RowSelected)
    def _on_row_selected(self) -> None:
        if not self._use_number_keys:
            self._open_search()

    @on(DataTable.CellSelected)
    def _on_cell_selected(self, event: DataTable.CellSelected) -> None:
        if len(self.label_fields) <= 1:
            return
        col_key = str(event.cell_key.column_key)
        if col_key.startswith("label:"):
            field_name = col_key.removeprefix("label:")
            self._open_search_for_field(field_name)

    @on(DataTable.CellHighlighted)
    def _on_cell_highlighted(self) -> None:
        self._update_detail()

    # -- Labeling --

    def _apply_label(self, label: str | None) -> None:
        table = self.query_one("#table", DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx >= len(self.examples):
            return
        fname = self._active_field_name()
        self.assigned[(row_idx, fname)] = label
        display = label or "---"
        col_key = (
            f"label:{fname}" if len(self.label_fields) > 1 else "label"
        )
        table.update_cell(str(row_idx), col_key, display)
        self._update_status()
        self._auto_advance()

    def _auto_advance(self) -> None:
        table = self.query_one("#table", DataTable)
        row_idx = table.cursor_row
        if row_idx is None:
            return
        fname = self._active_field_name()
        for offset in range(1, len(self.examples)):
            next_idx = (row_idx + offset) % len(self.examples)
            key = (next_idx, fname)
            if key not in self.assigned or self.assigned[key] is None:
                table.move_cursor(row=next_idx)
                return
        table.move_cursor(row=min(row_idx + 1, len(self.examples) - 1))

    def _save(self) -> None:
        output = {
            "fields": self._fields,
            "examples": [],
        }
        for i, ex in enumerate(self.examples):
            labeled_ex = {**ex}
            for field in self.label_fields:
                fname = field["name"]
                labeled_ex[fname] = self.assigned.get((i, fname))
            output["examples"].append(labeled_ex)
        self.output_path.write_text(json.dumps(output, indent=2))

    # -- Search mode --

    def _open_search_for_field(self, field_name: str) -> None:
        self._search_field = field_name
        self._search_mode = True
        panel = self.query_one("#search-panel")
        panel.display = True
        search_input = self.query_one("#label-search", Input)
        search_input.value = ""
        self._update_search_options("")
        self.set_focus(search_input)

    def _open_search(self) -> None:
        self._open_search_for_field(self._active_field_name())

    def _close_search(self) -> None:
        self._search_mode = False
        self.query_one("#search-panel").display = False
        self.query_one("#table", DataTable).focus()

    def _search_labels(self) -> list[str]:
        field_name = self._search_field or self._active_field_name()
        for f in self.label_fields:
            if f["name"] == field_name:
                return f["labels"]
        return self.labels

    def _update_search_options(self, query: str) -> None:
        option_list = self.query_one("#label-options", OptionList)
        option_list.clear_options()
        q = query.lower()
        for label in self._search_labels():
            if not q or q in label.lower():
                option_list.add_option(Option(label, id=label))
        if option_list.option_count > 0:
            option_list.highlighted = 0

    @on(Input.Changed, "#label-search")
    def _on_search_changed(self, event: Input.Changed) -> None:
        self._update_search_options(event.value)

    @on(Input.Submitted, "#label-search")
    def _on_search_submitted(self) -> None:
        option_list = self.query_one("#label-options", OptionList)
        if option_list.option_count > 0:
            highlighted = option_list.highlighted
            idx = highlighted if highlighted is not None else 0
            option = option_list.get_option_at_index(idx)
            self._apply_label_to_field(str(option.prompt))
            self._close_search()

    @on(OptionList.OptionSelected, "#label-options")
    def _on_option_selected(
        self, event: OptionList.OptionSelected,
    ) -> None:
        self._apply_label_to_field(str(event.option.prompt))
        self._close_search()

    def _apply_label_to_field(self, label: str) -> None:
        field_name = self._search_field or self._active_field_name()
        table = self.query_one("#table", DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx >= len(self.examples):
            return
        self.assigned[(row_idx, field_name)] = label
        col_key = (
            f"label:{field_name}" if len(self.label_fields) > 1 else "label"
        )
        table.update_cell(str(row_idx), col_key, label)
        self._update_status()
        self._auto_advance()

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

    def action_next_label_col(self) -> None:
        if not self._search_mode and len(self.label_fields) > 1:
            self.query_one("#table", DataTable).action_cursor_right()

    def action_prev_label_col(self) -> None:
        if not self._search_mode and len(self.label_fields) > 1:
            self.query_one("#table", DataTable).action_cursor_left()

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
                opts = self.query_one("#label-options", OptionList)
                opts.action_cursor_down()
                event.prevent_default()
                event.stop()
            elif event.key == "up":
                opts = self.query_one("#label-options", OptionList)
                opts.action_cursor_up()
                event.prevent_default()
                event.stop()
        elif len(self.label_fields) > 1:
            if event.key == "tab":
                self.query_one("#table", DataTable).action_cursor_right()
                event.prevent_default()
                event.stop()
            elif event.key == "shift+tab":
                self.query_one("#table", DataTable).action_cursor_left()
                event.prevent_default()
                event.stop()

    def __getattr__(self, name: str):
        if name.startswith("action_label_"):
            idx = int(name.removeprefix("action_label_"))
            if idx < len(self.labels):

                def _do_label():
                    self._apply_label(self.labels[idx])

                return _do_label
        raise AttributeError(name)
