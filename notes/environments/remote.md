# Remote environment playbook

This file applies whenever `CLAUDE_CODE_REMOTE=true` (Claude Code on the web,
Managed Agents API, or any other cloud-hosted session). See
[`agents.md`](agents.md) for the detection logic.

In a remote session there is no human at a terminal to push branches or click
buttons. The session's only durable output is what lands in GitHub, so every
unit of work must end as a merge-ready pull request.

## The contract

Every piece of work in a remote session must satisfy **all** of the following
before the session ends:

### 1. A GitHub issue exists for the work

- One issue per unit of work. If the user's prompt covers several independent
  tasks, file one issue per task.
- If the user referenced an existing issue (`#123`, a GitHub URL), use that
  one. Otherwise, create a new issue *first* describing the problem or
  feature, then start work.
- Keep the issue tightly scoped — it must be the thing the PR will close.

### 2. A pull request exists that closes the issue

- Open a PR against `main` once the branch is ready. Don't wait to be asked —
  in a remote session, opening the PR *is* the deliverable.
- The PR description must contain a GitHub auto-close keyword referencing the
  issue, so the issue closes automatically on merge:

  ```
  Closes #123
  ```

  Accepted keywords: `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`,
  `resolve`, `resolves`, `resolved`. Use `Closes #N` by default.
- One PR per issue. If scope grew mid-work, split into additional issues +
  PRs rather than bundling.

### 3. CI is green

- After pushing, watch the PR's checks until they finish.
- If a check fails, **fix the underlying problem** — push a follow-up commit
  and wait again. Do not bypass hooks (`--no-verify`), force-merge, or close
  the PR to make the failure go away.
- Only consider the work complete once every required check reports success.

### 4. The PR is mergeable

- Confirm GitHub reports the PR as mergeable (no conflicts with `main`).
- If `main` has moved and produced a conflict, rebase or merge `main` into
  the branch, resolve the conflicts, and re-push. Re-verify CI after the
  rebase — green checks before the rebase don't carry over.
- Do **not** merge the PR yourself unless the user explicitly asked. Leaving
  the PR green, mergeable, and tied to its issue is the goal.

## End-of-session report

When you hand control back, the final message should include:

- The issue number(s) you opened or used.
- The PR number / URL.
- The CI status (all green) and mergeable state.

If any of those four conditions can't be met (e.g. CI is failing in a way you
can't fix, or there are conflicts that need a human call), say so explicitly
in the final message rather than declaring the work done.
