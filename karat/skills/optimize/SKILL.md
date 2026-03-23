---
name: optimize
description: Interactive human-in-the-loop DSPy prompt optimization. Reads a DSPy Signature, samples data, presents examples for labeling, and produces an optimized compiled program.
---

# Optimize a DSPy Prompt

You are running an interactive prompt optimization workflow. The user (or calling agent) points you at a DSPy Signature and a data source. You sample intelligently, collect human labels, run DSPy optimization, and save a compiled program.

## Phase 1: Read the Signature

The user provides a DSPy Signature class -- either a file path with class name (e.g., `myproject/sigs.py:ClassifyRepo`) or an inline description.

Read the signature to understand:
- **Input fields**: what data is available for each example
- **Output fields**: what the model needs to predict
- **Docstring**: the current task description (this becomes the base instruction DSPy optimizes from)

If the user provides a description instead of a file, build a Signature class from it.

## Phase 2: Get Data

Ask the user where the data is. Accept whatever they give you -- a file path (CSV, TSV, JSON, JSONL, Parquet), a SQL query, a Python expression, an API call, a database table name. The calling agent has context on how to source data. Do not assume any particular data format or access pattern.

Load a working set of examples. If the dataset is large, sample ~100 examples for the initial pass.

## Phase 3: Smart Sampling for Labeling

Do NOT just random-sample. Use the LM itself to do a rough classification pass on the working set, then stratify:

1. **Run a quick pass.** Use `AgentLM` with the current (unoptimized) signature to predict labels for all ~100 examples.

2. **Stratify into three groups:**
   - **Likely positive** (5): examples the model confidently labeled as True/positive
   - **Likely negative** (5): examples the model confidently labeled as False/negative
   - **Ambiguous** (5): examples where the model hedged, gave short/uncertain responses, or where the prediction seems borderline

   For non-binary outputs (e.g., `language: str`), sample to cover the distribution of predicted values, with extra weight on rare or uncertain predictions.

3. **Present ambiguous examples first.** These are where human labels add the most value. Easy cases don't teach the model anything -- boundary cases are where prompt tuning matters.

## Phase 4: Collect Labels via TUI

Use `karat label` to collect human labels. You write a JSON file with your pre-populated first-pass labels, the user reviews and corrects them in the TUI in a separate terminal.

1. **Write the labeling file.** Create a JSON file with your sampled examples and pre-populated predictions:

```json
{
  "label_fields": [
    {"name": "is_collection", "labels": ["true", "false"]}
  ],
  "display_fields": ["repo_name", "url", "description"],
  "examples": [
    {"repo_name": "awesome-python", "url": "https://...", "description": "A curated list",
     "is_collection": "true"},
    {"repo_name": "flask", "url": "https://...", "description": "Web framework",
     "is_collection": "false"}
  ]
}
```

For multiple output fields, add more entries to `label_fields`:
```json
"label_fields": [
  {"name": "language", "labels": ["Python", "JavaScript", "Rust", ...]},
  {"name": "is_collection", "labels": ["true", "false"]}
]
```

Pre-populated values (from your Phase 3 rough classification) appear as editable defaults in the TUI. The human corrects mistakes rather than labeling from scratch.

2. **Tell the user to run the TUI** in a separate terminal:
```bash
karat label examples.json --output labeled.json
```

3. **Wait for the user to finish labeling.** The TUI saves results to the output file. The user will tell you when they're done, or you can check if the output file has been written/updated.

4. **Read the labeled output.** Parse the output JSON -- each example will have the label field values filled in (or `null` if skipped).

## Phase 5: Run DSPy Optimization

With labeled examples:

1. **Split train/val.** Default 70/30, or ask the user.

2. **Configure the LM:**
   ```python
   from karat import AgentLM
   import dspy

   lm = AgentLM(tools=[])
   dspy.configure(lm=lm)
   ```

3. **Build DSPy Examples.** Convert labeled data to `dspy.Example` objects with `.with_inputs()` set to the input field names from the Signature.

4. **Define a metric.** For binary/categorical classification, use exact match on the output field. For more complex tasks, ask the user what counts as correct.

5. **Choose an optimizer.** Default to `dspy.BootstrapFewShot` (fast, no extra LLM calls for optimization). If the user wants more thorough optimization, use `dspy.MIPROv2` (generates candidate instructions, evaluates them -- burns more LLM calls).

6. **Run optimization:**
   ```python
   optimizer = dspy.BootstrapFewShot(metric=metric)
   compiled = optimizer.compile(dspy.Predict(MySignature), trainset=train)
   ```

7. **Report results.** Show val accuracy and the optimized instruction.

## Phase 6: Save and Apply

Save the compiled DSPy program as JSON:
```json
{
  "instruction": "the optimized instruction string",
  "demos": [{"input_field": "...", "output_field": "..."}, ...],
  "signature": "input_field -> output_field:type",
  "optimizer": "BootstrapFewShot",
  "num_train": 7,
  "num_val": 3,
  "val_accuracy": 0.92
}
```

Tell the user where the file was saved and how to load it:
```python
compiled = dspy.Predict(MySignature)
compiled.load("path/to/optimized.json")
```

## Important

- Always use `tools=[]` with AgentLM for classification/structured-output tasks to prevent the model from exploring the filesystem instead of classifying.
- The `karat` package must be installed: `uv add git+ssh://git@github.com/thekevinscott/karat.git`
- The ambiguous examples are the most valuable. Do not skip Phase 3 stratification -- random sampling produces worse optimizations.
- This is an interactive workflow, not a batch script. Wait for user input at each labeling step.
