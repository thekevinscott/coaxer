# dspy-anthropic-agent-sdk

DSPy language model backed by the Anthropic Agent SDK (Claude Code). Use DSPy's optimizers and signatures with Claude Code as the LLM backend -- no API key needed, uses your existing Claude Code authentication.

## Install

```bash
uv add git+ssh://git@github.com/thekevinscott/dspy-anthropic-agent-sdk.git
```

## Usage

```python
import dspy
from dspy_agent_sdk import AgentLM

lm = AgentLM()
dspy.configure(lm=lm)

class Classify(dspy.Signature):
    """Classify a GitHub repo as a curated collection or an organic project."""
    readme: str = dspy.InputField()
    is_collection: bool = dspy.OutputField()

classify = dspy.Predict(Classify)
result = classify(readme="# awesome-skills\n\n500+ curated Claude skills")
```

## Options

`AgentLM` passes all keyword arguments through to `ClaudeAgentOptions`:

```python
# Strip all tools (recommended for classification/structured output)
lm = AgentLM(tools=[], max_turns=20)

# Allow specific tools
lm = AgentLM(allowed_tools=["Read", "Glob"])

# Set environment variables for the SDK subprocess
lm = AgentLM(env={"CLAUDECODE": ""})
```

## Caching

Pass a [cachetta](https://github.com/thekevinscott/cachetta) instance to cache LLM responses across runs:

```python
from cachetta import Cachetta
from dspy_agent_sdk import AgentLM

cache = Cachetta(path="./cache", duration="7d")
lm = AgentLM(cache=cache)
```

Cache keys are derived from the prompt and all options, so prompt changes automatically invalidate cached results.

## Development

```bash
uv sync --extra dev
uv run just test-unit   # Run tests
uv run just ci          # Full CI (lint + format + typecheck + tests)
```
