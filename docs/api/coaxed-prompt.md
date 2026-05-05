# `CoaxedPrompt`

_Online: <https://thekevinscott.github.io/coaxer/api/coaxed-prompt/>_

A compiled prompt loaded from a `coax`-produced directory.

=== "Python"

    ```python
    from coaxer import CoaxedPrompt

    p = CoaxedPrompt("prompts/repo-classification", role="classifier")
    filled = p(readme=new_readme, stars=1200)
    ```

=== "TypeScript"

    ```ts
    import { CoaxedPrompt } from "coaxer";

    const p = new CoaxedPrompt("prompts/repo-classification", { role: "classifier" });
    const filled = p({ readme: newReadme, stars: 1200 });
    ```

## Constructor

=== "Python"

    ```python
    CoaxedPrompt(path: str | Path, **bound: Any)
    ```

    - `path` — folder produced by `coax`.
    - `**bound` — default values bound at construction time. Overridden by call-time keyword arguments.

    `CoaxedPrompt` is a `str` subclass; instances carry the raw template as their string value, so they drop in anywhere a string is accepted (logging, LLM SDK `messages`, external template engines).

=== "TypeScript"

    ```ts
    new CoaxedPrompt(path: string, bound?: Record<string, unknown>)
    ```

    - `path` — folder produced by `coax`.
    - `bound` — default values bound at construction time. Overridden by call-time variables.

    The instance is callable; template-literal interpolation (`` `${p}` ``) returns the raw template, so instances drop in anywhere JS coerces a value to a string.

## Raw template

=== "Python"

    `str(p)` returns the raw template, including `{{ field }}` slots.

    ```python
    assert isinstance(p, str)
    assert "{{ readme }}" in str(p)
    ```

=== "TypeScript"

    Template-literal interpolation (`` `${p}` ``) returns the raw template, including `{{ field }}` slots.

    ```ts
    console.assert(`${p}`.includes("{{ readme }}"));
    ```

## Render

Calling the instance renders the template with the merged variables (bound defaults plus call-time variables; call-time wins). Missing variables raise `MissingVariableError`.

=== "Python"

    ```python
    filled = p(readme="# hi", stars=10)        # ok
    p()                                         # raises MissingVariableError
    ```

=== "TypeScript"

    ```ts
    const filled = p({ readme: "# hi", stars: 10 });   // ok
    p({});                                              // throws MissingVariableError
    ```

## Fields

`p.fields` is the list of input variables the template expects. It's parsed from the template on first access and cached on the instance.

=== "Python"

    ```python
    p.fields  # ['readme', 'description', 'stars']
    ```

=== "TypeScript"

    ```ts
    p.fields;  // ['readme', 'description', 'stars']
    ```

## Structured output

A schema for the compiled output, ready to hand to OpenAI's `.parse()` or Anthropic's tool-use. Cached after first access.

=== "Python"

    `p.response_format` is a Pydantic model class.

    ```python
    Model = p.response_format
    Model.model_json_schema()
    # {'type': 'object', 'properties': {'is_collection': {'type': 'boolean'}}, ...}
    ```

=== "TypeScript"

    `p.responseFormat()` returns a Zod schema.

    ```ts
    const schema = p.responseFormat();
    ```

### OpenAI

=== "Python"

    ```python
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.parse(
        model="gpt-4o",
        messages=[{"role": "user", "content": p(readme=..., stars=...)}],
        response_format=p.response_format,
    )
    result = resp.choices[0].message.parsed
    ```

=== "TypeScript"

    ```ts
    import { zodResponseFormat } from "openai/helpers/zod";

    const resp = await openai.chat.completions.parse({
      model: "gpt-4o",
      messages: [{ role: "user", content: `${p({ readme, stars })}` }],
      response_format: zodResponseFormat(p.responseFormat(), "Output"),
    });
    const result = resp.choices[0].message.parsed;
    ```

### Anthropic

=== "Python"

    ```python
    import anthropic

    Model = p.response_format
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": p(readme=..., stars=...)}],
        tools=[{
            "name": "respond",
            "input_schema": Model.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": "respond"},
    )
    parsed = Model.model_validate(resp.content[0].input)
    ```

=== "TypeScript"

    ```ts
    import { zodToJsonSchema } from "zod-to-json-schema";

    const schema = p.responseFormat();
    const resp = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      messages: [{ role: "user", content: `${p({ readme, stars })}` }],
      tools: [{ name: "respond", input_schema: zodToJsonSchema(schema) }],
      tool_choice: { type: "tool", name: "respond" },
    });
    const parsed = schema.parse(resp.content[0].input);
    ```
