from assistant import PAT


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
        voice.speak(greeting)

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
                    "good bye "
                )
                or normalized_input.startswith(
                    "goodbye "
                )
                or normalized_input.startswith(
                    "bye "
                )
                or normalized_input.startswith(
                    "exit "
                )
            )

            if should_exit:

                response = (
                    "Goodbye! "
                    "P.A.T is shutting down."
                )

                print("🔊 Speaking response...")

                voice.speak(
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

                print(
                    "🔊 Speaking response..."
                )

                voice.speak(
                    response
                )

            else:

                # Safety fallback
                fallback = (
                    "I am listening. "
                    "Please tell me what you need."
                )

                voice.speak(
                    fallback
                )

        except KeyboardInterrupt:

            print(
                "\n\nP.A.T voice session stopped."
            )

            break

        except Exception as error:

            print(
                "\nVoice loop error: "
                f"{type(error).__name__}: {error}"
            )


if __name__ == "__main__":
    main()