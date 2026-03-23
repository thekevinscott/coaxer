# karat

Evals-first prompt optimization. Label examples, get better prompts.

The prompt is a build artifact -- your labeled examples are the source of truth. When you want a better prompt, add more examples and regenerate.

## Install

```bash
uv add git+ssh://git@github.com/thekevinscott/karat.git
```

### Install the `/optimize` skill (optional)

```bash
uvx --from git+ssh://git@github.com/thekevinscott/karat.git karat install
```

Copies the `/optimize` skill into `.claude/skills/optimize/SKILL.md` in your project. The skill walks agents through labeling examples and optimizing prompts.

## Usage

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

## Loading Optimized Programs

After running `/optimize`, load the compiled program with `load_predict`:

```python
from karat import load_predict
from my_sigs import ClassifyRepo

# Loads optimized JSON if it exists, falls back to unoptimized
classify = load_predict(ClassifyRepo, path="data/optimized_classify_repo.json")
result = classify(readme="# awesome-skills\n\n500+ curated Claude skills")
```

## Labeling TUI

For interactive labeling in a separate terminal:

```bash
karat label examples.json --output labeled.json
```

The agent writes unlabeled examples to a JSON file, the user labels them in the TUI, and the agent picks up the results. See `karat label --help` for the input format.

## Options

`AgentLM` passes all keyword arguments through to `ClaudeAgentOptions`:

```python
# Strip all tools (recommended for classification/structured output)
lm = AgentLM(tools=[])

# Allow specific tools
lm = AgentLM(allowed_tools=["Read", "Glob"])

# Set environment variables for the SDK subprocess
lm = AgentLM(env={"CLAUDECODE": ""})
```

## Caching

Pass a [cachetta](https://github.com/thekevinscott/cachetta) instance to wrap the query function with file-backed caching:

```python
from cachetta import Cachetta
from karat import AgentLM

cache = Cachetta(path=lambda prompt, **kw: f"cache/{prompt}.pkl", duration="7d")
lm = AgentLM(cache=cache)
```

Install with the cache extra: `uv add "karat[cache] @ git+ssh://..."`

## Development

```bash
uv sync --extra dev
uv run just test-unit   # Run tests
uv run just ci          # Full CI (lint + format + typecheck + tests)
```
