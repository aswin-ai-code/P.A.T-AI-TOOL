import base64
import subprocess

from assistant import PAT


def speak_and_report(voice, text):
    """Speak through native Windows SAPI and report real process errors."""
    if not isinstance(text, str) or not text.strip():
        print("TTS SKIPPED: empty response", flush=True)
        return False

    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Volume = 100; "
        "$s.Rate = 0; "
        "$s.Speak([Console]::In.ReadToEnd()); "
        "$s.Dispose()"
    )

    encoded_script = base64.b64encode(
        script.encode("utf-16le")
    ).decode("ascii")

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                encoded_script,
            ],
            input=text.strip(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )

        print(f"WINDOWS SAPI EXIT CODE: {result.returncode}", flush=True)

        if result.returncode != 0:
            print(f"SAPI ERROR: {result.stderr}", flush=True)
            return False

        print("WINDOWS SAPI COMMAND COMPLETED", flush=True)
        return True

    except (subprocess.SubprocessError, OSError) as exc:
        print(f"SAPI ERROR: {type(exc).__name__}: {exc}", flush=True)
        return False


def main():

    print("=" * 40)
    print("          P.A.T AI")
    print("   Personal Assistant Tool")
    print("=" * 40)
    print("Voice conversation mode active.")
    print("Say 'exit' or 'goodbye' to stop.\n")

    # INITIALIZE P.A.T
    pat = PAT()

    # P.A.T VOICE SYSTEM
    voice = pat.voice

    # STARTUP GREETING
    greeting = pat.greet()

    if greeting:
        speak_and_report(voice, greeting)

    # -----------------------------------------
    # CONTINUOUS CONVERSATION LOOP
    # -----------------------------------------

    while True:

        try:

            # LISTEN
            user_input = voice.listen()

            # IGNORE EMPTY INPUT
            if not user_input:
                continue

            print(f"You: {user_input}")

            # ---------------------------------
            # EXIT CHECK
            # ---------------------------------

            normalized_input = (
                user_input
                .lower()
                .strip()
                .rstrip(".,!?")
            )

            # Normalize punctuation and spaces
            normalized_input = normalized_input.replace(
                "-",
                " "
            )

            normalized_input = normalized_input.replace(
                ",",
                " "
            )

            normalized_input = " ".join(
                normalized_input.split()
            )

            # ---------------------------------
            # EXIT COMMANDS
            # ---------------------------------

            exit_commands = {
                "exit",
                "quit",
                "stop",
                "goodbye",
                "good bye",
                "goodbye pat",
                "good bye pat",
                "bye",
                "bye pat",
                "see you",
                "see you later",
            }

            # ---------------------------------
            # EXIT PHRASE DETECTION
            # ---------------------------------

            should_exit = (
                normalized_input in exit_commands
                or normalized_input.startswith(
                    ("good bye ", "goodbye ", "bye ", "exit ")
                )
            )

            if should_exit:

                response = (
                    "Goodbye! "
                    "P.A.T is shutting down."
                )

                print("Speaking response...")

                speak_and_report(voice,
                    response
                )

                print(
                    "\nP.A.T voice session ended."
                )

                break

            # ---------------------------------
            # PROCESS USER MESSAGE
            # ---------------------------------

            response = pat.process_command(
                user_input
            )

            # ---------------------------------
            # VOICE RESPONSE
            # ---------------------------------

            if response:

                print(f"P.A.T RESPONSE: {response}", flush=True)
                print("Speaking response...", flush=True)
                speak_and_report(voice,response)
                

            else:

                # Safety fallback
                fallback = (
                    "I am listening. "
                    "Please tell me what you need."
                )

                speak_and_report(voice,
                    fallback
                )

        except KeyboardInterrupt:

            print(
                "\n\nP.A.T voice session stopped."
            )

            break

        except Exception as error:  # noqa: BLE001

            print(
                "\nVoice loop error: "
                f"{type(error).__name__}: {error}"
            )


if __name__ == "__main__":
    main()

