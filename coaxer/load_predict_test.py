"""Tests for load_predict."""

from unittest.mock import MagicMock, patch

from coaxer.load_predict import load_predict


def describe_load_predict():
    def it_returns_a_predict_without_path():
        predict = load_predict(MagicMock())
        assert predict is not None

    def it_loads_optimized_when_path_exists(tmp_path):
        optimized = tmp_path / "optimized.json"
        optimized.write_text("{}")

        with patch("coaxer.load_predict.dspy.Predict") as mock_predict_cls:
            mock_instance = MagicMock()
            mock_predict_cls.return_value = mock_instance

            result = load_predict(MagicMock(), path=optimized)

            mock_instance.load.assert_called_once_with(optimized)
            assert result is mock_instance

    def it_warns_when_path_missing(tmp_path, caplog):
        missing = tmp_path / "nonexistent.json"

        with patch("coaxer.load_predict.dspy.Predict") as mock_predict_cls:
            mock_instance = MagicMock()
            mock_predict_cls.return_value = mock_instance

            import logging

            with caplog.at_level(logging.WARNING):
                result = load_predict(MagicMock(), path=missing)

            mock_instance.load.assert_not_called()
            assert "not found" in caplog.text
            assert result is mock_instance

    def it_accepts_string_path(tmp_path):
        optimized = tmp_path / "optimized.json"
        optimized.write_text("{}")

        with patch("coaxer.load_predict.dspy.Predict") as mock_predict_cls:
            mock_instance = MagicMock()
            mock_predict_cls.return_value = mock_instance

            load_predict(MagicMock(), path=str(optimized))

            mock_instance.load.assert_called_once()
