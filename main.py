from ai.ai_engine import AIEngine


def main():
    print("=" * 40)
    print("          P.A.T AI")
    print("   Personal Assistant Tool")
    print("=" * 40)
    print("Type 'exit' to stop.\n")

    engine = AIEngine()

    while True:
        user_input = input("You: ")

        if user_input.lower().strip() == "exit":
            print("P.A.T: Goodbye! 👋")
            break

        response = engine.generate_response(user_input)

        print("P.A.T:", response)


if __name__ == "__main__":
    main()
