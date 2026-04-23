# Changelog

## Unreleased

### Added
- `OpenAILM` -- DSPy language model for OpenAI-compatible endpoints (Ollama, vLLM, OpenAI, etc.)

### Fixed
- `AgentLM` now routes the `system` message into `ClaudeAgentOptions.system_prompt` and flattens multi-turn few-shot demos into the user prompt. Previously, `extract_prompt` returned only the last user turn, silently dropping the system message and every demo turn DSPy's `ChatAdapter` had rendered -- so optimized programs sent a minimal prompt to Claude instead of the trained one. Callers can still override by passing `system_prompt` to the constructor or per-call kwargs.

### Changed
- **Breaking (internal):** `karat.extract_prompt.extract_prompt` now returns `tuple[str | None, str]` (system, user_text) instead of a single string. The function is not exported from the package root, but any direct imports will need to unpack the tuple.
