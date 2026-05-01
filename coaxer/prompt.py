"""`CoaxedPrompt` -- a compiled prompt as a `str` subclass.

`CoaxedPrompt("prompts/foo")` reads `prompt.jinja` and behaves as its raw
template string everywhere `str` is accepted. `p(**vars)` renders the
template with Jinja2 `StrictUndefined` (missing variables raise).
`p.response_format` returns a Pydantic model class derived from
`meta.json`, ready for OpenAI's `.parse()` or Anthropic's tool-use
`input_schema` (via `model_json_schema()`).
"""

from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined, Template
from pydantic import BaseModel, create_model

from coaxer.resolve_field_type import resolve_field_type
from coaxer.schema import Field

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

    @cached_property
    def response_format(self) -> type[BaseModel]:
        meta = json.loads((self._path / "meta.json").read_text())
        output = meta["fields"]["output"]
        name = meta.get("output_name", "output")
        field = Field(type=output.get("type", "str"), values=output.get("values"))
        field_spec = (resolve_field_type(field), ...)
        return create_model("Output", **{name: field_spec})  # ty: ignore[no-matching-overload]
