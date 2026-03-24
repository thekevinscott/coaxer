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

**IMPORTANT: If the user provides their own examples directly (not a large dataset), skip Phase 3 stratification entirely.** Only run the LM classification pass when you have a larger dataset and need to intelligently select which examples to label. If the user gives you, say, 3-15 examples and asks you to create a labeling file, just use all their examples directly.

## Phase 4: Collect Labels via TUI

Use `karat label` to collect human labels. You write a JSON file with the examples (and optionally pre-populated first-pass labels), the user reviews and corrects them in the TUI in a separate terminal.

### Step 1: Write the labeling file

**╔══════════════════════════════════════════════════════════════╗**
**║ MANDATORY RULE #1: ALWAYS USE THE Write TOOL.              ║**
**║ Create a BRAND NEW file. NEVER Read the target path first. ║**
**║ NEVER use the Edit tool. NEVER check if the file exists.   ║**
**║ NEVER say "file already exists" or "already has the right  ║**
**║ content." You MUST call the Write tool every single time.  ║**
**╚══════════════════════════════════════════════════════════════╝**

**╔══════════════════════════════════════════════════════════════╗**
**║ MANDATORY RULE #2: ABSOLUTE FILE PATHS ONLY.               ║**
**║ Run `pwd` via Bash FIRST to get current working directory.  ║**
**║ Use full absolute path (e.g., /home/user/project/file.json)║**
**║ NEVER use relative paths like "file.json".                 ║**
**╚══════════════════════════════════════════════════════════════╝**

**╔══════════════════════════════════════════════════════════════╗**
**║ MANDATORY RULE #3: "No pre-populated labels" means OMIT    ║**
**║ the label key ENTIRELY from example objects. Do NOT use     ║**
**║ null. Do NOT use empty string "". The key must NOT EXIST.   ║**
**║                                                             ║**
**║ CORRECT:   {"text": "I am happy"}                          ║**
**║ WRONG:     {"text": "I am happy", "sentiment": null}       ║**
**║ WRONG:     {"text": "I am happy", "sentiment": ""}         ║**
**╚══════════════════════════════════════════════════════════════╝**

Create a JSON file with your sampled examples. The file format uses a unified `fields` array (NOT separate `label_fields`/`display_fields`):

```json
{
  "fields": [
    {"name": "url", "table": true, "detail": true},
    {"name": "description", "table": true, "detail": true},
    {"name": "is_collection_reasoning", "table": false, "detail": true},
    {"name": "is_collection", "labels": ["true", "false"], "table": true, "detail": true}
  ],
  "examples": [
    {"url": "https://github.com/vinta/awesome-python",
     "description": "A curated list of awesome Python frameworks",
     "is_collection_reasoning": "YES: 'curated list' is a collection marker",
     "is_collection": "true"},
    {"url": "https://github.com/pallets/flask",
     "description": "The Python micro framework for building web applications",
     "is_collection_reasoning": "NO: this is a standalone project",
     "is_collection": "false"}
  ]
}
```

**Format reference:**

- **`fields`** (required): array of field definitions, in display order. Each field has:
  - `name` (required): field key matching example objects
  - `labels` (optional): array of allowed values. Makes the field editable. Omit the `labels` key entirely for read-only display fields.
  - `table` (optional, default `true`): show this field as a table column
  - `detail` (optional, default `true`): show this field in the detail panel below the table
- **`examples`** (required): array of objects. Pre-populated label values are optional -- if a label field key is present on an example (e.g., `"is_collection": "true"`), it appears as an editable default. If the user requests no pre-populated labels, simply omit the label key from each example object entirely (do NOT set to null).

**Field ordering matters.** Fields appear in the table and detail panel in the order you declare them. Put reasoning fields right before or after their label field. Set `"table": false` on reasoning fields to keep the table compact -- they'll still show in the detail panel.

URLs in display fields are **automatically clickable** in the table (truncated but full URL preserved as link).

For multiple output fields:
```json
"fields": [
  {"name": "url"},
  {"name": "language_reasoning", "table": false},
  {"name": "language", "labels": ["Python", "JavaScript", "Rust", ...]},
  {"name": "is_collection_reasoning", "table": false},
  {"name": "is_collection", "labels": ["true", "false"]}
]
```

**Example: No pre-populated labels (user wants to label from scratch):**
```json
{
  "fields": [
    {"name": "text", "table": true, "detail": true},
    {"name": "sentiment", "labels": ["positive", "negative"], "table": true, "detail": true}
  ],
  "examples": [
    {"text": "I love this product"},
    {"text": "Worst experience ever"},
    {"text": "It was fine"}
  ]
}
```
Note: the `sentiment` key is completely absent from each example object. This means the TUI will show empty/unlabeled cells for the user to fill in. **NEVER use `"sentiment": null` -- omit the key entirely.**

**TUI interaction modes** (automatic, based on the data):
- **Single field, <=9 labels**: number keys (1-9) assign labels directly
- **Single field, >9 labels**: press Enter to open a searchable filter, type to narrow, Enter to select
- **Multiple fields**: spreadsheet-style cell cursor. Enter on a label cell opens search for that field's labels. Tab/Shift+Tab move between label columns. Arrow keys navigate cells.
- **Keybindings**: `u` = clear current cell, `Shift+U` = clear entire row, `s` = skip, `q` = save & quit, `j`/`k` = navigate rows

### Step 2: Tell the user to run the TUI

After writing the JSON file, you MUST tell the user the **exact command** to run in a separate terminal.

**╔══════════════════════════════════════════════════════════════╗**
**║ MANDATORY CHECKLIST -- verify ALL before presenting:        ║**
**║ 1. ✅ Command starts with `karat label`                     ║**
**║ 2. ✅ First arg is ABSOLUTE path you wrote to               ║**
**║ 3. ✅ Includes `--output` flag                              ║**
**║ 4. ✅ `--output` followed by ABSOLUTE path for results      ║**
**║ 5. ✅ NO relative paths ANYWHERE                            ║**
**║ 6. ✅ NO placeholders like `<path>` ANYWHERE                ║**
**╚══════════════════════════════════════════════════════════════╝**

**The ONLY correct format is:**
```
karat label /absolute/path/to/input.json --output /absolute/path/to/output.json
```

**SELF-CHECK: Before you show the command to the user, re-read it character by character. Does it have `--output`? Does every path start with `/`? If not, FIX IT before responding.**

**Examples of WRONG commands (DO NOT DO ANY OF THESE):**
- `karat label sentiment_labels.json` ← relative path, missing --output
- `karat label /path/to/file.json` ← missing --output
- `karat label <path> --output <path>` ← placeholders instead of real paths
- `karat label sentiment_labels.json --output sentiment_labeled.json` ← relative paths
- Any command without `--output` is WRONG no matter what

### Step 3: Wait for labeled output

The user will tell you when they're done. You can also check if the output file exists and has been recently modified.

### Step 4: Read the labeled output

The output JSON has the same structure as the input (`fields` + `examples`), with label values filled in:

```json
{
  "fields": [...],
  "examples": [
    {"url": "...", "description": "...",
     "is_collection_reasoning": "YES: ...",
     "is_collection": "true"},
    {"url": "...", "description": "...",
     "is_collection_reasoning": "NO: ...",
     "is_collection": "false"},
    {"url": "...", "description": "...",
     "is_collection_reasoning": "...",
     "is_collection": null}
  ]
}
```

- Label values are strings matching one of the `labels` options, or `null` if the user skipped that example.
- **Exclude `null` examples from training.** A `null` label means the user intentionally skipped it -- do not include it in the training or validation set.

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

## Critical Rules Summary

1. **ALWAYS use the Write tool** to create the labeling JSON file. Never Read first, never Edit, never say it already exists.
2. **ALWAYS use absolute file paths** everywhere -- in the Write tool call AND in the karat label command.
3. **"No pre-populated labels" = OMIT the key entirely** from example objects. Never use null or empty string.
4. **ALWAYS include `--output` with an absolute path** in the karat label command. A command without --output is always wrong.
5. Always use `tools=[]` with AgentLM for classification/structured-output tasks.
6. The `karat` package must be installed: `uv add git+ssh://git@github.com/thekevinscott/karat.git`
7. The ambiguous examples are the most valuable. Do not skip Phase 3 stratification (unless user provides examples directly).
8. This is an interactive workflow. Wait for user input at each labeling step.
