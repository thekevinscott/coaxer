# CLI

_Online: <https://thekevinscott.github.io/coaxer/api/cli/>_

Coaxer exposes a single command: `coax`.

## `coax`

Compiles a label folder into a reusable prompt artifact.

```bash
coax <labels-dir> --out <prompts-dir> [--optimizer {none,gepa}] [--output-name NAME]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `<labels-dir>` | Yes | Path to the directory-per-record label folder. |
| `--out` | Yes | Output folder for `prompt.jinja`, `meta.json`, `dspy.json`, `history.jsonl`. Created if missing. |
| `--optimizer` | No | `none` (default) emits a schema-derived template without network. `gepa` runs DSPy 3's GEPA pass and writes `dspy.json`. |
| `--output-name` | No | Name of the predicted output field in the rendered template. Defaults to `output`. |

### Output

Four files land in `--out`:

| File | When | Purpose |
|---|---|---|
| `prompt.jinja` | Always | The Jinja2 template with `{{ field }}` slots. |
| `meta.json` | Always | `compiled_at`, `optimizer`, `example_count`, `label_hash`, and the field schema. |
| `dspy.json` | `--optimizer gepa` only | DSPy program state for future warm-start / inspection. |
| `history.jsonl` | Always | One line per compile; same shape as `meta.json`. |

### Example

```bash
coax labels/repo-classification --out prompts/repo-classification --optimizer gepa
```

Consume the output with [`CoaxedPrompt`](coaxed-prompt.md).
