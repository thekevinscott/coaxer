# Caching

coaxer supports response caching via [cachetta](https://github.com/thekevinscott/cachetta), a file-backed cache decorator. This avoids redundant LLM calls when the same prompt is run multiple times.

## Install

```bash
uv add "coaxer[cache]"
```

## Usage

```python
from cachetta import Cachetta
from coaxer import AgentLM

cache = Cachetta(
    path=lambda prompt, **kw: f"cache/{prompt}.pkl",
    duration="7d",
)
lm = AgentLM(cache=cache)
```

Cachetta wraps the internal `query_assistant_text` function as a decorator. The cache key is derived from the prompt argument automatically -- any change to the prompt invalidates the cache.

## How It Works

When `cache` is passed to `AgentLM`, the constructor calls `cache.wrap(query_assistant_text)` to create a cached version of the query function. On each `forward()` call:

1. The prompt is hashed to a cache key
2. If a cached response exists and hasn't expired, it's returned immediately
3. Otherwise, the SDK is called and the response is cached for future use

This is transparent to DSPy -- the `CompletionResponse` format is identical whether cached or not.
