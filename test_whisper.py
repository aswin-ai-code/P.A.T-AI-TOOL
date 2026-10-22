
"""Safe unit tests for P.A.T's faster-whisper integration.

These tests use mocks and synthetic data. They do not access the microphone,
download a model, or load a real Whisper model.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock


def extract_transcript(segments: object) -> str:
    """Combine recognized segment text into a clean transcript."""
    parts: list[str] = []

    for segment in segments:  # type: ignore[union-attr]
        text = getattr(segment, "text", "")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())

    return " ".join(parts).strip()


def normalize_language(language: str | None) -> str | None:
    """Normalize a language code without guessing a missing language."""
    if not isinstance(language, str):
        return None

    normalized = language.strip().casefold()
    return normalized or None


class TestWhisperHelpers(unittest.TestCase):
    """Test transcript handling without loading the Whisper model."""

    def test_transcript_combines_segments(self) -> None:
        segments = [
            SimpleNamespace(text=" Hello"),
            SimpleNamespace(text=" there."),
        ]

        self.assertEqual(extract_transcript(segments), "Hello there.")

    def test_transcript_strips_extra_whitespace(self) -> None:
        segments = [
            SimpleNamespace(text="  P.A.T  "),
            SimpleNamespace(text="\n is ready  "),
        ]

        self.assertEqual(extract_transcript(segments), "P.A.T is ready")

    def test_empty_segments_return_empty_transcript(self) -> None:
        self.assertEqual(extract_transcript([]), "")

    def test_blank_segments_are_ignored(self) -> None:
        segments = [
            SimpleNamespace(text=" "),
            SimpleNamespace(text="Hello"),
            SimpleNamespace(text=""),
        ]

        self.assertEqual(extract_transcript(segments), "Hello")

    def test_missing_segment_text_is_ignored(self) -> None:
        segments = [SimpleNamespace(), SimpleNamespace(text="Ready")]

        self.assertEqual(extract_transcript(segments), "Ready")

    def test_english_language_code_is_normalized(self) -> None:
        self.assertEqual(normalize_language(" EN "), "en")

    def test_tamil_language_code_is_normalized(self) -> None:
        self.assertEqual(normalize_language("TA"), "ta")

    def test_missing_language_is_not_guessed(self) -> None:
        self.assertIsNone(normalize_language(None))
        self.assertIsNone(normalize_language("   "))


class TestWhisperMockContract(unittest.TestCase):
    """Check expected interactions using a fake model object."""

    def test_model_transcribe_can_be_mocked(self) -> None:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (
            iter([SimpleNamespace(text=" P.A.T is ready.")]),
            SimpleNamespace(language="en", language_probability=0.99),
        )

        segments, info = mock_model.transcribe("mock-audio.wav")
        transcript = extract_transcript(segments)

        self.assertEqual(transcript, "P.A.T is ready.")
        self.assertEqual(info.language, "en")
        mock_model.transcribe.assert_called_once_with("mock-audio.wav")

    def test_transcription_failure_can_be_simulated(self) -> None:
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError(
            "Simulated transcription failure"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Simulated transcription failure",
        ):
            mock_model.transcribe("mock-audio.wav")


if __name__ == "__main__":
    unittest.main()
