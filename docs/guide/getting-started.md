# Getting Started

## Installation

```bash
uv add coaxer
```

### Install the `/optimize` skill (optional)

```bash
uvx coaxer install
```

This copies the `/optimize` skill into `.claude/skills/optimize/SKILL.md` in your project. The skill walks agents through labeling examples and optimizing prompts.

## Basic Usage

```python
import dspy
from coaxer import AgentLM

# Create a DSPy LM backed by Claude Code
lm = AgentLM()
dspy.configure(lm=lm)

# Define a signature
class Classify(dspy.Signature):
    """Classify a GitHub repo as a curated collection or an organic project."""
    readme: str = dspy.InputField()
    is_collection: bool = dspy.OutputField()

# Run inference
classify = dspy.Predict(Classify)
result = classify(readme="# awesome-skills\n\n500+ curated Claude skills")
```

## Loading Optimized Programs

After running `/optimize`, load the compiled program:

```python
from coaxer import load_predict
from my_sigs import ClassifyRepo

# Loads optimized JSON if it exists, falls back to unoptimized
classify = load_predict(ClassifyRepo, path="data/optimized_classify_repo.json")
result = classify(readme="# awesome-skills\n\n500+ curated Claude skills")
```

## Using Local Models (Ollama, vLLM)

`OpenAILM` calls any OpenAI-compatible chat completion API. No Claude Code CLI required.

```python
import dspy
from coaxer import OpenAILM

# Ollama (default -- targets localhost:11434)
lm = OpenAILM(model="llama3")
dspy.configure(lm=lm)

# vLLM
lm = OpenAILM(model="meta-llama/Llama-3-8B", base_url="http://localhost:8000/v1")

# OpenAI
lm = OpenAILM(model="gpt-4o", base_url="https://api.openai.com/v1", api_key="sk-...")
```

## AgentLM Options

All keyword arguments are forwarded to `ClaudeAgentOptions`:

```python
# Strip all tools (recommended for classification/structured output)
lm = AgentLM(tools=[])

# Allow specific tools
lm = AgentLM(allowed_tools=["Read", "Glob"])

# Set environment variables for the SDK subprocess
lm = AgentLM(env={"CLAUDECODE": ""})
```

Per-call kwargs override constructor kwargs (shallow merge).

## Requirements

- Python >= 3.14
- DSPy >= 2.6
- For `AgentLM`: Claude Code CLI installed and authenticated
- For `OpenAILM`: an OpenAI-compatible endpoint (Ollama, vLLM, OpenAI, etc.)
