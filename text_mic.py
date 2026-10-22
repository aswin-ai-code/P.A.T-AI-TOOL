
"""Convert microphone speech into text for P.A.T.

This utility is standalone and does not start automatically with P.A.T.
SpeechRecognition's Google recognizer requires an internet connection.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def recognize_from_microphone(
    *,
    language: str = "en-IN",
    timeout: int = 5,
    phrase_time_limit: int = 10,
    device_index: int | None = None,
) -> str | None:
    """Listen for one phrase and return recognized text.

    Returns None when no usable transcript is available.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        logger.error("SpeechRecognition is not installed.")
        print("SpeechRecognition package is unavailable.")
        return None

    recognizer = sr.Recognizer()
    microphone_args: dict[str, Any] = {}

    if device_index is not None:
        microphone_args["device_index"] = device_index

    try:
        with sr.Microphone(**microphone_args) as source:
            print("Listening... Speak clearly, bro.")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(
                source,
                timeout=max(1, min(int(timeout), 15)),
                phrase_time_limit=max(1, min(int(phrase_time_limit), 30)),
            )

        print("Recognizing speech...")

        transcript = recognizer.recognize_google(
            audio,
            language=language,
        )

        transcript = transcript.strip()
        return transcript or None

    except sr.WaitTimeoutError:
        print("No speech detected before the timeout.")
    except sr.UnknownValueError:
        print("Speech was detected, but the words were not understood.")
    except sr.RequestError:
        logger.exception("Online speech recognition request failed.")
        print("Speech recognition service unavailable. Check your internet.")
    except OSError:
        logger.exception("Could not access the microphone.")
        print("Microphone unavailable. Check device selection and permissions.")
    except Exception:
        logger.exception("Unexpected speech recognition error.")
        print("An unexpected microphone recognition error occurred.")

    return None


def main() -> int:
    """Run the standalone speech-to-text utility."""
    print("=" * 44)
    print("P.A.T — Microphone Speech-to-Text")
    print("=" * 44)
    print("This utility uses online recognition.")
    print("Type Ctrl+C to stop.\n")

    try:
        while True:
            transcript = recognize_from_microphone()

            if transcript:
                print(f"\nRecognized text: {transcript}\n")
            else:
                print()

            try:
                again = input("Listen again? (y/n): ").strip().casefold()
            except EOFError:
                return 0

            if again not in {"y", "yes"}:
                break

    except KeyboardInterrupt:
        print("\nSpeech-to-text stopped.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
