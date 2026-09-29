import os
import re
import time

import pyttsx3
import speech_recognition as sr

from faster_whisper import WhisperModel


class PATVoice:

    def __init__(self):

        # =================================================
        # MICROPHONE
        # =================================================

        self.microphone_index = 1

        self.recognizer = sr.Recognizer()

        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.2
        self.recognizer.non_speaking_duration = 0.5

        # =================================================
        # WHISPER MODEL
        # =================================================

        self.whisper_model_path = "base"

        print("Loading local Whisper model...")

        self.whisper = WhisperModel(
            self.whisper_model_path,
            device="cpu",
            compute_type="int8"
        )

        print("Whisper model loaded successfully.")

        # =================================================
        # TTS CONFIGURATION
        # =================================================

        print("Initializing P.A.T voice...")

        self.tts_rate = 165
        self.tts_volume = 1.0

        self.engine = None

        self._initialize_tts()

        print("P.A.T voice system ready.")

    # =====================================================
    # INITIALIZE TTS
    # =====================================================

    def _initialize_tts(self):

        try:

            # Create a completely fresh engine
            self.engine = pyttsx3.init()

            self.engine.setProperty(
                "rate",
                self.tts_rate
            )

            self.engine.setProperty(
                "volume",
                self.tts_volume
            )

            print(
                "TTS engine initialized successfully."
            )

        except Exception as error:

            self.engine = None

            print(
                f"TTS initialization error: "
                f"{type(error).__name__}: {error}"
            )

    # =====================================================
    # SPEAK
    # =====================================================

    def speak(self, text):

        if not isinstance(text, str):
            text = str(text)

        text = text.strip()

        if not text:
            return

        print(f"P.A.T: {text}")

        # -------------------------------------------------
        # ALWAYS CREATE A FRESH TTS ENGINE
        # -------------------------------------------------

        try:

            # Stop and release previous engine
            if self.engine is not None:

                try:
                    self.engine.stop()
                except Exception:
                    pass

                self.engine = None

            # Give Windows SAPI a tiny moment
            time.sleep(0.1)

            # Create fresh engine
            self.engine = pyttsx3.init()

            self.engine.setProperty(
                "rate",
                self.tts_rate
            )

            self.engine.setProperty(
                "volume",
                self.tts_volume
            )

            # -------------------------------------------------
            # FIND AVAILABLE VOICES
            # -------------------------------------------------

            try:

                voices = self.engine.getProperty(
                    "voices"
                )

                if voices:

                    # Use first available Windows voice
                    self.engine.setProperty(
                        "voice",
                        voices[0].id
                    )

            except Exception:

                pass

            # -------------------------------------------------
            # SPEAK
            # -------------------------------------------------

            self.engine.say(text)

            self.engine.runAndWait()

            # -------------------------------------------------
            # CLEAN STOP
            # -------------------------------------------------

            try:
                self.engine.stop()
            except Exception:
                pass

            time.sleep(0.2)

            print(
                "🔊 Voice playback completed."
            )

        except Exception as error:

            print(
                f"TTS error: "
                f"{type(error).__name__}: {error}"
            )

            # -------------------------------------------------
            # TTS RECOVERY
            # -------------------------------------------------

            try:

                self.engine = None

                time.sleep(0.2)

                recovery_engine = pyttsx3.init()

                recovery_engine.setProperty(
                    "rate",
                    self.tts_rate
                )

                recovery_engine.setProperty(
                    "volume",
                    self.tts_volume
                )

                recovery_engine.say(text)

                recovery_engine.runAndWait()

                try:
                    recovery_engine.stop()
                except Exception:
                    pass

                self.engine = None

                print(
                    "🔊 Voice playback recovered."
                )

            except Exception as retry_error:

                print(
                    f"TTS recovery error: "
                    f"{type(retry_error).__name__}: "
                    f"{retry_error}"
                )

                self.engine = None

    # =====================================================
    # CLEAN TRANSCRIPTION
    # =====================================================

    def clean_transcription(self, text):

        text = text.strip()

        if not text:
            return ""

        # -------------------------------------------------
        # NORMALIZE WHITESPACE
        # -------------------------------------------------

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        # -------------------------------------------------
        # REMOVE EXACT DUPLICATE SENTENCE
        # -------------------------------------------------

        words = text.split()

        if len(words) >= 4:

            for split_point in range(
                1,
                len(words) // 2 + 1
            ):

                first_part = words[:split_point]

                second_part = words[split_point:]

                if (
                    len(second_part) == split_point
                    and
                    [
                        word.lower().strip(".,!?")
                        for word in first_part
                    ]
                    ==
                    [
                        word.lower().strip(".,!?")
                        for word in second_part
                    ]
                ):

                    text = " ".join(first_part)

                    break

        # -------------------------------------------------
        # REMOVE CONSECUTIVE DUPLICATE WORDS
        # -------------------------------------------------

        cleaned_words = []

        for word in text.split():

            cleaned_word = (
                word.lower()
                .strip(".,!?")
            )

            if (
                cleaned_words
                and
                cleaned_word
                ==
                cleaned_words[-1]
                .lower()
                .strip(".,!?")
            ):

                continue

            cleaned_words.append(word)

        text = " ".join(cleaned_words)

        # -------------------------------------------------
        # P.A.T NAME CORRECTION
        # -------------------------------------------------

        normalized = (
            text.lower()
            .strip(".,!?")
        )

        replacements = {
            "bad": "P.A.T",
            "b a d": "P.A.T",
            "p a t": "P.A.T",
            "pat": "P.A.T",
        }

        if normalized in replacements:

            text = replacements[
                normalized
            ]

        return text.strip()

    # =====================================================
    # LISTEN
    # =====================================================

    def listen(self):

        wav_file = "pat_voice_input.wav"

        try:

            # ---------------------------------------------
            # MICROPHONE
            # ---------------------------------------------

            with sr.Microphone(
                device_index=self.microphone_index
            ) as source:

                print("🎤 Listening...")

                # -----------------------------------------
                # AMBIENT NOISE CALIBRATION
                # -----------------------------------------

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.25
                )

                print("🎤 Speak now...")

                audio = self.recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=10
                )

            print("🎧 Audio captured.")

            # ---------------------------------------------
            # SAVE AUDIO
            # ---------------------------------------------

            wav_data = audio.get_wav_data()

            with open(
                wav_file,
                "wb"
            ) as file:

                file.write(wav_data)

            # ---------------------------------------------
            # WHISPER
            # ---------------------------------------------

            print("🧠 Running Whisper...")

            segments, info = self.whisper.transcribe(

                wav_file,

                language="en",

                beam_size=5,

                best_of=5,

                temperature=0,

                initial_prompt=(
                    "This is a continuous conversation "
                    "with P.A.T, Personal Assistant Tool. "
                    "The user's name is Aswin. "
                    "Common phrases include: "
                    "hello, hi, hey, good morning, "
                    "good night, goodbye, bye, "
                    "how are you, what can you do, "
                    "tell me about yourself, "
                    "tell me about you, "
                    "I am tired today, "
                    "I am happy today, "
                    "I am sad today, "
                    "what is my name, "
                    "open calculator, "
                    "open browser, "
                    "open YouTube."
                ),

                condition_on_previous_text=False,

                vad_filter=True,

                vad_parameters={
                    "min_silence_duration_ms": 350,
                    "speech_pad_ms": 200,
                },

                no_speech_threshold=0.35,

                log_prob_threshold=-1.0,

                compression_ratio_threshold=2.4,
            )

            # ---------------------------------------------
            # COLLECT SEGMENTS
            # ---------------------------------------------

            segments = list(segments)

            text_parts = []

            for segment in segments:

                segment_text = (
                    segment.text
                    .strip()
                )

                if segment_text:

                    text_parts.append(
                        segment_text
                    )

            text = " ".join(
                text_parts
            ).strip()

            # ---------------------------------------------
            # EMPTY SPEECH
            # ---------------------------------------------

            if not text:

                print(
                    "P.A.T: No clear speech detected."
                )

                return ""

            # ---------------------------------------------
            # CLEAN
            # ---------------------------------------------

            text = self.clean_transcription(
                text
            )

            if not text:

                return ""

            # ---------------------------------------------
            # NORMALIZED TEXT
            # ---------------------------------------------

            normalized_text = (
                text.lower()
                .strip()
                .strip(".,!?")
            )

            # ---------------------------------------------
            # HALLUCINATION PROTECTION
            # ---------------------------------------------

            hallucination_phrases = {

                "you",
                "yeah",
                "yes",
                "thank you",
                "thanks for watching",
                "thank you for watching",
            }

            if normalized_text in hallucination_phrases:

                print(
                    "P.A.T: Ignoring possible "
                    "Whisper hallucination."
                )

                return ""

            # ---------------------------------------------
            # VERY SHORT INPUT
            # ---------------------------------------------

            if len(normalized_text) <= 1:

                print(
                    "P.A.T: Ignoring very short "
                    "voice input."
                )

                return ""

            # ---------------------------------------------
            # WAKE WORD ONLY
            # ---------------------------------------------

            if normalized_text in {
                "p.a.t",
                "pat",
                "p a t",
            }:

                print(
                    "P.A.T: Wake word detected. "
                    "Waiting for command..."
                )

                return ""

            # ---------------------------------------------
            # REPETITION PROTECTION
            # ---------------------------------------------

            words = normalized_text.split()

            if len(words) >= 6:

                unique_words = set(words)

                if unique_words:

                    repetition_ratio = (
                        len(words)
                        /
                        len(unique_words)
                    )

                    if repetition_ratio >= 2.5:

                        print(
                            "P.A.T: Ignoring possible "
                            "Whisper repetition."
                        )

                        return ""

            # ---------------------------------------------
            # DISPLAY RESULT
            # ---------------------------------------------

            print(
                f"Detected language: "
                f"{info.language}"
            )

            print(
                f"Whisper confidence: "
                f"{info.language_probability:.2f}"
            )

            return text

        # =================================================
        # ERRORS
        # =================================================

        except sr.WaitTimeoutError:

            print(
                "P.A.T: I didn't hear anything."
            )

            return ""

        except KeyboardInterrupt:

            print(
                "\nP.A.T: Voice input stopped."
            )

            return ""

        except OSError as error:

            print(
                f"Microphone error: {error}"
            )

            return ""

        except (
            ValueError,
            RuntimeError
        ) as error:

            print(
                f"Voice error: "
                f"{type(error).__name__}: {error}"
            )

            return ""

        except Exception as error:

            print(
                f"Unexpected voice error: "
                f"{type(error).__name__}: {error}"
            )

            return ""

        finally:

            try:

                if os.path.exists(
                    wav_file
                ):

                    os.remove(
                        wav_file
                    )

            except OSError:

                pass


# =========================================================
# P.A.T VOICE TEST
# =========================================================

if __name__ == "__main__":

    print()

    print(
        "===== P.A.T VOICE TEST ====="
    )

    pat_voice = PATVoice()

    pat_voice.speak(
        "Voice system test successful."
    )

    text = pat_voice.listen()

    print()

    print(
        "Final result:",
        text
    )