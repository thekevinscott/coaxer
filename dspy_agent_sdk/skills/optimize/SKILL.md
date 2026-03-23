---
name: optimize
description: Optimize a DSPy prompt from labeled examples (CSV, TSV, or JSON)
---

# Optimize a DSPy prompt from labeled examples

You are helping the user optimize a classification prompt using DSPy and the Anthropic Agent SDK.

## Input

The user will provide:
1. A file of labeled examples (CSV, TSV, or JSON)
2. A description of the task (e.g., "classify repos as collection or organic")

## Steps

1. **Read the examples file.** Detect the format (CSV, TSV, or JSON) and load all rows.

2. **Identify fields.** Determine which columns are inputs and which are the output label. If ambiguous, ask the user.

3. **Build a DSPy Signature.** Create a `dspy.Signature` subclass with the appropriate `InputField` and `OutputField` declarations. Use the task description as the docstring.

4. **Create DSPy Examples.** Convert each row to a `dspy.Example` with `.with_inputs()` set to the input field names.

5. **Split train/val.** Ask the user how they want to split, or default to 70/30.

6. **Configure the LM.** Use `AgentLM` from `dspy_agent_sdk`:
   ```python
   from dspy_agent_sdk import AgentLM
   lm = AgentLM(tools=[], max_turns=20)
   dspy.configure(lm=lm)
   ```

7. **Choose an optimizer.** Default to `dspy.BootstrapFewShot` for speed. If the user requests more thorough optimization, use `dspy.MIPROv2`.

8. **Define a metric.** For binary/categorical classification, use exact match on the output field. For more complex tasks, ask the user.

9. **Run optimization.**
   ```python
   optimizer = dspy.BootstrapFewShot(metric=metric)
   compiled = optimizer.compile(dspy.Predict(MySignature), trainset=train)
   ```

10. **Save the result.** Write a JSON file with:
    ```json
    {
      "instruction": "the optimized instruction string",
      "demos": [{"input_field": "...", "output_field": "..."}, ...],
      "signature": "input_field -> output_field:type",
      "optimizer": "BootstrapFewShot",
      "num_train": 7,
      "num_val": 3
    }
    ```

11. **Show the user** the optimized instruction and selected demos, and tell them where the JSON was saved.

## Important

- Always use `tools=[]` with AgentLM for classification tasks to prevent filesystem exploration.
- Set `max_turns=20` to allow thinking before structured output.
- The `dspy_agent_sdk` package must be installed: `uv add git+ssh://git@github.com/thekevinscott/dspy-anthropic-agent-sdk.git`
