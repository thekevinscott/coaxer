"""Label examples, derive prompts.

Compile a label folder into a reusable prompt::

    coaxer distill labels/repo-classification --out prompts/repo-classification

Use the compiled prompt as a drop-in `str`::

    from coaxer import CoaxPrompt

    p = CoaxPrompt("prompts/repo-classification")
    filled = p(readme=new_readme, stars=1200)

`AgentLM` and `OpenAILM` back the compile step and are also available for
direct use. `AgentLM` routes through the Anthropic Agent SDK (Claude Code);
`OpenAILM` calls any OpenAI-compatible endpoint (Ollama, vLLM, OpenAI).
"""

from coaxer.lm import AgentLM
from coaxer.openai_lm import OpenAILM
from coaxer.prompt import CoaxPrompt

__all__ = [
    "AgentLM",
    "CoaxPrompt",
    "OpenAILM",
]
