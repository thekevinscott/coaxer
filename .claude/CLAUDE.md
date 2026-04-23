# coaxer

Evals-first prompt optimization. Label examples, get better prompts.

## Sandbox

- **All scratch/debug Python scripts must go to `/tmp`**. Never run `python -c` or `python3 -c` inline. Write to `/tmp/coaxer-*.py` and execute that.

## Workflow

- **Always work in a branch or git worktree** -- never commit directly to main
- Work in git worktrees under `.worktrees/` for parallel work, or feature branches for sequential work
- Tie PRs to GitHub issues
- Keep PRs minimal but complete (one self-contained feature)
- Don't add unused code for future PRs

### Issue Tracking (Beads)

Use `bd` (beads) for local issue tracking. One issue per task.

```bash
bd create "title" --description "details"   # Create issue
bd update <id> --status in_progress         # Start work
bd close <id>                               # Done
bd list                                     # Show open issues
```

### PR Checklist

Before considering a PR complete:
1. **CI checks pass** -- monitor with `gh pr checks <pr-number>` or `gh run list`
2. **GPG commits are verified** -- all commits must be signed
3. **No merge conflicts** -- rebase on main if needed
4. **Changelog updated** -- if user-facing changes

## Testing (Red/Green TDD, Outside-In)

1. Write test first (must fail RED)
2. Minimal implementation to pass (GREEN)
3. Refactor if needed

TDD Order: integration tests first, then unit tests.

### Test organization

- **Unit tests** (`coaxer/*_test.py`): colocated, mock everything except the function under test
- **Integration tests** (`tests/integration/`): test multiple modules together with mocked externals (SDK, filesystem). ALL integration tests go here, not colocated.

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
coaxer/                   # Main package
  _internal/              # Private utilities (run_sync, etc.)
  prompt.py               # CoaxPrompt - str subclass, Jinja2 render
  compiler.py             # distill() - label folder -> prompt artifact
  records.py              # Read label folder into Record objects
  schema.py               # Parse/infer _schema.json
  signature.py            # Build DSPy Signature dynamically (internal)
  cli.py                  # CLI entry point (coaxer distill)
  lm.py                   # AgentLM - DSPy LM backed by Agent SDK
  openai_lm.py            # OpenAILM - DSPy LM for OpenAI-compatible endpoints
  for_query.py            # Async generator over SDK query blocks
  query_assistant_text.py # Extract text from assistant responses
  extract_prompt.py       # Normalize DSPy prompt formats
  dataclasses.py          # OpenAI-compatible response types
karat/                    # Deprecated shim package (re-exports from coaxer)
tests/
  fixtures/labels/demo/   # Label-folder fixture used by distill + records tests
  integration/            # Integration tests (mocked SDK)
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
