from pathlib import Path

import pytest
from jinja2 import UndefinedError

from coaxer.prompt import CoaxedPrompt


def _write_prompt(tmp: Path, body: str) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "prompt.jinja").write_text(body)
    return tmp


def test_is_str_subclass(tmp_path: Path):
    path = _write_prompt(tmp_path / "p", "hello {{ name }}")
    p = CoaxedPrompt(path)
    assert isinstance(p, str)


def test_str_returns_raw_template(tmp_path: Path):
    path = _write_prompt(tmp_path / "p", "hello {{ name }}")
    p = CoaxedPrompt(path)
    assert str(p) == "hello {{ name }}"


def test_call_renders_template(tmp_path: Path):
    path = _write_prompt(tmp_path / "p", "hello {{ name }}")
    p = CoaxedPrompt(path)
    assert p(name="world") == "hello world"


def test_missing_var_raises_undefined(tmp_path: Path):
    path = _write_prompt(tmp_path / "p", "hello {{ name }}")
    p = CoaxedPrompt(path)
    with pytest.raises(UndefinedError):
        p()


def test_bound_defaults_applied(tmp_path: Path):
    path = _write_prompt(tmp_path / "p", "{{ role }}: {{ msg }}")
    p = CoaxedPrompt(path, role="classifier")
    assert p(msg="hi") == "classifier: hi"


def test_call_time_overrides_bound(tmp_path: Path):
    path = _write_prompt(tmp_path / "p", "{{ role }}")
    p = CoaxedPrompt(path, role="classifier")
    assert p(role="summarizer") == "summarizer"


def test_missing_prompt_file_raises(tmp_path: Path):
    tmp_path.joinpath("p").mkdir()
    with pytest.raises(FileNotFoundError):
        CoaxedPrompt(tmp_path / "p")


def test_accepts_string_path(tmp_path: Path):
    path = _write_prompt(tmp_path / "p", "hi")
    p = CoaxedPrompt(str(path))
    assert str(p) == "hi"


def test_preserves_jinja_braces_in_raw_template(tmp_path: Path):
    # templates often have JSON / code braces that must not collide
    path = _write_prompt(tmp_path / "p", 'Return {"ok": true} with {{ msg }}')
    p = CoaxedPrompt(path)
    assert p(msg="done") == 'Return {"ok": true} with done'
