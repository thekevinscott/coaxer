# coaxer

_Online: <https://thekevinscott.github.io/coaxer/>_

Label examples. Derive the prompt. Consume it as a string.

The prompt is a build artifact; your labeled examples are the source of truth. When the prompt drifts, add more examples and recompile.

## Install

=== "Python"

    ```bash
    uv add coaxer
    ```

=== "TypeScript"

    ```bash
    npm install coaxer
    ```

## Quick start

Label a handful of examples in a folder (see [Getting Started](guide/getting-started.md) for the shape), then:

```bash
coax labels/repo-classification --out prompts/repo-classification
```

Use the compiled prompt:

=== "Python"

    ```python
    from coaxer import CoaxedPrompt

    p = CoaxedPrompt("prompts/repo-classification")
    filled = p(readme=new_readme, stars=1200)
    ```

=== "TypeScript"

    ```ts
    import { CoaxedPrompt } from "coaxer";

    const p = new CoaxedPrompt("prompts/repo-classification");
    const filled = p({ readme: newReadme, stars: 1200 });
    ```

## Core concepts

- **Label folder** — one directory per record. `record.json` holds scalar fields; sibling files (`readme.md`, `logo.png`) carry large text or binary inputs.
- **`coax`** — reads the folder, builds a DSPy signature internally, optionally runs GEPA, writes a prompt artifact.
- **`CoaxedPrompt(path)`** — a `str` subclass in Python (callable instance in TS). The raw template is the string value; calling renders it. Drops in anywhere a string is accepted. Exposes a structured-output schema (`p.response_format` / `p.responseFormat()`) for OpenAI's `.parse()` and Anthropic's tool-use.
- **`AgentLM` / `OpenAILM`** — LLM backends for the optional compile-time optimizer. See the [API reference](api/agent-lm.md).
