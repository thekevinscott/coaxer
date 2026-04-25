# coaxer -- Complete Reference (LLM-friendly)

_Online: <https://thekevinscott.github.io/coaxer/llms-full/>_

Full coaxer documentation on a single page, designed for consumption by language models.

## What is coaxer?

Coaxer turns labeled examples into prompts. You label behavior you want, coaxer compiles it into a `prompt.jinja` template, you consume the template as a string at runtime.

The library provides:

1. **Label folder format** — one directory per record; `record.json` + sibling files for text/binary.
2. **`coax` CLI** — reads the folder, optionally runs DSPy 3 + GEPA optimization, writes a prompt artifact.
3. **`CoaxedPrompt`** — a `str` subclass that loads `prompt.jinja` and renders it via Jinja2 at call time.
4. **`AgentLM` / `OpenAILM`** — DSPy `BaseLM` backends for the optional compile-time optimizer (Claude via Agent SDK, or any OpenAI-compatible endpoint).

The prompt is a build artifact. Labeled examples are the source of truth.

## Installation

```bash
uv add coaxer
```

Requirements: Python >= 3.14, DSPy >= 3.0, Jinja2 >= 3.0. `AgentLM` additionally requires the Claude Code CLI installed and authenticated.

## Label folder format

```
labels/<name>/
  _schema.json              # optional
  0001/
    record.json
    readme.md               # sibling file referenced from record.json
  0002/
    record.json
    logo.png                # binary is fine
```

`record.json`:

```json
{
  "id": "0001",
  "inputs": {
    "readme": "readme.md",
    "stars": 521
  },
  "output": "true"
}
```

When a value names a file that exists in the record folder, the file's contents are substituted at compile time (UTF-8 text if decodable, raw bytes otherwise). Other values pass through.

`_schema.json` is optional. It adds field descriptions, types, and enum values:

```json
{
  "inputs": {
    "readme": {"desc": "Project README markdown"},
    "stars": {"desc": "GitHub star count", "type": "int"}
  },
  "output": {
    "desc": "Curated collection vs organic project",
    "type": "enum",
    "values": ["true", "false"]
  }
}
```

Supported types: `str`, `int`, `float`, `bool`, `bytes`, `enum` (with `values`). Without `_schema.json`, types are inferred from the first record.

## CLI

### `coax`

```bash
coax <labels-dir> --out <prompts-dir> [--optimizer {none,gepa}] [--output-name NAME]
```

- `<labels-dir>` — path to the label folder.
- `--out` — output folder (created if missing).
- `--optimizer` — `none` (default) emits schema-derived template with no network. `gepa` runs DSPy 3 GEPA, requires an LLM credential, writes `dspy.json`.
- `--output-name` — name of the predicted output field in the rendered template (default `output`).

Writes:

| File | When | Content |
|---|---|---|
| `prompt.jinja` | Always | Jinja2 template with `{{ field }}` slots. |
| `meta.json` | Always | `compiled_at`, `optimizer`, `example_count`, `label_hash`, schema. |
| `dspy.json` | `--optimizer gepa` | DSPy program state. |
| `history.jsonl` | Always | One line per compile. |

## `CoaxedPrompt`

```python
from coaxer import CoaxedPrompt

p = CoaxedPrompt("prompts/repo-classification", role="classifier")
filled = p(readme=new_readme, stars=1200)
```

- `CoaxedPrompt(path, **bound)` — str subclass. `__new__` reads `prompt.jinja`. `**bound` sets default variables.
- `str(p)` — raw template.
- `p(**vars)` — Jinja2 `StrictUndefined` render. Missing vars raise `UndefinedError`. Call-time vars override bound defaults.

Because `CoaxedPrompt` is a `str`, it drops into any API that accepts a string.

## `AgentLM`

DSPy `BaseLM` subclass. Each `forward()` call spawns a Claude Code subprocess via `claude_agent_sdk.query()`.

```python
AgentLM(
    model: str = "claude-agent-sdk",
    model_type: str = "chat",
    max_tokens: int = 4096,
    **kwargs,                # forwarded to ClaudeAgentOptions
)
```

Common `ClaudeAgentOptions` kwargs:

- `tools: list` — pass `[]` for structured-output tasks.
- `allowed_tools: list[str]`, `disallowed_tools: list[str]`.
- `max_turns: int`.
- `env: dict[str, str]` — subprocess environment.

Methods: `forward`, `aforward`, `copy(**kwargs)`, `inspect_history(n)`.

## `OpenAILM`

DSPy `BaseLM` subclass that hits any OpenAI-compatible chat endpoint.

```python
from coaxer import OpenAILM

lm = OpenAILM(model="llama3")                                           # Ollama default
lm = OpenAILM(model="meta-llama/Llama-3-8B", base_url="http://localhost:8000/v1")
lm = OpenAILM(model="gpt-4o", base_url="https://api.openai.com/v1", api_key="sk-...")
```

## End-to-end example

```bash
coax labels/repo-classification --out prompts/repo-classification
```

```python
from coaxer import CoaxedPrompt

p = CoaxedPrompt("prompts/repo-classification")
print(p(
    readme="# awesome-skills\n500+ curated Claude skills",
    description="A curated list of awesome Claude skills",
    stars=521,
))
```
