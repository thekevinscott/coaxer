# e2e tests

End-to-end tests for the JavaScript package. Empty for now — this directory carries the policy so the next agent doesn't have to ask.

## Scope

**E2E tests exercise the published `coax` CLI binary against a real LLM, with no mocking.** They are the only place real-LLM calls happen in this package.

A passing e2e run proves the full user-facing story:

1. The `coax` binary (the JS shim that spawns the Python CLI) accepts argv, runs distill, and writes a prompt artifact.
2. `CoaxedPrompt` loads the artifact, renders with bound + call-time variables, and exposes a Zod schema via `responseFormat()`.
3. The rendered prompt + schema produce a structured response from a real provider (OpenAI's `.parse()` or Anthropic's tool-use).

## Out of scope

- Anything mocked (`spawn`, `fetch`, `fs`). That's integration territory.
- Library-only paths that don't touch the binary. Those belong under `tests/integration/`.
- Python-side coverage (the upstream `tests/e2e/cli/` already drives the Python `coax` end-to-end against Anthropic).

## Running

E2E is **not** part of CI — costs money, depends on live provider behavior. Run locally before declaring a PR ready when the change touches the SDK-contract surface (constructor shape, `responseFormat()` mapping, the `coax` binary's argv pass-through).

```bash
npm run test:e2e   # to be added; not wired up yet
```

## Running locally

```bash
# from packages/javascript/
npm run test:e2e
```

The e2e test spawns the built `dist/bin.js`, which itself spawns the Python `coax` CLI. Make sure `coax` is reachable on `PATH` (e.g. `source <repo>/.venv/bin/activate`). The test auto-detects `.venv/bin/coax` and `.venv-313/bin/coax` at the repo root; override with `COAXER_E2E_COAX_BIN_DIR` if your `coax` lives elsewhere.

LLM access rides on the local Claude Code session via `@anthropic-ai/claude-agent-sdk` — no extra credentials needed when run from a Claude Code CLI / agent environment.
