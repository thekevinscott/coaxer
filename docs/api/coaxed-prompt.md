# `CoaxedPrompt`

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
