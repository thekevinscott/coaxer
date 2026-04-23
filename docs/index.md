# coaxer

Label examples. Derive the prompt. Consume it as a string.

The prompt is a build artifact; your labeled examples are the source of truth. When the prompt drifts, add more examples and recompile.

## Install

```bash
uv add coaxer
```

## Quick start

Label a handful of examples in a folder (see [Getting Started](guide/getting-started.md) for the shape), then:

```bash
coax labels/repo-classification --out prompts/repo-classification
```

Use the compiled prompt:

```python
from coaxer import CoaxedPrompt

p = CoaxedPrompt("prompts/repo-classification")
filled = p(readme=new_readme, stars=1200)
```

## Core concepts

- **Label folder** — one directory per record. `record.json` holds scalar fields; sibling files (`readme.md`, `logo.png`) carry large text or binary inputs.
- **`coax`** — reads the folder, builds a DSPy signature internally, optionally runs GEPA, writes `prompt.jinja` + `meta.json` + `dspy.json` + `history.jsonl`.
- **`CoaxedPrompt(path)`** — a `str` subclass. `str(p)` is the raw Jinja template; `p(**vars)` renders it. Drops in anywhere a string is accepted.
- **`AgentLM` / `OpenAILM`** — LLM backends for the optional compile-time optimizer. See the [API reference](api/agent-lm.md).
