# OpenAILM

::: coaxer.OpenAILM
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      heading_level: 2

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | *(required)* | Model name sent in the API request (e.g., `"llama3"`, `"gpt-4o"`). |
| `base_url` | `str` | `"http://localhost:11434/v1"` | Base URL of the OpenAI-compatible API. Trailing slash is stripped. |
| `api_key` | `str` | `"ollama"` | API key sent as `Bearer` token. Ollama ignores this, but OpenAI/vLLM require it. |
| `**kwargs` | | | Forwarded to the chat completion request body (`temperature`, `max_tokens`, etc.). |

## Methods

### `forward(prompt, messages, **kwargs)`

Synchronous forward pass. Accepts either a plain string `prompt` (wrapped as a user message) or an OpenAI-style `messages` list (sent as-is). Per-call kwargs override constructor kwargs.

Returns a `CompletionResponse` (OpenAI-compatible format).

### `aforward(prompt, messages, **kwargs)`

Async version of `forward()`. Uses `httpx.AsyncClient`.

### `copy(**kwargs)`

Returns a new `OpenAILM` with updated kwargs. Inherited from `BaseLM`.

## Examples

```python
import dspy
from coaxer import OpenAILM

# Ollama (default)
lm = OpenAILM(model="llama3")
dspy.configure(lm=lm)

# OpenAI
lm = OpenAILM(
    model="gpt-4o",
    base_url="https://api.openai.com/v1",
    api_key="sk-...",
)

# vLLM
lm = OpenAILM(
    model="meta-llama/Llama-3-8B",
    base_url="http://localhost:8000/v1",
)

# With temperature
lm = OpenAILM(model="llama3", temperature=0.7, max_tokens=2048)
```

## Supported Providers

Any server exposing the `POST /chat/completions` endpoint in OpenAI format:

- **Ollama** -- `http://localhost:11434/v1` (default)
- **vLLM** -- `http://localhost:8000/v1`
- **OpenAI** -- `https://api.openai.com/v1`
- **Azure OpenAI** -- your deployment URL + `/v1`
- **LM Studio** -- `http://localhost:1234/v1`
- **llama.cpp server** -- `http://localhost:8080/v1`
