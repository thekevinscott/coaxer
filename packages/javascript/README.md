# coaxer

Label examples. Derive the prompt. Consume it as a string.

Full docs: <https://thekevinscott.github.io/coaxer/>

## Install

```bash
npm install coaxer zod
```

`coaxer` peerDeps `zod@^4`. The `coax` CLI is shipped by the Python package — install it with `uv add coaxer` (or have it on `PATH`) if you want to compile label folders into prompt artifacts.

## Quick start

```bash
coax labels/repo-classification --out prompts/repo-classification
```

```ts
import { CoaxedPrompt } from "coaxer";

const p = new CoaxedPrompt("prompts/repo-classification");
const filled = p({ readme: newReadme, stars: 1200 });
```

## CoaxedPrompt

`new CoaxedPrompt(path, bound?)` reads the compiled artifact. The instance is callable; `` `${p}` `` returns the raw template; `p({...})` renders it. Missing variables raise `MissingVariableError`. Bind defaults at construction; call-time vars override. `p.fields` lists the input variables the template expects.

```ts
const p = new CoaxedPrompt("prompts/repo-classification", { role: "classifier" });
const filled = p({ role: "summarizer", readme, stars }); // call-time wins
p.fields; // ['readme', 'stars', 'role']
```

## Structured output

`p.responseFormat()` returns a Zod schema for the compiled output, ready to hand to OpenAI's `.parse()` or Anthropic's tool-use.

```ts
import { zodResponseFormat } from "openai/helpers/zod";

const resp = await openai.chat.completions.parse({
  model: "gpt-4o",
  messages: [{ role: "user", content: `${p({ readme, stars })}` }],
  response_format: zodResponseFormat(p.responseFormat(), "Output"),
});
```

```ts
import { zodToJsonSchema } from "zod-to-json-schema";

const schema = p.responseFormat();
const resp = await anthropic.messages.create({
  model: "claude-sonnet-4-5",
  messages: [{ role: "user", content: `${p({ readme, stars })}` }],
  tools: [{ name: "respond", input_schema: zodToJsonSchema(schema) }],
  tool_choice: { type: "tool", name: "respond" },
});
```

## License

MIT
