"""Integration test: a rendered ``CoaxedPrompt`` travels through ``OpenAILM``
to the OpenAI-compatible HTTP boundary unchanged.

Contract: distill → CoaxedPrompt → lm.forward(prompt=...) must produce a
chat completion request whose ``messages[0].content`` is the rendered
template string, and whose response is parsed back into a
``CompletionResponse``. ``httpx.MockTransport`` captures the wire-level
request so we never hit a real endpoint.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from coaxer.compiler import distill
from coaxer.dataclasses import CompletionResponse
from coaxer.openai_lm import OpenAILM
from coaxer.prompt import CoaxedPrompt

FIXTURE = Path(__file__).resolve().parents[1] / "__fixtures__" / "labels" / "demo"


def _chat_response(content: str = "true", model: str = "llama3") -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
    }


def describe_coaxed_prompt_through_openai_lm():
    def it_reaches_openai_endpoint_unchanged_sync(tmp_path: Path) -> None:
        out = tmp_path / "out"
        distill(FIXTURE, out, optimizer=None)

        prompt = CoaxedPrompt(out)
        rendered = prompt(
            readme="# sample\nline two",
            description="A demo repository",
            stars=321,
        )

        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["body"] = json.loads(request.content)
            captured["auth"] = request.headers.get("authorization")
            return httpx.Response(200, json=_chat_response("true"))

        transport = httpx.MockTransport(handler)
        lm = OpenAILM(model="llama3", _transport=transport)
        result = lm.forward(prompt=rendered)

        # The rendered template must arrive verbatim in the user message.
        assert captured["url"].endswith("/chat/completions")
        assert captured["body"]["model"] == "llama3"
        assert captured["body"]["messages"] == [{"role": "user", "content": rendered}]
        assert "# sample" in captured["body"]["messages"][0]["content"]
        assert "A demo repository" in captured["body"]["messages"][0]["content"]
        assert "321" in captured["body"]["messages"][0]["content"]

        # And the response must parse back into a CompletionResponse.
        assert isinstance(result, CompletionResponse)
        assert result.choices[0].message.content == "true"
        assert result.usage["total_tokens"] == 6

    @pytest.mark.asyncio
    async def it_reaches_openai_endpoint_unchanged_async(tmp_path: Path) -> None:
        out = tmp_path / "out"
        distill(FIXTURE, out, optimizer=None)
        prompt = CoaxedPrompt(out)
        rendered = prompt(readme="# r", description="d", stars=9)

        captured: dict = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=_chat_response("false"))

        transport = httpx.MockTransport(handler)
        lm = OpenAILM(model="llama3", _transport=transport)
        result = await lm.aforward(prompt=rendered)

        assert captured["body"]["messages"][0]["content"] == rendered
        assert result.choices[0].message.content == "false"

    def it_passes_unrendered_prompt_as_string(tmp_path: Path) -> None:
        """Because ``CoaxedPrompt`` is a ``str`` subclass, passing it directly
        (unrendered) must still land in the request body as its template text."""
        out = tmp_path / "out"
        distill(FIXTURE, out, optimizer=None)
        prompt = CoaxedPrompt(out)

        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=_chat_response())

        transport = httpx.MockTransport(handler)
        lm = OpenAILM(model="llama3", _transport=transport)
        lm.forward(prompt=prompt)

        assert captured["body"]["messages"][0]["content"] == str(prompt)
        # The raw template includes the Jinja slot markers.
        assert "{{ readme }}" in captured["body"]["messages"][0]["content"]
