"""Tests for prompt extraction."""

import pytest

from karat.extract_prompt import extract_prompt


@pytest.mark.parametrize(
    "prompt,messages,expected",
    [
        ("Hello world", None, "Hello world"),
        (None, None, ""),
        (
            None,
            [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Second question"},
            ],
            "Second question",
        ),
        (
            None,
            [
                {"role": "system", "content": "System prompt"},
                {"role": "assistant", "content": "Hello"},
            ],
            "system: System prompt\nassistant: Hello",
        ),
        (
            "From prompt",
            [{"role": "user", "content": "From messages"}],
            "From messages",
        ),
        ("Fallback", [], "Fallback"),
        (None, [{"role": "user"}], ""),
    ],
    ids=[
        "simple_prompt",
        "empty_inputs",
        "last_user_message",
        "concatenate_no_user",
        "messages_precedence",
        "empty_messages_fallback",
        "missing_content",
    ],
)
def test_extract_prompt(prompt, messages, expected):
    assert extract_prompt(prompt, messages) == expected
