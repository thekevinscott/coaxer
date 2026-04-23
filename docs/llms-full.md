# coaxer -- Complete Reference (LLM-friendly)

This is the full coaxer documentation on a single page, designed for consumption by language models.

## What is coaxer?

coaxer is an evals-first prompt optimization library for Python. It provides:

1. **AgentLM**: A DSPy language model that routes LLM calls through the Anthropic Agent SDK (Claude Code). No API key needed.
2. **load_predict**: Load optimized DSPy programs from JSON, with fallback to unoptimized.
3. **Labeling TUI**: A terminal interface for human-in-the-loop example labeling.
4. **/optimize skill**: A Claude Code skill orchestrating the full workflow: signature -> data -> sampling -> labeling -> optimization -> compiled program.

The core idea: the prompt is a build artifact. Your labeled examples are the source of truth. When you want a better prompt, add more examples and regenerate.

## Installation

```bash
uv add coaxer
```

With caching support:

```bash
uv add "coaxer[cache]"
```

Install the /optimize Claude Code skill:

```bash
uvx coaxer install
```

Requirements: Python >= 3.14, Claude Code CLI installed and authenticated, DSPy >= 2.6.

## AgentLM

A DSPy `BaseLM` subclass. Each `forward()` call spawns a Claude Code subprocess via `claude_agent_sdk.query()`.

### Constructor

```python
AgentLM(
    model: str = "claude-agent-sdk",    # DSPy tracking identifier
    model_type: str = "chat",
    max_tokens: int = 4096,
    cache: Cachetta | None = None,      # Optional response cache
    **kwargs,                           # Forwarded to ClaudeAgentOptions
)
```

### Common kwargs (ClaudeAgentOptions)

- `tools: list` -- Tools available. Pass `[]` for classification/structured output.
- `allowed_tools: list[str]` -- Tool allowlist (e.g., `["Read", "Glob"]`).
- `disallowed_tools: list[str]` -- Tool denylist.
- `max_turns: int` -- Maximum agentic turns.
- `env: dict[str, str]` -- Environment variables for the subprocess.

### Methods

- `forward(prompt=None, messages=None, **kwargs) -> CompletionResponse` -- Sync forward pass. String prompt or OpenAI-style messages. Per-call kwargs override constructor kwargs.
- `aforward(prompt=None, messages=None, **kwargs) -> CompletionResponse` -- Async version.
- `copy(**kwargs) -> AgentLM` -- New instance with updated kwargs.
- `inspect_history(n=1) -> list[dict]` -- Last n prompt/response pairs.

### Usage

```python
import dspy
from coaxer import AgentLM

lm = AgentLM(tools=[])
dspy.configure(lm=lm)

class Classify(dspy.Signature):
    """Classify a GitHub repo as a curated collection or an organic project."""
    readme: str = dspy.InputField()
    is_collection: bool = dspy.OutputField()

classify = dspy.Predict(Classify)
result = classify(readme="# awesome-skills\n\n500+ curated Claude skills")
```

## load_predict

```python
load_predict(signature: type, path: str | Path | None = None) -> dspy.Predict
```

Creates a `dspy.Predict(signature)`. If `path` is provided and exists, loads the optimized program. If path doesn't exist, logs a warning and returns unoptimized. If path is None, returns unoptimized.

```python
from coaxer import load_predict
classify = load_predict(ClassifyRepo, path="data/optimized.json")
```

## CLI

### coaxer install

```bash
uvx coaxer install
```

Copies bundled skills into `.claude/skills/` in the current directory.

### coaxer label

```bash
coaxer label <input.json> --output <output.json>
```

Both the input path and `--output` flag are required. Launches the labeling TUI.

## Labeling TUI Input Format

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

### Field Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | string | required | Key matching example objects |
| `labels` | string[] | omit | Allowed values. Makes the field editable. Omit entirely for read-only. |
| `table` | bool | `true` | Show as a table column |
| `detail` | bool | `true` | Show in detail panel |

Field ordering matters -- fields appear in declared order.

### Pre-populated Labels

Include the label key in the example object for a pre-populated default. Omit the key entirely (not null, not empty string) for blank.

```json
{"text": "I love this", "sentiment": "positive"}
{"text": "It was okay"}
```

### URLs

URLs in display fields render as clickable links in the table.

### Interaction Modes

- **Single field, <= 9 labels**: Number keys (1-9) assign directly
- **Single field, > 9 labels**: Enter opens searchable filter
- **Multiple editable fields**: Spreadsheet-style cell cursor, Enter opens search, Tab/Shift+Tab between columns

### Keybindings

- `j`/Down, `k`/Up: Navigate rows
- `1`-`9`: Assign label (single-field, <= 9 labels)
- Enter: Open searchable filter
- Tab/Shift+Tab: Next/prev label column (multi-field)
- `u`: Clear cell
- `Shift+U`: Clear row
- `s`: Skip example
- `q`: Save and quit

### Output Format

Same structure as input. Label values are strings or `null` (skipped). Exclude null examples from training.

### Multiple Editable Fields Example

```json
{
  "fields": [
    {"name": "url"},
    {"name": "language_reasoning", "table": false},
    {"name": "language", "labels": ["Python", "JavaScript", "Rust", "Go"]},
    {"name": "is_collection_reasoning", "table": false},
    {"name": "is_collection", "labels": ["true", "false"]}
  ],
  "examples": [
    {"url": "https://github.com/example/repo"}
  ]
}
```

### Legacy Formats

Also supported: `label_fields` + `display_fields` arrays, or `label_field` (string) + `labels` (array) + `display_fields`.

## /optimize Skill Workflow

1. **Read Signature**: User provides a DSPy Signature (file path or inline)
2. **Get Data**: Accept any format (CSV, JSON, JSONL, Parquet, SQL, etc.)
3. **Smart Sampling**: LM classification pass, stratify into positive/negative/ambiguous, present ambiguous first
4. **Collect Labels**: Write JSON, user runs `coaxer label` in separate terminal
5. **Optimize**: Split train/val, configure AgentLM(tools=[]), run BootstrapFewShot or MIPROv2
6. **Save**: Compiled program as JSON with instruction, demos, metadata

## Caching

```python
from cachetta import Cachetta
from coaxer import AgentLM

cache = Cachetta(path=lambda prompt, **kw: f"cache/{prompt}.pkl", duration="7d")
lm = AgentLM(cache=cache, tools=[])
```

Wraps the internal query function. Cache key derived from prompt. Install: `uv add "coaxer[cache]"`.
