"""DSPy language models for Claude Code and OpenAI-compatible endpoints.

AgentLM routes calls through the Anthropic Agent SDK (Claude Code).
OpenAILM calls any OpenAI-compatible chat completion API (Ollama, vLLM,
OpenAI, etc.).

Quick start with Claude Code::

    import dspy
    from karat import AgentLM

    lm = AgentLM()
    dspy.configure(lm=lm)

Quick start with Ollama::

    from karat import OpenAILM

    lm = OpenAILM(model="llama3")
    dspy.configure(lm=lm)

Quick start with OpenAI::

    lm = OpenAILM(model="gpt-4o", base_url="https://api.openai.com/v1", api_key="sk-...")

Load optimized programs saved by the /optimize skill::

    from karat import load_predict
    classify = load_predict(ClassifyRepo, path="data/optimized.json")
"""

from .lm import AgentLM
from .load_predict import load_predict
from .openai_lm import OpenAILM

__all__ = [
    "AgentLM",
    "OpenAILM",
    "load_predict",
]
