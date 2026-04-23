"""DSPy language model for OpenAI-compatible endpoints (Ollama, vLLM, OpenAI, etc.)."""

import uuid
from typing import Any

import httpx
from dspy.clients.base_lm import BaseLM

from .dataclasses import Choice, CompletionResponse, Message


class OpenAILM(BaseLM):
    """DSPy language model that calls any OpenAI-compatible chat completion API.

    Defaults target Ollama on localhost. For other providers, set base_url
    and api_key::

        # Ollama (default)
        lm = OpenAILM(model="llama3")

        # OpenAI
        lm = OpenAILM(model="gpt-4o", base_url="https://api.openai.com/v1", api_key="sk-...")

        # vLLM
        lm = OpenAILM(model="meta-llama/Llama-3-8B", base_url="http://localhost:8000/v1")
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        _transport: httpx.BaseTransport | None = None,
        **kwargs,
    ):
        super().__init__(model=model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._transport = _transport

    def forward(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        merged = {**self.kwargs, **kwargs}
        msgs = messages if messages else [{"role": "user", "content": prompt or ""}]
        body = {"model": self.model, "messages": msgs, **merged}

        client_kwargs: dict[str, Any] = {}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        with httpx.Client(**client_kwargs) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()

        return self._parse_response(resp.json())

    async def aforward(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        merged = {**self.kwargs, **kwargs}
        msgs = messages if messages else [{"role": "user", "content": prompt or ""}]
        body = {"model": self.model, "messages": msgs, **merged}

        client_kwargs: dict[str, Any] = {}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        async with httpx.AsyncClient(**client_kwargs) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()

        return self._parse_response(resp.json())

    def _parse_response(self, data: dict) -> CompletionResponse:
        choices = [
            Choice(
                index=c.get("index", i),
                message=Message(
                    role=c["message"]["role"],
                    content=c["message"].get("content", ""),
                ),
                finish_reason=c.get("finish_reason", "stop"),
            )
            for i, c in enumerate(data.get("choices", []))
        ]

        usage = data.get("usage", {})

        return CompletionResponse(
            id=data.get("id", f"openai-lm-{uuid.uuid4().hex[:8]}"),
            model=data.get("model", self.model),
            choices=choices,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )
