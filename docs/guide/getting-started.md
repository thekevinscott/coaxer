# Getting Started

## Installation

```bash
uv add coaxer
```

## Label your examples

Coaxer uses a directory-per-record format. Each record lives in its own folder under a labels root; `record.json` holds scalar fields and references sibling files for larger text or binary inputs.

```
labels/repo-classification/
  _schema.json              # optional
  0001/
    record.json
    readme.md
  0002/
    record.json
    readme.md
```

`record.json`:

```json
{
  "id": "0001",
  "inputs": {
    "readme": "readme.md",
    "description": "A curated list of awesome Claude skills",
    "stars": 521
  },
  "output": "true"
}
```

When an input value names a file that exists in the record folder, coaxer reads that file at compile time (UTF-8 for text, raw bytes for binary). All other values pass through as-is.

### Optional schema

`_schema.json` adds field descriptions, explicit types, and enum values. Descriptions feed the optimizer's prompt synthesis; types become the DSPy signature annotations.

```json
{
  "inputs": {
    "readme": {"desc": "Project README markdown"},
    "stars": {"desc": "GitHub star count", "type": "int"}
  },
  "output": {
    "desc": "Whether the repo is a curated collection",
    "type": "enum",
    "values": ["true", "false"]
  }
}
```

Without a schema, field names and types are inferred from the first record.

## Distill a prompt

```bash
coax labels/repo-classification --out prompts/repo-classification
```

This writes four artifacts:

| File | Purpose |
|---|---|
| `prompt.jinja` | The prompt template with `{{ field }}` slots. |
| `meta.json` | `compiled_at`, `example_count`, `label_hash`, schema snapshot. |
| `dspy.json` | DSPy program state (only when `--optimizer gepa`). |
| `history.jsonl` | One line per compile. |

The default optimizer is `none` -- it emits a schema-derived template without calling any LLM. Pass `--optimizer gepa` to run DSPy 3's GEPA pass, which requires an LLM credential (default: `AgentLM` / Claude Code).

## Consume the prompt

`CoaxedPrompt` is a `str` subclass. The raw Jinja template is what `str(p)` returns, so the object drops in anywhere a string is accepted. `p(**vars)` renders it.

```python
from coaxer import CoaxedPrompt

p = CoaxedPrompt("prompts/repo-classification")
filled = p(
    readme="# awesome-skills\n\n500+ curated Claude skills",
    description="A curated list of awesome Claude skills",
    stars=521,
)
```

Missing variables raise `UndefinedError` (Jinja2 `StrictUndefined`). Bind defaults at construction time and override at call time:

```python
p = CoaxedPrompt("prompts/repo-classification", role="classifier")
filled = p(role="summarizer", readme=..., stars=...)  # call-time wins
```

## Optional: back the compile step with a specific LLM

```python
import dspy
from coaxer import AgentLM, OpenAILM

dspy.configure(lm=AgentLM())                        # Claude via Agent SDK
dspy.configure(lm=OpenAILM(model="llama3"))         # Ollama
```

Then:

```bash
coax labels/... --out prompts/... --optimizer gepa
```

## Requirements

- Python >= 3.14
- DSPy >= 3.0 (for GEPA)
- Jinja2 >= 3.0
- For `AgentLM`: Claude Code CLI installed and authenticated
- For `OpenAILM`: an OpenAI-compatible endpoint
