# karat

Evals-first prompt optimization. Label examples, get better prompts.

## Sandbox

- **All scratch/debug Python scripts must go to `/tmp`**. Never run `python -c` or `python3 -c` inline. Write to `/tmp/karat-*.py` and execute that.

## Workflow

- Work in git worktrees under `.worktrees/`, tie PRs to GitHub issues
- Never commit directly to main -- always create a PR
- Keep PRs minimal but complete (one self-contained feature)
- Don't add unused code for future PRs

## Testing (Red/Green TDD, Outside-In)

1. Write test first (must fail RED)
2. Minimal implementation to pass (GREEN)
3. Refactor if needed

TDD Order: integration tests first, then unit tests.

### Test organization

- **Unit tests** (`karat/*_test.py`): colocated, mock everything except the function under test
- **Integration tests** (`tests/integration/`): test multiple modules together with mocked externals (SDK, filesystem). ALL integration tests go here, not colocated.
- **E2E tests** (`tests/e2e/`): curtaincall-based, real PTY, test actual user experience

### Running Tests

```bash
uv run just test-unit        # Unit tests (colocated *_test.py)
uv run just test-integration # Integration tests
uv run just test-cov         # Unit tests with coverage
uv run just ci               # Full local CI (lint + format + typecheck + tests)
```

## Code Style

- **One function per file** -- `extract_prompt.py` contains `extract_prompt()`
- **Multi-function -> package** -- Promote to directory with `__init__.py`
- **Colocated tests** -- `foo.py` -> `foo_test.py`
- **Test naming** -- Files end in `_test.py` (not `test_*.py`)
- **Docstrings**: Skip Args/Returns/Raises; use for *why*, not *how*
- **Type hints**: Prefer fixing issues over `# type: ignore`
- **Module organization**: `_internal/` for private utilities

## Commit Convention (Conventional Commits)

- `feat:` -- New user-facing functionality
- `fix:` -- Bug fixes
- `test:` -- Test additions
- `chore:` -- CI, tooling, maintenance
- `refactor:` -- Code restructuring
- `docs:` -- Documentation

## Project Structure

```
karat/                   # Main package
  _internal/             # Private utilities (run_sync, etc.)
  skills/optimize/       # /optimize skill (SKILL.md, installed via CLI)
  lm.py                  # AgentLM - DSPy LM backed by Agent SDK
  load_predict.py        # Load optimized DSPy programs with fallback
  tui.py                 # Textual labeling TUI (multi-field, pre-population)
  cli.py                 # CLI entry point (karat install, karat label)
  for_query.py           # Async generator over SDK query blocks
  query_assistant_text.py # Extract text from assistant responses
  extract_prompt.py      # Normalize DSPy prompt formats
  dataclasses.py         # OpenAI-compatible response types
tests/
  integration/           # Integration tests (TUI pilot, mocked SDK)
  e2e/                   # End-to-end tests (subprocess CLI)
```

## Key Commands

```bash
uv run just lint          # Ruff lint
uv run just format        # Ruff format
uv run just typecheck     # ty type check
uv run just test-unit     # pytest (colocated tests)
uv run just ci            # Full CI pipeline
uv run just build         # Build package
```
