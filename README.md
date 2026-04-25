# coaxer

Label examples. Derive the prompt. Consume it as a string.

Full docs: <https://thekevinscott.github.io/coaxer/> · ship-with-package source in [`docs/`](docs/).

## Motivation

Writing prompts by hand is slow, and the prose grows brittle as cases accumulate. Coaxer flips it: label examples of the behavior you want, derive the prompt from those labels — when it drifts, add more labels instead of rewriting.

Labels are the source of truth. The prompt is a build artifact.

## Install

```bash
uv add coaxer
```

## Quick start

```bash
coax labels/repo-classification --out prompts/repo-classification
```

```python
from coaxer import CoaxedPrompt

p = CoaxedPrompt("prompts/repo-classification")
filled = p(readme=new_readme, stars=1200)
```

## Getting Started

Label folder is one directory per record; `record.json` plus sibling files for large text or binary inputs. `coax` compiles the folder into `prompt.jinja` + `meta.json` (+ `dspy.json` when `--optimizer gepa`) + `history.jsonl`. Default optimizer is `none` (schema-derived, no network).

Full walkthrough: [`docs/guide/getting-started.md`](docs/guide/getting-started.md).

## CoaxedPrompt

`CoaxedPrompt(path, **bound)` is a `str` subclass. `str(p)` is the raw Jinja template; `p(**vars)` renders it (Jinja2 `StrictUndefined` — missing vars raise). Bound defaults at construction; call-time vars override.

Reference: [`docs/api/coaxed-prompt.md`](docs/api/coaxed-prompt.md).

## CLI

```bash
coax <labels-dir> --out <prompts-dir> [--optimizer {none,gepa}] [--output-name NAME]
```

Reference: [`docs/api/cli.md`](docs/api/cli.md).

## AgentLM

DSPy `BaseLM` backed by the Claude Agent SDK. `**kwargs` forward to `ClaudeAgentOptions` (`tools`, `allowed_tools`, `max_turns`, …).

```python
from coaxer import AgentLM
lm = AgentLM(tools=[])
```

Reference: [`docs/api/agent-lm.md`](docs/api/agent-lm.md).

## OpenAILM

DSPy `BaseLM` for any OpenAI-compatible chat endpoint (Ollama, vLLM, OpenAI, LM Studio, …).

```python
from coaxer import OpenAILM
lm = OpenAILM(model="gpt-4o", base_url="https://api.openai.com/v1", api_key="sk-...")
```

Reference: [`docs/api/openai-lm.md`](docs/api/openai-lm.md).

## Migrations

Downstream-consumer upgrade instructions for breaking changes live in [`MIGRATIONS.md`](MIGRATIONS.md) (also published at [`docs/migrations.md`](docs/migrations.md)). The full release log is in [`CHANGELOG.md`](CHANGELOG.md).

## Development

```bash
uv sync --extra dev
uv run just test-unit   # Unit tests
uv run just ci          # Full CI (lint + format + typecheck + tests)
```
