# Agent environments

Different runtime environments call for different workflows. Before doing
anything else, agents should detect which environment they're running in and
load the matching playbook.

## Detecting a remote / managed environment

Claude Code sets the following environment variables automatically when the
session is running in a cloud / managed-agents container (Claude Code on the
web, the Managed Agents API, etc.):

| Variable                       | Meaning                                                |
| ------------------------------ | ------------------------------------------------------ |
| `CLAUDE_CODE_REMOTE`           | `"true"` when the session is running as a cloud session |
| `CLAUDE_CODE_REMOTE_SESSION_ID`| The current cloud session's ID                          |

If `CLAUDE_CODE_REMOTE` is set to `true` (or `CLAUDE_CODE_REMOTE_SESSION_ID`
is non-empty), the agent is in a remote environment. **Read
[`remote.md`](remote.md) before starting work** — it overrides the local
defaults in the repo's top-level `AGENTS.md` (e.g. "don't open a PR unless I
ask").

Quick check from a shell:

```bash
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
    cat notes/environments/remote.md
fi
```

## Local / interactive sessions

If neither of those variables is set, you're in a local terminal session with
the human in the loop. Follow the defaults in the top-level `AGENTS.md` —
notably, **don't open a PR unless asked**.
