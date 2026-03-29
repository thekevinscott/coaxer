# /optimize Skill

The `/optimize` skill is a Claude Code skill that orchestrates the full prompt optimization workflow: read a DSPy Signature, sample data intelligently, collect human labels via the TUI, run DSPy optimization, and save a compiled program.

## Install

```bash
uvx karat install
```

This copies `SKILL.md` into `.claude/skills/optimize/` in your project. Claude Code loads it automatically when you invoke `/optimize`.

## Workflow

### Phase 1: Read the Signature

Provide a DSPy Signature class -- either as a file path with class name (e.g., `myproject/sigs.py:ClassifyRepo`) or an inline description. The skill reads the input/output fields and docstring.

### Phase 2: Get Data

The skill asks where the data is. It accepts any format: CSV, TSV, JSON, JSONL, Parquet, SQL query, Python expression, API call. If the dataset is large, it samples ~100 examples.

### Phase 3: Smart Sampling

The skill uses the LM itself to do a rough classification pass, then stratifies:

1. **Run a quick pass** using `AgentLM` with the current (unoptimized) signature
2. **Stratify into three groups:**
   - **Likely positive** (5): confidently labeled True/positive
   - **Likely negative** (5): confidently labeled False/negative
   - **Ambiguous** (5): hedged, uncertain, or borderline predictions
3. **Present ambiguous examples first** -- boundary cases are where prompt tuning adds the most value

For non-binary outputs, sampling covers the distribution of predicted values with extra weight on rare or uncertain predictions.

If the user provides their own small set of examples directly (not a large dataset), stratification is skipped.

### Phase 4: Collect Labels via TUI

The skill writes a JSON file with sampled examples and tells the user to run:

```bash
karat label /absolute/path/to/input.json --output /absolute/path/to/output.json
```

The user reviews and corrects labels in the TUI in a separate terminal.

See [Labeling TUI](labeling-tui.md) for the full input format and interaction reference.

### Phase 5: Run DSPy Optimization

With labeled examples:

1. Split train/val (default 70/30)
2. Configure the LM:
   ```python
   from karat import AgentLM
   import dspy

   lm = AgentLM(tools=[])
   dspy.configure(lm=lm)
   ```
3. Build `dspy.Example` objects with `.with_inputs()` set to input field names
4. Define a metric (exact match for classification, or ask the user)
5. Choose an optimizer: `dspy.BootstrapFewShot` (fast) or `dspy.MIPROv2` (thorough, burns more LLM calls)
6. Run optimization and report val accuracy

### Phase 6: Save and Apply

The compiled program is saved as JSON:

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

Load it in your code:

```python
from karat import load_predict
classify = load_predict(ClassifyRepo, path="path/to/optimized.json")
```
