# karat

Evals-first prompt optimization. Label examples, get better prompts.

The prompt is a build artifact -- your labeled examples are the source of truth. When you want a better prompt, add more examples and regenerate.

## Install

```bash
uv add karat
```

## Quick Start

```python
import dspy
from karat import AgentLM

lm = AgentLM()
dspy.configure(lm=lm)

class Classify(dspy.Signature):
    """Classify a GitHub repo as a curated collection or an organic project."""
    readme: str = dspy.InputField()
    is_collection: bool = dspy.OutputField()

classify = dspy.Predict(Classify)
result = classify(readme="# awesome-skills\n\n500+ curated Claude skills")
```

## Core Concepts

**AgentLM** is a DSPy language model that routes all LLM calls through the Anthropic Agent SDK (Claude Code). No API key needed -- it uses your existing Claude Code authentication.

**load_predict** loads optimized DSPy programs saved by the `/optimize` skill, with automatic fallback to unoptimized if the file doesn't exist.

**Labeling TUI** is a terminal interface for human-in-the-loop labeling. An agent writes examples to JSON, a human labels them in the TUI, and the agent reads results back.

**/optimize skill** is a Claude Code skill that orchestrates the full workflow: read a DSPy Signature, sample data, collect human labels via the TUI, run DSPy optimization, and save a compiled program.
