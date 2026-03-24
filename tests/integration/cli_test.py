"""Integration tests for CLI argument handling."""

from karat.cli import label


def test_label_requires_output_flag(capsys):
    """karat label without --output should exit with error."""
    import pytest

    with pytest.raises(SystemExit) as exc:
        label(["input.json"])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "--output" in captured.out or "--output" in captured.err
