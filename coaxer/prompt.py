"""`CoaxedPrompt` -- a compiled prompt as a `str` subclass.

`CoaxedPrompt("prompts/foo")` reads `prompt.jinja` and behaves as its raw
template string everywhere `str` is accepted. `p(**vars)` renders the
template with Jinja2 `StrictUndefined` (missing variables raise).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined, Template

_ENV = Environment(undefined=StrictUndefined, keep_trailing_newline=True)


class CoaxedPrompt(str):
    _path: Path
    _bound: dict[str, Any]
    _template: Template

    def __new__(cls, path: str | Path, **bound: Any) -> CoaxedPrompt:
        folder = Path(path)
        template_text = (folder / "prompt.jinja").read_text()
        instance = super().__new__(cls, template_text)
        instance._path = folder
        instance._bound = bound
        instance._template = _ENV.from_string(template_text)
        return instance

    def __call__(self, **variables: Any) -> str:
        merged = {**self._bound, **variables}
        return self._template.render(**merged)
