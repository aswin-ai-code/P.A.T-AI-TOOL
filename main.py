from assistant import PAT


def speak_and_report(voice, text):
    """Speak and report whether the TTS call succeeded."""
    result = voice.speak(text)
    print(f"TTS RESULT: {result}", flush=True)
    return result


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

                speak_and_report(voice, response)

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
