# `CoaxedPrompt`

_Online: <https://thekevinscott.github.io/coaxer/api/coaxed-prompt/>_

A compiled prompt as a `str` subclass.

```python
from coaxer import CoaxedPrompt

p = CoaxedPrompt("prompts/repo-classification", role="classifier")
filled = p(readme=new_readme, stars=1200)
```

## Constructor

```python
CoaxedPrompt(path: str | Path, **bound: Any)
```

- `path` — folder produced by `coax`. Must contain `prompt.jinja`.
- `**bound` — default values bound at construction time. Overridden by call-time keyword arguments.

`__new__` reads `prompt.jinja` and stores the raw template as the underlying `str`. Because `CoaxedPrompt` is a `str`, instances drop in anywhere a string is accepted (logging, LLM SDK `messages`, external template engines).

## `str(p)`

Returns the raw Jinja template, including `{{ field }}` slots.

```python
assert isinstance(p, str)
assert "{{ readme }}" in str(p)
```

## `p(**variables)`

Renders the template with the merged variables (bound defaults plus call-time keyword arguments; call-time wins).

Uses Jinja2 `StrictUndefined` — missing variables raise `jinja2.UndefinedError`.

```python
filled = p(readme="# hi", stars=10)                 # ok
p()                                                  # raises UndefinedError
```

## Field discovery

The expected variables are whatever slots the template contains, which in turn reflects the label folder's schema at compile time. Inspect `meta.json` (sibling to `prompt.jinja`) for the canonical field list:

```python
import json
from pathlib import Path

meta = json.loads(Path("prompts/repo-classification/meta.json").read_text())
list(meta["fields"]["inputs"])  # ['readme', 'description', 'stars']
```

## `p.response_format`

A Pydantic model class derived from the compiled output schema. Cached after first access.

```python
Model = p.response_format
Model.model_json_schema()
# {'type': 'object', 'properties': {'is_collection': {'type': 'boolean'}}, ...}
```

### OpenAI

```python
from openai import OpenAI

client = OpenAI()
resp = client.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": p(readme=..., stars=...)}],
    response_format=p.response_format,
)
result = resp.choices[0].message.parsed
```

### Anthropic

```python
import anthropic

Model = p.response_format
client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": p(readme=..., stars=...)}],
    tools=[{
        "name": "respond",
        "input_schema": Model.model_json_schema(),
    }],
    tool_choice={"type": "tool", "name": "respond"},
)
parsed = Model.model_validate(resp.content[0].input)
```
