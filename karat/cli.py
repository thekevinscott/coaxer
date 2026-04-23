"""Deprecated CLI alias. Delegates to :mod:`coaxer.cli`."""

import warnings

from coaxer.cli import main as _main


def main() -> None:
    warnings.warn(
        "The `karat` CLI has been renamed to `coaxer`. Use `coaxer` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    _main()
