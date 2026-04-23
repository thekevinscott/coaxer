# coaxer

Label examples. Derive the prompt. Consume it as a string.

[Documentation](https://thekevinscott.github.io/coaxer/)

## Motivation

Writing prompts by hand is slow, and the prose grows brittle as cases accumulate. Coaxer flips it: label examples of the behavior you want, derive the prompt from those labels -- when it drifts, add more labels instead of rewriting.

Labels are the source of truth. The prompt is a build artifact.

## Install

```bash
uv add coaxer
```

## Label

One directory per record. `record.json` holds scalar fields; large text and binary inputs live as sibling files.

```
labels/repo-classification/
  _schema.json              # optional: field descriptions + types + enums
  0001/
    record.json             # {id, inputs: {readme, stars, ...}, output}
    readme.md               # large text referenced from record.json
  0002/
    ...
```

`_schema.json` is optional. Without it, field names and types are inferred from the records.

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

## Distill

```bash
coaxer distill labels/repo-classification --out prompts/repo-classification
```

Writes four files to the output folder:

| File | Purpose |
|---|---|
| `prompt.jinja` | Human-readable Jinja template with `{{ field }}` slots. |
| `meta.json` | Compile metadata: `compiled_at`, `example_count`, `label_hash`, schema. |
| `dspy.json` | DSPy program state (only when `--optimizer gepa`). |
| `history.jsonl` | Append-only compile log. |

Optimizer is opt-in. `--optimizer gepa` runs DSPy 3's GEPA pass and requires an LLM credential. The default (`--optimizer none`) emits a schema-derived template and is reproducible without network.

## Consume

```python
from coaxer import CoaxPrompt

p = CoaxPrompt("prompts/repo-classification", role="classifier")  # bind defaults
filled = p(readme=new_readme, stars=1200)                         # render at call time
```

- `CoaxPrompt(path, **bound)` — `str` subclass; `__new__` reads `prompt.jinja`.
- `str(p)` — raw template.
- `p(**vars)` — Jinja2 `StrictUndefined` render; missing variables raise.
- Call-time variables override bound defaults.

Because `CoaxPrompt` is a `str`, it drops in anywhere a string is accepted (logging, OpenAI SDK `messages`, Anthropic SDK, DSPy signatures built externally, etc.).

## Compile LLMs

`AgentLM` routes compile calls through the Anthropic Agent SDK (Claude Code). `OpenAILM` hits any OpenAI-compatible endpoint (Ollama, vLLM, OpenAI).

```python
from coaxer import AgentLM, OpenAILM

lm = AgentLM()                                # Claude via Agent SDK
lm = OpenAILM(model="llama3")                 # Ollama
lm = OpenAILM(model="gpt-4o", base_url="https://api.openai.com/v1", api_key="sk-...")
```

Both pass keyword arguments through to their underlying client.

## Caching

Pass a [cachetta](https://github.com/thekevinscott/cachetta) instance to file-back LM responses:

```python
from cachetta import Cachetta
from coaxer import AgentLM

cache = Cachetta(path=lambda prompt, **kw: f"cache/{prompt}.pkl", duration="7d")
lm = AgentLM(cache=cache)
```

Install with the cache extra: `uv add "coaxer[cache]"`.

## Development

```bash
uv sync --extra dev
uv run just test-unit   # Unit tests
uv run just ci          # Full CI (lint + format + typecheck + tests)
```
