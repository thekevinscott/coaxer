# AgentLM

_Online: <https://thekevinscott.github.io/coaxer/api/agent-lm/>_

::: coaxer.AgentLM
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      heading_level: 2

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"claude-agent-sdk"` | Model identifier for DSPy tracking. The actual model is determined by the Claude Code CLI. |
| `model_type` | `str` | `"chat"` | DSPy model type. |
| `max_tokens` | `int` | `4096` | Maximum tokens (forwarded to DSPy, not the SDK). |
| `cache` | `Cachetta \| None` | `None` | Optional cachetta instance for response caching. |
| `**kwargs` | | | All other kwargs forwarded to `ClaudeAgentOptions`. |

## Common ClaudeAgentOptions

| Parameter | Type | Description |
|-----------|------|-------------|
| `tools` | `list` | Tools available to the model. Pass `[]` for classification/structured output. |
| `allowed_tools` | `list[str]` | Allowlist of tool names (e.g., `["Read", "Glob"]`). |
| `disallowed_tools` | `list[str]` | Denylist of tool names. |
| `max_turns` | `int` | Maximum agentic turns. |
| `env` | `dict[str, str]` | Environment variables for the SDK subprocess. |

## Methods

### `forward(prompt, messages, **kwargs)`

Synchronous forward pass. Accepts either a plain string `prompt` or an OpenAI-style `messages` list. Per-call kwargs override constructor kwargs.

Returns a `CompletionResponse` (OpenAI-compatible format).

### `aforward(prompt, messages, **kwargs)`

Async version of `forward()`. Calls the SDK directly without threading.

### `copy(**kwargs)`

Returns a new `AgentLM` with updated kwargs. Useful for creating variants with different tool configurations.

### `inspect_history(n=1)`

Returns the last `n` history entries (prompt + response pairs).

## Examples

```python
import dspy
from coaxer import AgentLM

# Basic usage
lm = AgentLM()
dspy.configure(lm=lm)

# Classification (no tools)
lm = AgentLM(tools=[])

# With caching
from cachetta import Cachetta
cache = Cachetta(path=lambda prompt, **kw: f"cache/{prompt}.pkl", duration="7d")
lm = AgentLM(cache=cache, tools=[])
```
