# Changelog

## Unreleased

### Changed
- **Breaking: public API replaced.** Coaxer no longer exposes DSPy. The new shape is:
  - A dir-per-record label folder (`labels/<name>/0001/record.json` + sibling files).
  - A `coaxer distill <labels> --out <prompts>` CLI that compiles the folder into `prompt.jinja` + `meta.json` + `dspy.json` + `history.jsonl`.
  - A `CoaxPrompt(path)` `str` subclass that loads `prompt.jinja` and renders it via Jinja2 `StrictUndefined` at call time (`p(readme=..., stars=...)`).
- Templating switched to Jinja2 (`{{ field }}` slots avoid JSON/code brace collisions).
- Optimizer switched to DSPy 3 + GEPA (opt-in via `--optimizer gepa`). The default (`--optimizer none`) emits a schema-derived template without network access.
- `pyproject.toml`: added `jinja2>=3.0`; dropped `textual>=3.0` and the `curtaincall` dev dep; bumped `dspy>=3.0` (for GEPA).

### Removed
- **Labeling TUI** (`coaxer/tui/`, `coaxer label` CLI, `docs/guide/labeling-tui.md`). Labeling happens in an editor or via a Claude Code agent writing the folder directly.
- **`/optimize` skill** (`coaxer install` CLI, `coaxer/skills/`, `docs/guide/optimize-skill.md`). The skill's workflow is now `coaxer distill`.
- **`load_predict`** (`coaxer.load_predict`, `docs/api/load-predict.md`). DSPy is no longer part of the public surface.

### Migration
- `from coaxer import load_predict` → use `CoaxPrompt("prompts/<name>")` after running `coaxer distill`.
- `coaxer label` → label folder is edited directly (JSON + sibling files) or populated by an agent.
- `coaxer install` → no replacement; skill is gone.

## 0.2.x

### Changed
- **Renamed package from `karat` to `coaxer`.** Install with `uv add coaxer`. Update imports to `from coaxer import ...`. The repository has moved to https://github.com/thekevinscott/coaxer.

### Deprecated
- The `karat` package remains as a thin shim that re-exports from `coaxer` and emits a `DeprecationWarning`. The shim will be removed in a future release; migrate to `coaxer`.

### Added
- `OpenAILM` -- DSPy language model for OpenAI-compatible endpoints (Ollama, vLLM, OpenAI, etc.)

### Fixed
- `AgentLM` now routes the `system` message into `ClaudeAgentOptions.system_prompt` and flattens multi-turn few-shot demos into the user prompt. Previously, `extract_prompt` returned only the last user turn, silently dropping the system message and every demo turn DSPy's `ChatAdapter` had rendered -- so optimized programs sent a minimal prompt to Claude instead of the trained one. Callers can still override by passing `system_prompt` to the constructor or per-call kwargs.
- **Breaking (internal):** `coaxer.extract_prompt.extract_prompt` now returns `tuple[str | None, str]` (system, user_text) instead of a single string. The function is not exported from the package root, but any direct imports will need to unpack the tuple.
