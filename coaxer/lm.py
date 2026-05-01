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

        lm = AgentLM(tools=[])

    The model identifier (default "claude-agent-sdk") is for DSPy's internal
    tracking only -- the actual model is determined by the Claude Code CLI.

    Per-call kwargs override constructor kwargs (shallow merge).
    """

    def __init__(
        self,
        model: str = "claude-agent-sdk",
        model_type: str = "chat",
        max_tokens: int = 4096,
        **kwargs,
    ):
        # Claude Code refuses to launch when CLAUDECODE is inherited from the
        # parent, so every AgentLM call from inside a Claude Code session
        # (e.g. `coax --optimizer gepa` running each rollout as a nested
        # SDK query) would fail. Default env to clear CLAUDECODE; callers
        # who really need to inherit it can pass env={"CLAUDECODE": "1"}.
        env = dict(kwargs.get("env") or {})
        env.setdefault("CLAUDECODE", "")
        kwargs["env"] = env

        self.model = model
        self.model_type = model_type
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        self.history: list[dict] = []

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
        user_prompt, merged_opts = self._prepare_call(prompt, messages, kwargs)

        response_text = run_sync(query_assistant_text(user_prompt, **merged_opts))

        return self._build_response(user_prompt, response_text, kwargs)

    async def aforward(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        """Async forward pass. Calls the SDK directly without threading."""
        user_prompt, merged_opts = self._prepare_call(prompt, messages, kwargs)

        response_text = await query_assistant_text(user_prompt, **merged_opts)

        return self._build_response(user_prompt, response_text, kwargs)

    def _prepare_call(
        self,
        prompt: str | None,
        messages: list[dict] | None,
        kwargs: dict,
    ) -> tuple[str, dict]:
        """Extract user prompt text and build merged SDK options.

        Routes any ``system`` turn in ``messages`` into the
        ``system_prompt`` option of ClaudeAgentOptions, unless the caller
        has already supplied ``system_prompt`` via constructor or per-call
        kwargs (in which case the caller wins).
        """
        system, user_prompt = extract_prompt(prompt, messages)
        merged_opts = {**self.kwargs, **kwargs}
        if system and "system_prompt" not in merged_opts:
            merged_opts["system_prompt"] = system
        return user_prompt, merged_opts

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
            **new_kwargs,
        )

    def update_history(self, entry: dict[str, Any]) -> None:
        """Append an entry to the history."""
        self.history.append(entry)

    def inspect_history(self, n: int = 1) -> list[dict]:
        """Return the last n history entries."""
        return self.history[-n:]
