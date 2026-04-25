# Changelog

## Unreleased

### Added
- **`notes/environments/{agents,remote}.md` codify per-environment agent workflow.** `agents.md` documents how to detect a remote / managed-agents session via the `CLAUDE_CODE_REMOTE` env var (and `CLAUDE_CODE_REMOTE_SESSION_ID`); `remote.md` is the playbook for those sessions: every unit of work needs a GitHub issue, ends with a PR that auto-closes the issue (`Closes #N`), and the agent must drive CI to green and confirm the PR is mergeable before handing back.
- **Three-level documentation: README, `docs/`, docs site.** README now mirrors the `docs/` folder structure as `##` sections with relative links into `docs/`, while the docs site renders `docs/` 1:1. Each page in `docs/` (and `MIGRATIONS.md`) now carries an `_Online: <url>_` line so an agent or human reading the file offline can find the hosted version. Reasoning: agents don't browse the docs site, so the package itself needs to carry the same structure.
- **`docs/` ships with the wheel under `coaxer/docs/`.** Hatchling `force-include` copies the docs folder (and `MIGRATIONS.md`) into the installed package, so any consumer (or LLM tool with site-packages access) can read the same documentation locally without a network fetch. Sdist `include` is now spelled out so the layout is explicit.
- **`AGENTS.md` at the repo root consolidates contributor instructions.** Moved everything that was previously in `.claude/CLAUDE.md` (PR workflow, testing, code style, commit conventions, project layout) into the agent-agnostic `AGENTS.md` convention so tools beyond Claude Code can pick it up. Root `CLAUDE.md` now just `@`-includes `AGENTS.md` and `putitoutthere/AGENTS.md`.
- **Changelog / migration policy codified in `AGENTS.md`.** Every PR must add a bullet under `## Unreleased`; public-facing changes also require a `MIGRATIONS.md` entry using the 5-section template (summary, required changes, deprecations removed, behavior changes, verification). Opt out of the changelog check with a `skip-changelog: true` commit trailer.
- **`MIGRATIONS.md` is the canonical downstream-consumer upgrade guide.** Repo-root file with a 5-section per-version template (summary, required changes, deprecations removed, behavior changes, verification). Published on the docs site at `/migrations/` via `pymdownx.snippets` so there is a single source of truth.
- **Schema: `backing` field on input entries.** Explicit opt-in for sibling-file resolution (`{"backing": "file"}`) alongside the existing `{"type": "file"}` form. (#27) See [MIGRATIONS.md](MIGRATIONS.md#unreleased--sibling-file-resolution-no-longer-implies-file-on-slash) for upgrade instructions.
- **Compiled prompts now auto-surface enum values.** When `output.type == "enum"`, the compiler appends `Respond with exactly one of: <values>.` to the instructions so callers don't have to stuff format hints into `output.desc`. (#28) See [MIGRATIONS.md](MIGRATIONS.md#unreleased--compiled-prompt-cleanup-and-enum-auto-format) for upgrade instructions.

### Changed
- **`.gitignore`: stopped ignoring `notes/`.** The repo now tracks the `notes/` tree so checked-in agent docs (e.g. `notes/environments/{agents,remote}.md`) are visible to fresh / cloud sessions. Local-only scratch belongs under `tmp/`, which is still ignored.
- **CI now fails PRs that bump the release trailer to `minor` or `major` without updating `MIGRATIONS.md`.** New `migrations` workflow inspects the `release:` trailer in the PR's commit messages (and PR body, for "Squash and merge"); if the bump is `minor` or `major` and `MIGRATIONS.md` wasn't touched, the check fails with a pointer to the 5-section template. Bypass with a `skip-migration: true` trailer for the rare breaking-internal case where a feature/breaking bump has no consumer surface. `release:` of `patch`, `skip`, or omitted continues to skip the check.
- **`.gitignore`: ignore agent worktrees at `.claude/worktrees/`.** Matches the existing `.worktrees` entry; the agent-tool worktree path sits under `.claude/` rather than at the repo root.
- **CI now fails PRs that don't update `CHANGELOG.md`.** Every PR — including internal-only refactors, CI changes, and docs — must add a bullet under `## Unreleased`. Bypass with a `skip-changelog: true` commit trailer (the trailer is honored when present in any commit in the PR or in the PR body for "Squash and merge"). We don't follow semver strictly enough to rely on version numbers, so the changelog is the audit trail.
- **Release pipeline: upgraded to `putitoutthere@0.1.37`.** Dropped the hand-rolled entry-point workarounds now that upstream split the CLI entry into `dist/cli-bin.js` (the GHA bundle + `npm i -g`/`npx` symlink bugs we worked around are both fixed upstream). Bumped the plan + PR dry-run jobs from Node 20 → 24 to clear the deprecation warning. Set `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_COAXER` on the sdist build step so `hatch-vcs` honors putitoutthere's planned version instead of deriving a `0.2.X.devN` suffix from the pre-tag git history.
- **Release config: `putitoutthere.toml` `paths` now includes `CHANGELOG.md`.** Changelog-only edits (and notes landing alongside substantive changes) now naturally trigger a patch release instead of silently being skipped by cascade detection.
- **Breaking: CLI renamed to `coax`.** Replaces `coaxer distill`; the labels folder is now the top-level positional argument (`coax <labels> --out <prompts>`). No shim — the `coaxer` console script is gone. See [MIGRATIONS.md](MIGRATIONS.md#03x-public-api-replaced) for upgrade instructions.
- **Breaking: `CoaxPrompt` renamed to `CoaxedPrompt`.** Import is now `from coaxer import CoaxedPrompt`. See [MIGRATIONS.md](MIGRATIONS.md#03x-public-api-replaced) for upgrade instructions.
- **Release pipeline: swapped to [putitoutthere](https://github.com/thekevinscott/put-it-out-there).** Releases are now driven by a `release: <patch|minor|major|skip>` trailer on the merge commit (see `putitoutthere/AGENTS.md`). The cron-based daily patch-bump workflow and manual minor-release dispatch have been removed; a single `release.yml` handles plan/build/publish on push-to-main, with `putitoutthere-check.yml` running a PR dry-run.
- **Breaking: public API replaced.** Coaxer no longer exposes DSPy. See [MIGRATIONS.md](MIGRATIONS.md#03x-public-api-replaced) for upgrade instructions. The new shape is:
  - A dir-per-record label folder (`labels/<name>/0001/record.json` + sibling files).
  - A `coax <labels> --out <prompts>` CLI that compiles the folder into `prompt.jinja` + `meta.json` + `dspy.json` + `history.jsonl`.
  - A `CoaxedPrompt(path)` `str` subclass that loads `prompt.jinja` and renders it via Jinja2 `StrictUndefined` at call time (`p(readme=..., stars=...)`).
- Templating switched to Jinja2 (`{{ field }}` slots avoid JSON/code brace collisions).
- Optimizer switched to DSPy 3 + GEPA (opt-in via `--optimizer gepa`). The default (`--optimizer none`) emits a schema-derived template without network access.
- `pyproject.toml`: added `jinja2>=3.0`; dropped `textual>=3.0` and the `curtaincall` dev dep; bumped `dspy>=3.0` (for GEPA).

### Removed
- **`karat` shim package.** The re-export shim introduced when the package was renamed to `coaxer` has been removed. Migration: `from karat import X` → `from coaxer import X`.
- **Labeling TUI** (`coaxer/tui/`, `coaxer label` CLI, `docs/guide/labeling-tui.md`). Labeling happens in an editor or via a Claude Code agent writing the folder directly.
- **`/optimize` skill** (`coaxer install` CLI, `coaxer/skills/`, `docs/guide/optimize-skill.md`). The skill's workflow is now `coax`.
- **`load_predict`** (`coaxer.load_predict`, `docs/api/load-predict.md`). DSPy is no longer part of the public surface.

### Fixed
- **Release pipeline: use setuptools-scm's global `SETUPTOOLS_SCM_PRETEND_VERSION` env var.** The per-package `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_COAXER` added in the previous release is silently ignored by hatch-vcs (verified locally), which caused `0.2.14` to ship to PyPI as `0.2.14.dev2`. Switching to the global variant makes hatch-vcs honor putitoutthere's planned version as intended.
- **GEPA optimizer: metric now accepts DSPy 3's required 5-arg signature.** Previously `coax --optimizer gepa` raised `TypeError: GEPA metric must accept five arguments` on any run; the inner metric in `_run_gepa` has been updated to `(gold, pred, trace, pred_name, pred_trace)` per DSPy 3's `inspect.signature(...).bind` check. No public API change. (#26)
- **Sibling-file resolution no longer false-positives on scalar inputs containing `/`.** Values like `"repo_name": "expo/skills"` (GitHub `owner/name`) or `"date": "2024/01/15"` previously raised `FileNotFoundError: Sibling file not found`. Resolution is now driven by `_schema.json` (`type: "file"` or `backing: "file"`) rather than a slash/extension heuristic, with implicit resolution preserved when the value is a plain filename that exists on disk. (#27) See [MIGRATIONS.md](MIGRATIONS.md#unreleased--sibling-file-resolution-no-longer-implies-file-on-slash) for upgrade instructions.
- **Rendered `prompt.jinja` no longer has `..` punctuation artifacts or a duplicate `Inputs:` header.** `_build_instructions` now joins parts with `\n\n` instead of `". "`, and the inline field-description block is titled `Field descriptions:` so it doesn't shadow the template's `Inputs:` slot block. (#28) See [MIGRATIONS.md](MIGRATIONS.md#unreleased--compiled-prompt-cleanup-and-enum-auto-format) for upgrade instructions.

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
