"""Extract a single prompt string from DSPy's message formats."""


def extract_prompt(prompt: str | None = None, messages: list[dict] | None = None) -> str:
    """Extract a single prompt string from prompt or messages.

    DSPy may pass a simple string prompt or an OpenAI-style message list.
    This normalizes both into a single string for the Agent SDK.
    """
    if messages:
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages:
            return user_messages[-1].get("content", "")
        return "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
    return prompt or ""
