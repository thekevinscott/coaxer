"""DSPy language model backed by the Anthropic Agent SDK."""

import uuid
from typing import Any

from dspy.clients.base_lm import BaseLM

from ._internal.run_sync import run_sync
from .dataclasses import Choice, CompletionResponse, Message
from .extract_prompt import extract_prompt
from .query_assistant_text import query_assistant_text


class AgentLM(BaseLM):
    """DSPy language model that routes calls through the Anthropic Agent SDK.

    Each call to forward() spawns a Claude Code subprocess via
    claude_agent_sdk.query(). All keyword arguments (both constructor and
    per-call) are forwarded to ClaudeAgentOptions, giving full control over
    tools, turns, environment, and other SDK options.

    For classification or structured output where you don't want the model
    to use filesystem tools, pass tools=[] and max_turns=20::

        lm = AgentLM(tools=[], max_turns=20)

    The model identifier (default "claude-agent-sdk") is for DSPy's internal
    tracking only -- the actual model is determined by the Claude Code CLI.

    Caching: pass a Cachetta instance to persist responses across runs.
    Cachetta wraps the query function as a decorator, so the cache key is
    derived from the prompt argument automatically. Any change to the prompt
    invalidates the cache::

        from cachetta import Cachetta
        lm = AgentLM(cache=Cachetta(path=lambda prompt: f"cache/{prompt}.pkl"))

    Per-call kwargs override constructor kwargs (shallow merge).
    """

    def __init__(
        self,
        model: str = "claude-agent-sdk",
        model_type: str = "chat",
        max_tokens: int = 4096,
        cache: Any = None,
        **kwargs,
    ):
        self.model = model
        self.model_type = model_type
        self.max_tokens = max_tokens
        self.cache = cache
        self.kwargs = kwargs
        self.history: list[dict] = []

        # If cache provided, wrap the query function with cachetta
        if cache is not None:
            self._cached_query = cache.wrap(query_assistant_text)
        else:
            self._cached_query = None

    def forward(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        """Synchronous forward pass. Bridges to the async SDK via run_sync.

        Accepts either a plain string prompt or an OpenAI-style message list.
        Any extra kwargs are merged with constructor kwargs and forwarded to
        ClaudeAgentOptions.
        """
        extracted_prompt = extract_prompt(prompt, messages)
        merged_opts = {**self.kwargs, **kwargs}

        query_fn = self._cached_query or query_assistant_text
        response_text = run_sync(query_fn(extracted_prompt, **merged_opts))

        return self._build_response(extracted_prompt, response_text, kwargs)

    async def aforward(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        """Async forward pass. Calls the SDK directly without threading."""
        extracted_prompt = extract_prompt(prompt, messages)
        merged_opts = {**self.kwargs, **kwargs}

        query_fn = self._cached_query or query_assistant_text
        response_text = await query_fn(extracted_prompt, **merged_opts)

        return self._build_response(extracted_prompt, response_text, kwargs)

    def _build_response(self, prompt: str, response_text: str, kwargs: dict) -> CompletionResponse:
        """Build a CompletionResponse and update history."""
        result = CompletionResponse(
            id=f"claude-agent-{uuid.uuid4().hex[:8]}",
            model=self.model,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content=response_text),
                )
            ],
        )
        self.update_history({"prompt": prompt, "response": result, "kwargs": kwargs})
        return result

    def copy(self, **kwargs) -> AgentLM:
        """Return a copy with updated kwargs."""
        new_kwargs = {**self.kwargs, **kwargs}
        return AgentLM(
            model=self.model,
            model_type=self.model_type,
            max_tokens=self.max_tokens,
            cache=self.cache,
            **new_kwargs,
        )

    def update_history(self, entry: dict[str, Any]) -> None:
        """Append an entry to the history."""
        self.history.append(entry)

    def inspect_history(self, n: int = 1) -> list[dict]:
        """Return the last n history entries."""
        return self.history[-n:]
