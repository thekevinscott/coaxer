"""DSPy language model backed by the Anthropic Agent SDK (Claude Code).

This package provides AgentLM, a drop-in DSPy language model that routes
all LLM calls through the Anthropic Agent SDK. No API key is needed --
it uses your existing Claude Code authentication.

Quick start::

    import dspy
    from dspy_agent_sdk import AgentLM

    lm = AgentLM()
    dspy.configure(lm=lm)

    predict = dspy.Predict("question -> answer")
    result = predict(question="What is 2+2?")

For classification and structured output, disable tools to prevent the
model from exploring the filesystem::

    lm = AgentLM(tools=[], max_turns=20)

All keyword arguments are passed through to ClaudeAgentOptions (tools,
max_turns, allowed_tools, disallowed_tools, env, etc.).

Optional caching via cachetta (decorator-based, wraps the query function)::

    from cachetta import Cachetta
    cache = Cachetta(path=lambda prompt, **kw: f"cache/{prompt}.pkl", duration="7d")
    lm = AgentLM(cache=cache)
"""

from .lm import AgentLM

__all__ = [
    "AgentLM",
]
