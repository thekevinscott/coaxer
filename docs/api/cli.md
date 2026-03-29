# CLI

karat provides a command-line interface with two subcommands.

## `karat install`

Copies bundled skills into `.claude/skills/` in the current project directory.

```bash
uvx karat install
```

Currently installs the `/optimize` skill. Each skill is a `SKILL.md` file that Claude Code loads automatically.

## `karat label`

Launches the labeling TUI for interactive example labeling.

```bash
karat label <input.json> --output <output.json>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<input.json>` | Yes | Path to the input JSON file containing fields and examples. |
| `--output`, `-o` | Yes | Path where labeled output will be saved. |

Both paths should be absolute. The `--output` flag is required -- the command exits with an error if omitted.

See [Labeling TUI](../guide/labeling-tui.md) for the input format and interaction reference.
