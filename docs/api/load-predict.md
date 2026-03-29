# load_predict

::: karat.load_predict
    options:
      show_source: false
      show_root_heading: true
      heading_level: 2

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `signature` | `type` | required | A DSPy Signature class. |
| `path` | `str \| Path \| None` | `None` | Path to an optimized program JSON file. If `None` or the file doesn't exist, returns an unoptimized `dspy.Predict`. |

## Returns

`dspy.Predict` -- a DSPy predictor, optionally loaded with optimized instructions and demos.

## Behavior

1. Creates a `dspy.Predict(signature)`
2. If `path` is provided and the file exists, calls `predict.load(path)` to load the optimized program
3. If `path` is provided but doesn't exist, logs a warning and returns the unoptimized predictor
4. If `path` is `None`, returns the unoptimized predictor

This is the complement to the `/optimize` skill, which saves optimized programs as JSON.

## Example

```python
from karat import load_predict
from my_sigs import ClassifyRepo

# With optimization (falls back gracefully)
classify = load_predict(ClassifyRepo, path="data/optimized_classify_repo.json")
result = classify(readme="# awesome-skills\n\n500+ curated Claude skills")

# Without optimization
classify = load_predict(ClassifyRepo)
result = classify(readme="...")
```
