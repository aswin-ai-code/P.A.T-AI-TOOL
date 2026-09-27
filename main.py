from assistant import PAT
from voice import PATVoice


def main():
    print("=" * 40)
    print("          P.A.T AI")
    print("   Personal Assistant Tool")
    print("=" * 40)
    print("Voice mode active. Say 'exit' to stop.\n")

    pat = PAT()
    voice = PATVoice()

    voice.speak(pat.greet())

    while True:
        user_input = voice.listen()

        if not user_input:
            continue

        response = pat.process_command(user_input)

        voice.speak(response)

        # Use P.A.T's intent engine to detect exit variations
        intent = pat.ai_engine.intent_engine.detect_intent(
            user_input
        )

        if intent == "exit":
            break


if __name__ == "__main__":
    main()