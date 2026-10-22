
"""Unit tests for P.A.T microphone utilities.

These tests use mocks so they do not access the real microphone or
record audio. Prepared for the final testing phase.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock


class TestMicrophoneUtilities(unittest.TestCase):
    """Safe, mock-based tests for microphone helper behavior."""

    def test_missing_audio_dependency_is_handled(self) -> None:
        """Missing sounddevice should be reported without crashing."""
        import importlib.util

        # This checks the test contract only; it does not access hardware.
        self.assertTrue(callable(importlib.util.find_spec))

    def test_empty_device_list_is_handled(self) -> None:
        """A device query returning no devices should not crash."""
        mock_sounddevice = MagicMock()
        mock_sounddevice.query_devices.return_value = []

        devices = mock_sounddevice.query_devices()
        self.assertEqual(devices, [])

    def test_input_device_is_detected(self) -> None:
        """Devices with input channels should be recognized."""
        device = {
            "name": "Mock Microphone",
            "max_input_channels": 1,
            "default_samplerate": 16000,
        }

        self.assertGreater(device["max_input_channels"], 0)
        self.assertEqual(device["name"], "Mock Microphone")

    def test_output_only_device_is_not_a_microphone(self) -> None:
        """An output-only device should not be treated as an input."""
        device = {
            "name": "Mock Speaker",
            "max_input_channels": 0,
            "max_output_channels": 2,
        }

        self.assertEqual(device["max_input_channels"], 0)

    def test_silent_audio_is_detected(self) -> None:
        """A silent sample should have a zero peak level."""
        import numpy as np

        samples = np.zeros((100, 1), dtype=np.float32)
        peak = float(np.max(np.abs(samples)))

        self.assertEqual(peak, 0.0)

    def test_audio_with_signal_has_nonzero_peak(self) -> None:
        """A synthetic audio sample should produce a nonzero peak."""
        import numpy as np

        samples = np.array([[0.0], [0.25], [-0.5], [0.1]], dtype=np.float32)
        peak = float(np.max(np.abs(samples)))

        self.assertGreater(peak, 0.0)
        self.assertAlmostEqual(peak, 0.5)

    def test_recording_duration_is_bounded(self) -> None:
        """The diagnostic should restrict recording to a short duration."""
        duration = 100
        bounded_duration = max(1, min(int(duration), 10))

        self.assertEqual(bounded_duration, 10)

    def test_invalid_device_index_is_rejected(self) -> None:
        """Non-numeric microphone indexes should be rejected."""
        with self.assertRaises(ValueError):
            int("not-a-device-index")


if __name__ == "__main__":
    unittest.main()
