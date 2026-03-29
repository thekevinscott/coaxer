"""Tests for OpenAILM."""

import json

import httpx
import pytest

from karat.dataclasses import CompletionResponse
from karat.openai_lm import OpenAILM


def _mock_chat_response(content="Hello world", model="llama3"):
    """Build a raw OpenAI chat completion JSON response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }


def _mock_transport(response_body, status_code=200):
    """Create an httpx MockTransport that returns a fixed response."""

    def handler(request):
        return httpx.Response(status_code, json=response_body)

    return httpx.MockTransport(handler)


def describe_OpenAILM():
    def describe_init():
        def it_sets_default_values():
            lm = OpenAILM(model="llama3")
            assert lm.model == "llama3"
            assert lm.base_url == "http://localhost:11434/v1"
            assert lm.api_key == "ollama"
            assert lm.history == []

        def it_accepts_custom_base_url():
            lm = OpenAILM(model="gpt-4o", base_url="https://api.openai.com/v1", api_key="sk-xxx")
            assert lm.base_url == "https://api.openai.com/v1"
            assert lm.api_key == "sk-xxx"

        def it_strips_trailing_slash_from_base_url():
            lm = OpenAILM(model="llama3", base_url="http://localhost:11434/v1/")
            assert lm.base_url == "http://localhost:11434/v1"

        def it_passes_kwargs_through():
            lm = OpenAILM(model="llama3", temperature=0.7, max_tokens=2048)
            assert lm.kwargs["temperature"] == 0.7
            assert lm.kwargs["max_tokens"] == 2048

    def describe_forward():
        def it_calls_chat_completions_endpoint():
            transport = _mock_transport(_mock_chat_response("Test response"))
            lm = OpenAILM(model="llama3", _transport=transport)
            result = lm.forward(prompt="Hello")
            assert isinstance(result, CompletionResponse)
            assert result.choices[0].message.content == "Test response"

        def it_sends_correct_request_body():
            captured = {}

            def handler(request):
                captured["body"] = json.loads(request.content)
                captured["url"] = str(request.url)
                captured["auth"] = request.headers.get("authorization")
                return httpx.Response(200, json=_mock_chat_response())

            transport = httpx.MockTransport(handler)
            lm = OpenAILM(model="llama3", api_key="test-key", _transport=transport)
            lm.forward(prompt="What is 2+2?")

            assert captured["url"] == "http://localhost:11434/v1/chat/completions"
            assert captured["body"]["model"] == "llama3"
            assert captured["body"]["messages"] == [{"role": "user", "content": "What is 2+2?"}]
            assert captured["auth"] == "Bearer test-key"

        def it_extracts_prompt_from_messages():
            transport = _mock_transport(_mock_chat_response("Response"))
            lm = OpenAILM(model="llama3", _transport=transport)
            result = lm.forward(
                messages=[
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "Hello"},
                ]
            )
            assert result.choices[0].message.content == "Response"

        def it_passes_messages_directly_when_provided():
            captured = {}

            def handler(request):
                captured["body"] = json.loads(request.content)
                return httpx.Response(200, json=_mock_chat_response())

            transport = httpx.MockTransport(handler)
            lm = OpenAILM(model="llama3", _transport=transport)
            msgs = [{"role": "system", "content": "Be brief"}, {"role": "user", "content": "Hi"}]
            lm.forward(messages=msgs)

            assert captured["body"]["messages"] == msgs

        def it_merges_kwargs():
            captured = {}

            def handler(request):
                captured["body"] = json.loads(request.content)
                return httpx.Response(200, json=_mock_chat_response())

            transport = httpx.MockTransport(handler)
            lm = OpenAILM(model="llama3", temperature=0.5, _transport=transport)
            lm.forward(prompt="test", temperature=0.9)

            assert captured["body"]["temperature"] == 0.9

        def it_populates_usage():
            transport = _mock_transport(_mock_chat_response())
            lm = OpenAILM(model="llama3", _transport=transport)
            result = lm.forward(prompt="test")
            assert result.usage["prompt_tokens"] == 10
            assert result.usage["completion_tokens"] == 5
            assert result.usage["total_tokens"] == 15

        def it_updates_history_via_call():
            transport = _mock_transport(_mock_chat_response("Answer"))
            lm = OpenAILM(model="llama3", _transport=transport)
            lm(prompt="Question")
            assert len(lm.history) == 1

        def it_raises_on_http_error():
            transport = _mock_transport(
                {"error": {"message": "Model not found", "type": "invalid_request_error"}},
                status_code=404,
            )
            lm = OpenAILM(model="nonexistent", _transport=transport)
            with pytest.raises(httpx.HTTPStatusError):
                lm.forward(prompt="test")

    def describe_aforward():
        @pytest.mark.asyncio
        async def it_calls_endpoint_async():
            async def handler(request):
                return httpx.Response(200, json=_mock_chat_response("Async response"))

            transport = httpx.MockTransport(handler)
            lm = OpenAILM(model="llama3", _transport=transport)
            result = await lm.aforward(prompt="Hello async")
            assert isinstance(result, CompletionResponse)
            assert result.choices[0].message.content == "Async response"

        @pytest.mark.asyncio
        async def it_passes_messages_async():
            async def handler(request):
                return httpx.Response(200, json=_mock_chat_response("Ok"))

            transport = httpx.MockTransport(handler)
            lm = OpenAILM(model="llama3", _transport=transport)
            result = await lm.aforward(messages=[{"role": "user", "content": "Hi"}])
            assert result.choices[0].message.content == "Ok"

    def describe_copy():
        def it_returns_new_instance():
            lm = OpenAILM(model="llama3", temperature=0.5)
            copied = lm.copy(temperature=0.9)
            assert copied is not lm
            assert copied.kwargs["temperature"] == 0.9
            assert copied.base_url == lm.base_url
            assert copied.api_key == lm.api_key

        def it_preserves_original():
            lm = OpenAILM(model="llama3", temperature=0.5)
            lm.copy(temperature=0.9)
            assert lm.kwargs["temperature"] == 0.5
