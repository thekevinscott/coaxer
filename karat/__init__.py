"""Deprecated alias for the :mod:`coaxer` package.

The project was renamed from ``karat`` to ``coaxer``. Importing
``karat`` continues to work via re-exports from :mod:`coaxer` but emits
a :class:`DeprecationWarning`. The shim will be removed in a future
release; migrate to ``from coaxer import ...``.
"""

import warnings

warnings.warn(
    "`karat` has been renamed to `coaxer`. "
    "Replace `from karat import X` with `from coaxer import X`. "
    "The `karat` shim will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from coaxer import AgentLM, CoaxedPrompt, OpenAILM  # noqa: E402

__all__ = ["AgentLM", "CoaxedPrompt", "OpenAILM"]
