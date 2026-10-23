
import logging
import tempfile
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PATVoice:
    """Provide speech input and spoken responses for P.A.T."""

    def __init__(
        self,
        *,
        language: str = "auto",
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        offline_first: bool = True,
        enable_tts: bool = True,
        microphone_index: int | None = None,
    ) -> None:
        self.language = language
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.offline_first = offline_first
        self.enable_tts = enable_tts
        self.microphone_index = microphone_index

        self._model: Any | None = None
        self._tts_engine: Any | None = None
        self._recognizer: Any | None = None
        self._model_lock = threading.RLock()
        self._tts_lock = threading.RLock()
        self._listen_lock = threading.Lock()
        self._closed = False

        self._initialize_tts()

    def _initialize_tts(self) -> None:
        """Initialize the configured female TTS voice."""
        if not self.enable_tts:
            return

        try:
            import pyttsx3

            self._tts_engine = pyttsx3.init(driverName='sapi5')
            voices = self._tts_engine.getProperty("voices") or []

            female_voice = next(
                (
                    voice for voice in voices
                    if "zira" in f"{voice.id} {voice.name}".lower()
                ),
                None,
            )

            if female_voice is not None:
                self._tts_engine.setProperty("voice", female_voice.id)
                logger.info("Selected TTS voice: %s", female_voice.name)
            else:
                logger.warning(
                    "Microsoft Zira not found; using the system default voice."
                )

            self._tts_engine.setProperty("rate", 165)
            self._tts_engine.setProperty("volume", 1.0)

        except Exception:
            logger.warning(
                "Text-to-speech initialization failed.", exc_info=True
            )
            self._tts_engine = None

    def _get_recognizer(self) -> Any | None:
        """Create the microphone recognizer when first needed."""
        if self._recognizer is not None:
            return self._recognizer
        try:
            import speech_recognition as sr

            self._recognizer = sr.Recognizer()
            self._recognizer.dynamic_energy_threshold = True
            return self._recognizer
        except ImportError:
            logger.error("SpeechRecognition is not installed.")
            return None

    def _get_whisper_model(self) -> Any | None:
        """Load the offline model on demand."""
        with self._model_lock:
            if self._model is not None:
                return self._model
            if self._closed:
                logger.warning("Cannot load Whisper after voice cleanup.")
                return None
            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                logger.info("Loaded faster-whisper model '%s'.", self.model_size)
                return self._model
            except Exception:
                logger.exception(
                    "Could not load faster-whisper model. "
                    "Check model download/cache access."
                )
                return None

    @staticmethod
    def _language_code(language: str | None) -> str | None:
        """Normalize a language name/code into a short language code."""
        if not language:
            return None
        code = language.strip().replace("_", "-").split("-", maxsplit=1)[0]
        return code.casefold() or None

    @staticmethod
    def _tamil_to_tanglish(text: str) -> str:
        """Convert Tamil Unicode text approximately to Tanglish."""
        vowels = {
            "\u0b85": "a", "\u0b86": "aa", "\u0b87": "i",
            "\u0b88": "ee", "\u0b89": "u", "\u0b8a": "oo",
            "\u0b8e": "e", "\u0b8f": "e", "\u0b90": "ai",
            "\u0b92": "o", "\u0b93": "o", "\u0b94": "au",
        }
        consonants = {
            "\u0b95": "k", "\u0b99": "ng", "\u0b9a": "s",
            "\u0b9e": "nj", "\u0b9f": "t", "\u0ba3": "n",
            "\u0ba4": "th", "\u0ba8": "n", "\u0baa": "p",
            "\u0bae": "m", "\u0baf": "y", "\u0bb0": "r",
            "\u0bb2": "l", "\u0bb5": "v", "\u0bb4": "zh",
            "\u0bb3": "l", "\u0bb1": "r", "\u0ba9": "n",
            "\u0b9c": "j", "\u0bb7": "sh", "\u0bb8": "s",
            "\u0bb9": "h", "\u0bb6": "sh",
        }
        signs = {
            "\u0bbe": "aa", "\u0bbf": "i", "\u0bc0": "ee",
            "\u0bc1": "u", "\u0bc2": "oo", "\u0bc6": "e",
            "\u0bc7": "e", "\u0bc8": "ai", "\u0bca": "o",
            "\u0bcb": "o", "\u0bcc": "au",
        }
        pulli = "\u0bcd"
        result = []
        i = 0

        while i < len(text):
            ch = text[i]

            if ch in vowels:
                result.append(vowels[ch])
                i += 1
            elif ch == "\u0b83":
                result.append("ah")
                i += 1
            elif ch in consonants:
                base = consonants[ch]
                nxt = text[i + 1] if i + 1 < len(text) else ""
                if nxt == pulli:
                    result.append(base)
                    i += 2
                elif nxt in signs:
                    result.append(base + signs[nxt])
                    i += 2
                else:
                    result.append(base + "a")
                    i += 1
            else:
                result.append(ch)
                i += 1

        result_text = "".join(result)

        # Common-word refinements for natural Tanglish spelling.
        result_text = result_text.replace("nanri", "nandri")
        return result_text

    @classmethod
    def _display_transcript(cls, text: str) -> str:
        """Convert Tamil-script text to Tanglish and preserve English text."""
        if not text:
            return text
        if any("\u0b80" <= ch <= "\u0bff" for ch in text):
            return cls._tamil_to_tanglish(text)
        return text

    def speak(self, text: str) -> bool:
        """Speak text using the initialized native TTS engine."""
        if not isinstance(text, str) or not text.strip():
            return False

        if self._closed or not self.enable_tts:
            return False

        with self._tts_lock:
            if self._closed or self._tts_engine is None:
                return False

            try:
                self._tts_engine.say(text.strip())
                self._tts_engine.runAndWait()
                return True
            except Exception:
                logger.exception("Text-to-speech failed.")
                return False
    def say(self, text: str) -> bool:
        """Compatibility alias for speak()."""
        return self.speak(text)

    def listen(
        self,
        *,
        timeout: int = 5,
        phrase_time_limit: int = 10,
        language: str | None = None,
        offline: bool | None = None,
        device_index: int | None = None,
    ) -> str | None:
        """Capture one microphone phrase and return English/Tanglish text.

        Pass language="auto" (the default) for Whisper language detection.
        Online recognition is used only when explicitly requested with offline=False.
        """
        if self._closed:
            logger.warning("Voice input requested after cleanup.")
            return None
        if not self._listen_lock.acquire(blocking=False):
            logger.warning("Another microphone operation is in progress.")
            return None
        try:
            return self._listen_once(
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
                language=language,
                offline=offline,
                device_index=device_index,
            )
        finally:
            self._listen_lock.release()

    def listen_once(self, **kwargs: Any) -> str | None:
        """Compatibility alias for listen()."""
        return self.listen(**kwargs)

    def recognize(self, **kwargs: Any) -> str | None:
        """Compatibility alias for listen()."""
        return self.listen(**kwargs)

    def _listen_once(
        self,
        *,
        timeout: int,
        phrase_time_limit: int,
        language: str | None,
        offline: bool | None,
        device_index: int | None,
    ) -> str | None:
        try:
            import speech_recognition as sr
        except ImportError:
            logger.error("SpeechRecognition is not installed.")
            return None

        recognizer = self._get_recognizer()
        if recognizer is None:
            return None

        selected_device = (
            device_index if device_index is not None else self.microphone_index
        )
        try:
            microphone_args: dict[str, Any] = {}
            if selected_device is not None:
                microphone_args["device_index"] = selected_device
            with sr.Microphone(**microphone_args) as microphone:
                recognizer.adjust_for_ambient_noise(microphone, duration=0.4)
                logger.info("Listening for speech.")
                audio = recognizer.listen(
                    microphone,
                    timeout=max(1, min(int(timeout), 15)),
                    phrase_time_limit=max(1, min(int(phrase_time_limit), 30)),
                )
        except sr.WaitTimeoutError:
            logger.info("No speech detected before timeout.")
            return None
        except (OSError, AttributeError):
            logger.exception("Microphone is unavailable.")
            return None
        except Exception:
            logger.exception("Could not capture microphone audio.")
            return None

        use_offline = self.offline_first if offline is None else bool(offline)
        if use_offline:
            transcript = self._transcribe_offline(audio, language)
            if transcript:
                return transcript
            logger.warning(
                "Offline recognition returned no transcript. "
                "No online fallback was attempted."
            )
            return None
        return self._transcribe_online(audio, language)

    def _transcribe_offline(
        self,
        audio: Any,
        language: str | None,
    ) -> str | None:
        """Transcribe recorded audio with faster-whisper."""
        model = self._get_whisper_model()
        if model is None:
            return None

        wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(wav_bytes)
                temp_path = temp_file.name

            options: dict[str, Any] = {
                "beam_size": 5,
                "vad_filter": True,
                "condition_on_previous_text": False,
                "temperature": 0,
            }
            normalized_language = self._language_code(language or self.language)
            if normalized_language and normalized_language not in {"auto", "none"}:
                options["language"] = normalized_language

            segments, _info = model.transcribe(temp_path, **options)
            print(
                "WHISPER LANGUAGE:",
                getattr(_info, "language", "unknown"),
                "PROBABILITY:",
                round(getattr(_info, "language_probability", 0.0), 3),
            )
            segments = list(segments)
            print(
               "WHISPER SEGMENTS:",
             [
                  (round(s.start, 2), round(s.end, 2), repr(s.text))
                   for s in segments
           ],
        )
            raw_transcript = " ".join(
                segment.text.strip()
                for segment in segments
                if isinstance(segment.text, str) and segment.text.strip()
            ).strip()
            transcript = self._display_transcript(raw_transcript)
            return transcript or None
        except Exception:
            logger.exception("Offline speech transcription failed.")
            return None
        finally:
            if temp_path:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except OSError:
                    logger.warning("Could not remove temporary audio file.")

    def _transcribe_online(
        self,
        audio: Any,
        language: str | None,
    ) -> str | None:
        """Transcribe audio online only when explicitly enabled by the caller."""
        recognizer = self._get_recognizer()
        if recognizer is None:
            return None
        try:
            locale = language or self.language
            normalized = self._language_code(locale)
            # Google recognition needs an explicit locale; auto-detection is not
            # available through this call. Default to Indian English, not silent upload.
            if normalized in {None, "auto", "none"}:
                locale = "en-IN"
            elif normalized == "ta":
                locale = "ta-IN"
            elif normalized == "en":
                locale = "en-IN"
            transcript = recognizer.recognize_google(audio, language=locale)
            return self._display_transcript(transcript.strip()) or None
        except Exception:
            logger.exception("Online speech recognition failed.")
            return None

    def status(self) -> dict[str, Any]:
        """Return voice capability status without loading Whisper."""
        return {
            "closed": self._closed,
            "tts_enabled": self.enable_tts,
            "tts_available": self._tts_engine is not None,
            "whisper_loaded": self._model is not None,
            "offline_first": self.offline_first,
            "language": self.language,
            "model_size": self.model_size,
            "microphone_index": self.microphone_index,
        }

    def cleanup(self) -> None:
        """Release TTS resources and prevent new voice operations."""
        with self._tts_lock:
            if self._closed:
                return
            self._closed = True
            if self._tts_engine is not None:
                try:
                    self._tts_engine.stop()
                except Exception:
                    logger.debug("TTS shutdown raised an error.", exc_info=True)
                finally:
                    self._tts_engine = None

        with self._model_lock:
            self._model = None
        self._recognizer = None

    def close(self) -> None:
        """Compatibility alias for cleanup()."""
        self.cleanup()

    def shutdown(self) -> None:
        """Compatibility alias for cleanup()."""
        self.cleanup()


# Backward-compatible class aliases.
Voice = PATVoice
VoiceAssistant = PATVoice
