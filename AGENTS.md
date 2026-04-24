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

### Opening PRs

- **Local sessions:** don't open a PR unless I ask.
- **Remote / cloud sessions (Claude Code on the web, sandboxed environments where I can't push from my own machine):** you *should* open a PR once the branch is ready. Push first, then open it against `main` with a summary and test plan. This is the default output of a remote session — waiting for me to ask defeats the point.

### PR Checklist

Before considering a PR complete:
1. **CI checks pass** -- monitor with `gh pr checks <pr-number>` or `gh run list`
2. **GPG commits are verified** -- all commits must be signed
3. **No merge conflicts** -- rebase on main if needed
4. **CHANGELOG.md updated** -- **every PR** adds at least one bullet under `## Unreleased`. No exceptions: bug fixes, refactors, CI, docs, internal-only. We don't follow semver strictly enough to rely on version numbers as the signal, so the audit trail lives in the changelog. Enforced by the `changelog` CI job.
   - **Bypass:** add the trailer `skip-changelog: true` to the PR's merge-commit body (or to every commit in a rebase-merge branch) to skip the check. Use sparingly — dependabot bumps, trivial typo fixes inside docs where the CHANGELOG itself is the touched file, etc. If in doubt, add a line to the changelog.
5. **MIGRATIONS.md updated** -- if the PR changes any public-facing surface (see *Scope* below), add a versioned entry to `MIGRATIONS.md` using the template in the next section.

### Changelog format

- Sections under `## Unreleased` follow [Keep a Changelog](https://keepachangelog.com): `### Added`, `### Changed`, `### Deprecated`, `### Removed`, `### Fixed`, `### Security`.
- Each bullet starts with a bold lead-in summarizing the change, then explains the *why* in 1-2 sentences. See the existing `## Unreleased` entries for the expected voice.
- Reference the PR/issue number at the end of the bullet when relevant (`(#27)`).
- When the change ships with a migration entry, cross-link: `See [MIGRATIONS.md](MIGRATIONS.md#<anchor>).`

### Migration guide (MIGRATIONS.md)

`MIGRATIONS.md` at the repo root is the **source of truth** for downstream-consumer upgrade instructions. It's also published on the docs site (mkdocs pulls it in directly — do not duplicate content; edit `MIGRATIONS.md` and the docs page updates on the next build).

Each migration entry is scoped to the release that introduced the change and uses this template:

```markdown
## <version-or-unreleased> — <short slug>

### (a) Summary
One paragraph: what broke, why the change was made, who is affected.

### (b) Required changes
Table of before/after snippets for every public-facing touch point: config,
CLI invocation, action inputs, imports, function signatures.

| Area        | Before                | After                  |
| ----------- | --------------------- | ---------------------- |
| Import      | `from karat import X` | `from coaxer import X` |
| CLI command | `coaxer distill ...`  | `coax ...`             |

### (c) Deprecations removed
List anything previously emitting a `DeprecationWarning` that is now fully
gone. If nothing, write "None."

### (d) Behavior changes without code changes
Same API, different runtime behavior: tag formats, exit codes, default values,
file-layout assumptions, network vs. offline behavior, etc. If nothing, write
"None."

### (e) Verification
The exact command a consumer runs to confirm the upgrade worked, plus the
expected output (or the error that proves they forgot a step). Prefer a
dry-run / non-destructive check.
```

Mark the corresponding CHANGELOG bullet in `### Changed` / `### Removed` / `### Deprecated` with **Breaking:** when the migration is required for consumers to keep working.

**Scope -- what counts as public-facing:**
- Anything exported from `coaxer/__init__.py`.
- The `coax` CLI surface: flags, positional args, exit codes, stdout/stderr shape.
- The label-folder layout: `_schema.json`, `record.json`, sibling-file conventions.
- The compiled artifact layout: `prompt.jinja`, `meta.json`, `dspy.json`, `history.jsonl`.
- The `AgentLM` / `OpenAILM` constructor kwargs and return shape.

Changes to any of these require a `MIGRATIONS.md` entry even if the `release:` trailer is `patch`.

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

### Trailers

- `release: <patch|minor|major|skip>` -- determines the release bump on merge. See `putitoutthere/AGENTS.md` for scoping and semantics.
- `skip-changelog: true` -- bypass the `changelog` CI job for this PR. Use rarely.

## Project Structure

```
coaxer/                   # Main package
  _internal/              # Private utilities (run_sync, etc.)
  prompt.py               # CoaxedPrompt - str subclass, Jinja2 render
  compiler.py             # distill() - label folder -> prompt artifact
  records.py              # Read label folder into Record objects
  schema.py               # Parse/infer _schema.json
  signature.py            # Build DSPy Signature dynamically (internal)
  cli.py                  # CLI entry point (coax)
  lm.py                   # AgentLM - DSPy LM backed by Agent SDK
  openai_lm.py            # OpenAILM - DSPy LM for OpenAI-compatible endpoints
  for_query.py            # Async generator over SDK query blocks
  query_assistant_text.py # Extract text from assistant responses
  extract_prompt.py       # Normalize DSPy prompt formats
  dataclasses.py          # OpenAI-compatible response types
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
