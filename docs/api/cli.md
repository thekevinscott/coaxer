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
| `--out` | Yes | Output folder for trained prompt. Created if missing. |
| `--optimizer` | No | `none` (default) emits a schema-derived template without network. `gepa` runs DSPy 3's GEPA pass. |
| `--output-name` | No | Name of the predicted output field in the rendered template. Defaults to `output`. |

### Example

```bash
coax labels/repo-classification --out prompts/repo-classification --optimizer gepa
```

Consume the output with [`CoaxedPrompt`](coaxed-prompt.md).
