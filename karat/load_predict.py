"""Load a DSPy Predict module, optionally with an optimized program."""

import logging
from pathlib import Path

import dspy

logger = logging.getLogger(__name__)


def load_predict(signature: type, path: str | Path | None = None) -> dspy.Predict:
    """Create a dspy.Predict and load an optimized program if available.

    Eliminates the boilerplate of creating a Predict, checking if an
    optimized JSON exists, and conditionally loading it. Falls back
    to an unoptimized predictor if the path doesn't exist.

    This is the complement to the /optimize skill, which saves
    optimized programs as JSON files.

    Usage::

        from karat import load_predict
        from my_sigs import ClassifyRepo

        classify = load_predict(ClassifyRepo, path="data/optimized_classify_repo.json")
        result = classify(readme="...")
    """
    predict = dspy.Predict(signature)  # type: ignore[arg-type]

    if path is not None:
        resolved = Path(path)
        if resolved.exists():
            predict.load(resolved)
        else:
            logger.warning("Optimized program not found at %s, using unoptimized", resolved)

    return predict
