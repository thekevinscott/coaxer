import json
from pathlib import Path

import pytest
from jinja2 import UndefinedError
from pydantic import BaseModel, ValidationError

from coaxer.prompt import CoaxedPrompt


def _write_prompt(tmp: Path, body: str) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "prompt.jinja").write_text(body)
    return tmp


def _write_artifact(
    tmp: Path,
    body: str,
    *,
    output_type: str,
    output_values: list[str] | None = None,
    output_name: str | None = "output",
) -> Path:
    """Write a minimal prompt + meta.json pair so ``response_format`` has
    everything it needs without going through ``distill()``."""
    folder = _write_prompt(tmp, body)
    output_field: dict = {"type": output_type}
    if output_values is not None:
        output_field["values"] = output_values
    meta: dict = {"fields": {"inputs": {}, "output": output_field}}
    if output_name is not None:
        meta["output_name"] = output_name
    (folder / "meta.json").write_text(json.dumps(meta))
    return folder


def describe_CoaxedPrompt():
    def it_is_a_str_subclass(tmp_path: Path):
        path = _write_prompt(tmp_path / "p", "hello {{ name }}")
        p = CoaxedPrompt(path)
        assert isinstance(p, str)

    def it_returns_raw_template_as_str(tmp_path: Path):
        path = _write_prompt(tmp_path / "p", "hello {{ name }}")
        p = CoaxedPrompt(path)
        assert str(p) == "hello {{ name }}"

    def it_renders_template_when_called(tmp_path: Path):
        path = _write_prompt(tmp_path / "p", "hello {{ name }}")
        p = CoaxedPrompt(path)
        assert p(name="world") == "hello world"

    def it_raises_undefined_when_var_is_missing(tmp_path: Path):
        path = _write_prompt(tmp_path / "p", "hello {{ name }}")
        p = CoaxedPrompt(path)
        with pytest.raises(UndefinedError):
            p()

    def it_applies_bound_defaults(tmp_path: Path):
        path = _write_prompt(tmp_path / "p", "{{ role }}: {{ msg }}")
        p = CoaxedPrompt(path, role="classifier")
        assert p(msg="hi") == "classifier: hi"

    def it_lets_call_time_args_override_bound(tmp_path: Path):
        path = _write_prompt(tmp_path / "p", "{{ role }}")
        p = CoaxedPrompt(path, role="classifier")
        assert p(role="summarizer") == "summarizer"

    def it_raises_when_prompt_file_is_missing(tmp_path: Path):
        tmp_path.joinpath("p").mkdir()
        with pytest.raises(FileNotFoundError):
            CoaxedPrompt(tmp_path / "p")

    def it_accepts_string_path(tmp_path: Path):
        path = _write_prompt(tmp_path / "p", "hi")
        p = CoaxedPrompt(str(path))
        assert str(p) == "hi"

    def it_preserves_jinja_braces_in_raw_template(tmp_path: Path):
        # templates often have JSON / code braces that must not collide
        path = _write_prompt(tmp_path / "p", 'Return {"ok": true} with {{ msg }}')
        p = CoaxedPrompt(path)
        assert p(msg="done") == 'Return {"ok": true} with done'


def describe_response_format():
    def it_returns_a_basemodel_subclass(tmp_path: Path):
        path = _write_artifact(tmp_path / "p", "x", output_type="bool")
        Model = CoaxedPrompt(path).response_format
        assert isinstance(Model, type)
        assert issubclass(Model, BaseModel)

    @pytest.mark.parametrize(
        "output_type,json_type",
        [
            ("bool", "boolean"),
            ("int", "integer"),
            ("float", "number"),
            ("str", "string"),
        ],
    )
    def it_maps_python_types_to_json_schema_types(output_type: str, json_type: str, tmp_path: Path):
        path = _write_artifact(tmp_path / "p", "x", output_type=output_type)
        schema = CoaxedPrompt(path).response_format.model_json_schema()
        assert schema["properties"]["output"]["type"] == json_type

    def describe_enum_outputs():
        def it_accepts_listed_values(tmp_path: Path):
            path = _write_artifact(
                tmp_path / "p", "x", output_type="enum", output_values=["yes", "no"]
            )
            Model = CoaxedPrompt(path).response_format
            Model.model_validate({"output": "yes"})
            Model.model_validate({"output": "no"})

        def it_rejects_unlisted_values(tmp_path: Path):
            path = _write_artifact(
                tmp_path / "p", "x", output_type="enum", output_values=["yes", "no"]
            )
            Model = CoaxedPrompt(path).response_format
            with pytest.raises(ValidationError):
                Model.model_validate({"output": "maybe"})

    def describe_field_name():
        def it_uses_output_name_from_meta(tmp_path: Path):
            path = _write_artifact(
                tmp_path / "p", "x", output_type="bool", output_name="is_collection"
            )
            schema = CoaxedPrompt(path).response_format.model_json_schema()
            assert "is_collection" in schema["properties"]
            assert "output" not in schema["properties"]

        def it_defaults_to_output_when_meta_lacks_output_name(tmp_path: Path):
            """Older artifacts won't have ``output_name``; runtime falls back to ``output``."""
            path = _write_artifact(tmp_path / "p", "x", output_type="bool", output_name=None)
            schema = CoaxedPrompt(path).response_format.model_json_schema()
            assert "output" in schema["properties"]

    def it_raises_when_meta_is_missing(tmp_path: Path):
        """``response_format`` reads ``meta.json``; the consumer should get a clear error."""
        path = _write_prompt(tmp_path / "p", "x")
        p = CoaxedPrompt(path)
        with pytest.raises(FileNotFoundError):
            _ = p.response_format
