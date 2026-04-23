"""Tests for prompt extraction."""

import pytest

from coaxer.extract_prompt import extract_prompt


@pytest.mark.parametrize(
    "prompt,messages,expected",
    [
        ("Hello world", None, (None, "Hello world")),
        (None, None, (None, "")),
        (
            None,
            [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Second question"},
            ],
            (
                "System prompt",
                "user: First question\n\nassistant: First answer\n\nuser: Second question",
            ),
        ),
        (
            None,
            [
                {"role": "system", "content": "System prompt"},
                {"role": "assistant", "content": "Hello"},
            ],
            ("System prompt", "assistant: Hello"),
        ),
        (
            "From prompt",
            [{"role": "user", "content": "From messages"}],
            (None, "From messages"),
        ),
        ("Fallback", [], (None, "Fallback")),
        (None, [{"role": "user"}], (None, "")),
        (
            None,
            [{"role": "user", "content": "Only user"}],
            (None, "Only user"),
        ),
        (
            None,
            [
                {"role": "system", "content": "Sys A"},
                {"role": "system", "content": "Sys B"},
                {"role": "user", "content": "Q"},
            ],
            ("Sys A\n\nSys B", "Q"),
        ),
    ],
    ids=[
        "simple_prompt",
        "empty_inputs",
        "system_plus_multi_turn_demos",
        "system_plus_assistant_only",
        "messages_precedence",
        "empty_messages_fallback",
        "missing_content",
        "single_user_no_role_label",
        "multiple_system_messages_joined",
    ],
)
def test_extract_prompt(prompt, messages, expected):
    assert extract_prompt(prompt, messages) == expected
