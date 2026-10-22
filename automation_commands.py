
"""P.A.T natural-language automation command mapper."""

from automation_engine import AutomationEngine


class AutomationCommands:
    def __init__(self):
        self.engine = AutomationEngine()

        # Only explicitly approved, simple actions.
        self.command_map = {
            "open calculator": "open_calculator",
            "calculator open": "open_calculator",
            "open notepad": "open_notepad",
            "open browser": "open_browser",
            "open google": "open_google",
            "open youtube": "open_youtube",
            "show desktop": "show_desktop",
            "minimize window": "minimize_window",
            "maximize window": "maximize_window",
            "current directory": "current_directory",
            "show current directory": "current_directory",
        }

    def handle(self, text: str) -> str:
        command = " ".join(text.lower().strip().split())

        if not command:
            return "Please say an automation command."

        action = self.command_map.get(command)

        if action is None:
            return (
                "Command not recognized. "
                "Try: open calculator, open notepad, "
                "open browser, or show current directory."
            )

        result = self.engine.run(action)

        if isinstance(result, str):
            return result

        return str(result)


if __name__ == "__main__":
    assistant = AutomationCommands()

    print("P.A.T Natural-Language Automation")
    print("Type 'exit' to quit.")

    while True:
        command = input("\nYou: ").strip()

        if command.lower() in {"exit", "quit"}:
            print("P.A.T: Automation test ended.")
            break

        print("P.A.T:", assistant.handle(command))
