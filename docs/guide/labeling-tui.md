# Labeling TUI

Interactive terminal interface for human-in-the-loop example labeling. An agent writes examples to a JSON file, the user labels them in the TUI, and the agent reads results back.

## Launch

```bash
coaxer label /path/to/input.json --output /path/to/output.json
```

Both `--output` (or `-o`) and the input path are required. Use absolute paths.

## Input Format

```json
{
  "fields": [
    {"name": "url"},
    {"name": "description"},
    {"name": "reasoning", "table": false},
    {"name": "is_collection", "labels": ["true", "false"]}
  ],
  "examples": [
    {
      "url": "https://github.com/vinta/awesome-python",
      "description": "A curated list of awesome Python frameworks",
      "reasoning": "YES: 'curated list' is a collection marker",
      "is_collection": "true"
    },
    {
      "url": "https://github.com/pallets/flask",
      "description": "The Python micro framework for building web applications"
    }
  ]
}
```

### Field Definitions

Each field in the `fields` array has:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | string | required | Key matching example objects |
| `labels` | string[] | omit | Allowed values. Makes the field **editable**. Omit entirely for read-only display fields. |
| `table` | bool | `true` | Show as a table column |
| `detail` | bool | `true` | Show in detail panel below the table |

**Field ordering matters.** Fields appear in the table and detail panel in the order declared. Put reasoning fields right before or after their label field.

### Pre-populated Labels

If an example object includes a value for a label field, it appears as an editable default:

```json
{"text": "I love this", "sentiment": "positive"}
```

To leave a label blank for the user to fill in, **omit the key entirely** from the example object:

```json
{"text": "I love this"}
```

Do not use `null` or empty string -- omit the key.

### URLs

URLs in display fields are automatically rendered as clickable links in the table (truncated for display, full URL preserved).

## Interaction Modes

The TUI automatically selects an interaction mode based on the data:

### Single field, <= 9 labels

Number keys (1-9) assign labels directly. Press the corresponding number to label the current row.

### Single field, > 9 labels

Press Enter to open a searchable filter. Type to narrow the list, press Enter to select. Arrow keys navigate the filtered list.

### Multiple editable fields

Spreadsheet-style cell cursor. Enter on a label cell opens search for that field's labels. Tab/Shift+Tab move between label columns. Arrow keys navigate cells.

## Keybindings

| Key | Action |
|-----|--------|
| `j` / Down | Next row |
| `k` / Up | Previous row |
| `1`-`9` | Assign label (single-field mode with <= 9 labels) |
| Enter | Open searchable filter for current field |
| Tab | Next label column (multi-field mode) |
| Shift+Tab | Previous label column (multi-field mode) |
| `u` | Clear current cell |
| `Shift+U` | Clear entire row |
| `s` | Skip current example |
| `q` | Save and quit |

## Output Format

The output JSON has the same structure as input (`fields` + `examples`), with label values filled in:

```json
{
  "fields": [...],
  "examples": [
    {"url": "...", "description": "...", "is_collection": "true"},
    {"url": "...", "description": "...", "is_collection": "false"},
    {"url": "...", "description": "...", "is_collection": null}
  ]
}
```

- Label values are strings matching one of the `labels` options
- `null` means the user skipped that example -- exclude from training

## Multiple Editable Fields

For signatures with multiple output fields:

```json
{
  "fields": [
    {"name": "url"},
    {"name": "language_reasoning", "table": false},
    {"name": "language", "labels": ["Python", "JavaScript", "Rust", "Go", "Java", "Other"]},
    {"name": "is_collection_reasoning", "table": false},
    {"name": "is_collection", "labels": ["true", "false"]}
  ],
  "examples": [
    {"url": "https://github.com/example/repo"}
  ]
}
```

Set `"table": false` on reasoning fields to keep the table compact -- they still show in the detail panel.

## Legacy Formats

The TUI also accepts older formats for backwards compatibility:

- **Split format**: `label_fields` + `display_fields` arrays
- **Simple format**: `label_field` (string) + `labels` (array) + `display_fields`

These are converted internally to the unified `fields` format.
