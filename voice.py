
import os
import speech_recognition as sr
import pyttsx3
from faster_whisper import WhisperModel


class PATVoice:

    def __init__(self):

        self.microphone_index = 1

        self.recognizer = sr.Recognizer()

        # ---------------------------------------------
        # MICROPHONE SETTINGS
        # ---------------------------------------------

        self.recognizer.energy_threshold = 120
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.2
        self.recognizer.non_speaking_duration = 0.5

        # ---------------------------------------------
        # LOCAL WHISPER MODEL
        # ---------------------------------------------

        self.whisper_model_path = (
            r"C:\Users\JEBASTIN ASWIN.S\.cache\huggingface\hub"
            r"\models--Systran--faster-whisper-tiny"
            r"\snapshots\d90ca5fe260221311c53c58e660288d3deb8d356"
        )

        print("Loading local Whisper model...")

        self.whisper = WhisperModel(
            self.whisper_model_path,
            device="cpu",
            compute_type="int8"
        )

        print("Whisper model loaded successfully.")

    # ---------------------------------------------
    # VOICE OUTPUT
    # ---------------------------------------------

    def speak(self, text):

        if not isinstance(text, str):
            text = str(text)

        print(f"P.A.T: {text}")

        engine = pyttsx3.init()

        try:
            # P.A.T is pronounced as "PAT"
            engine.say(f"PAT. {text}")
            engine.runAndWait()

        finally:
            engine.stop()

    # ---------------------------------------------
    # VOICE INPUT
    # ---------------------------------------------

    def listen(self):

        wav_file = "pat_voice_input.wav"

        try:

            # -----------------------------------------
            # MICROPHONE INPUT
            # -----------------------------------------

            with sr.Microphone(
                device_index=self.microphone_index
            ) as source:

                print("🎤 Listening...")

                audio = self.recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=8
                )

            print("🎧 Audio captured.")
            print("🧠 Running Whisper...")

            # -----------------------------------------
            # SAVE AUDIO TEMPORARILY
            # -----------------------------------------

            wav_data = audio.get_wav_data()

            with open(wav_file, "wb") as file:
                file.write(wav_data)

            # -----------------------------------------
            # WHISPER TRANSCRIPTION
            # -----------------------------------------

            segments, info = self.whisper.transcribe(
                wav_file,
                language=None,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 500
                },
                beam_size=5,
                temperature=0,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
                compression_ratio_threshold=2.4
            )

            # -----------------------------------------
            # LANGUAGE FILTER
            # ONLY ENGLISH + TAMIL
            # -----------------------------------------

            if info.language not in ["en", "ta"]:

                print(
                    f"P.A.T: Unsupported language detected: "
                    f"{info.language}"
                )

                return ""

            # -----------------------------------------
            # COLLECT WHISPER SEGMENTS
            # -----------------------------------------

            segments = list(segments)

            text_parts = []

            for segment in segments:

                segment_text = segment.text.strip()

                if segment_text:
                    text_parts.append(segment_text)

            text = " ".join(text_parts).strip()

            # -----------------------------------------
            # EMPTY / SILENCE PROTECTION
            # -----------------------------------------

            if not text:

                print(
                    "P.A.T: No clear speech detected."
                )

                return ""

            # -----------------------------------------
            # REPETITION PROTECTION
            # -----------------------------------------

            words = text.split()

            if len(words) >= 8:

                unique_words = set(words)

                repetition_ratio = (
                    len(words) / len(unique_words)
                    if unique_words
                    else 0
                )

                if repetition_ratio >= 3:

                    print(
                        "P.A.T: Ignoring possible "
                        "Whisper hallucination."
                    )

                    return ""

            # -----------------------------------------
            # SHORT HALLUCINATION PROTECTION
            # -----------------------------------------

            hallucination_phrases = {
                "you",
                "thank you very much",
                "thank you very much thank you very much",
            }

            normalized_text = text.lower().strip()

            if normalized_text in hallucination_phrases:

                print(
                    "P.A.T: Ignoring possible "
                    "hallucinated speech."
                )

                return ""

            # -----------------------------------------
            # FINAL RESULT
            # -----------------------------------------

            print(f"You: {text}")
            print(f"Detected language: {info.language}")

            return text

        # ---------------------------------------------
        # ERROR HANDLING
        # ---------------------------------------------

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

        except Exception as error:

            print(
                f"Voice error: "
                f"{type(error).__name__}: {error}"
            )

            return ""

        # ---------------------------------------------
        # REMOVE TEMPORARY AUDIO FILE
        # ---------------------------------------------

        finally:

            try:

                if os.path.exists(wav_file):
                    os.remove(wav_file)

            except OSError:
                pass
