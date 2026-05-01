from pathlib import Path

import pytest
from jinja2 import UndefinedError

from coaxer.prompt import CoaxedPrompt


def _write_prompt(tmp: Path, body: str) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "prompt.jinja").write_text(body)
    return tmp


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
