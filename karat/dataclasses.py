"""OpenAI-compatible response dataclasses that DSPy expects from BaseLM.

DSPy's internals assume LM responses follow the OpenAI chat completion
shape: a CompletionResponse with a list of Choices, each containing a
Message. These dataclasses provide that interface without depending on
the OpenAI SDK.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """OpenAI-style message."""

    role: str
    content: str
    tool_calls: list | None = None


@dataclass
class Choice:
    """OpenAI-style choice."""

    index: int
    message: Message
    finish_reason: str = "stop"
    logprobs: Any = None


@dataclass
class CompletionResponse:
    """OpenAI-style completion response.

    The usage dict uses string keys (not a dataclass) because DSPy calls
    dict(response.usage) internally.
    """

    id: str
    object: str = "chat.completion"
    model: str = "claude-agent-sdk"
    choices: list[Choice] = field(default_factory=list)
    usage: dict = field(
        default_factory=lambda: {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    )
