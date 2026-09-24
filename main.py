from assistant import PAT
import logging


logging.basicConfig(
    filename="pat.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    pat = PAT()

    print(pat.greet())

    while True:
        try:
            user_input = input("You: ")

            # Input validation
            if not user_input.strip():
                print("P.A.T: Please enter a command.")
                continue

            response = pat.process_command(user_input)

            print("P.A.T:", response)

            if user_input.lower().strip() == "exit":
                break

        except KeyboardInterrupt:
            print("\nP.A.T: Goodbye! P.A.T is shutting down.")
            break

        except Exception:
            logging.exception("Unexpected error occurred")
            print("P.A.T: Sorry, an unexpected error occurred.")


if __name__ == "__main__":
    main()