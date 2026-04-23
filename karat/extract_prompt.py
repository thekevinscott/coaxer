"""Extract a system prompt and user-turn text from DSPy's message formats."""


def extract_prompt(
    prompt: str | None = None,
    messages: list[dict] | None = None,
) -> tuple[str | None, str]:
    """Split a DSPy messages list into (system_prompt, user_text).

    DSPy may pass a simple string prompt or an OpenAI-style message list. The
    Claude Agent SDK wants two things: a ``system_prompt`` argument and a
    single user-turn string. This function separates them:

    - All ``system`` messages are concatenated (joined by a blank line) and
      returned as the first element. If none are present, the first element
      is ``None`` so callers can detect "no system message set".
    - The remaining messages (user + assistant few-shot turns) are flattened
      into a single string. If there's exactly one user message, its content
      is returned verbatim so simple single-turn prompts aren't mangled.
      Otherwise each turn is prefixed with ``role: `` and turns are joined
      by a blank line — preserving multi-turn few-shot demonstrations that
      would otherwise be discarded by ``ClaudeAgentOptions`` (which accepts
      only a single user prompt string).

    A bare ``prompt`` string is returned as ``(None, prompt)``. Empty inputs
    return ``(None, "")``.
    """
    if not messages:
        return None, prompt or ""

    system_contents = [m.get("content", "") for m in messages if m.get("role") == "system"]
    system = "\n\n".join(c for c in system_contents if c) or None

    non_system = [m for m in messages if m.get("role") != "system"]

    if not non_system:
        # Only system messages — fall back to the prompt arg if provided.
        return system, prompt or ""

    if len(non_system) == 1 and non_system[0].get("role") == "user":
        return system, non_system[0].get("content", "")

    user_text = "\n\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in non_system)
    return system, user_text
