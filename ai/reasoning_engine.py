class ReasoningEngine:
    def __init__(self):
        self.last_reasoning = None

    def analyze(self, user_input, intent="unknown", context=None):
        if not isinstance(user_input, str) or not user_input.strip():
            return {
                "understanding": "Empty request",
                "intent": intent,
                "steps": [],
                "action_required": False,
            }

        text = user_input.strip()

        steps = self._build_steps(intent, text)

        result = {
            "understanding": text,
            "intent": intent,
            "steps": steps,
            "action_required": intent not in {
                "greeting",
                "help",
                "general_conversation",
            },
            "context_available": bool(context),
        }

        self.last_reasoning = result
        return result

    def _build_steps(self, intent, text):
        reasoning_steps = {
            "file_operation": [
                "Identify the requested file operation",
                "Identify the target file or folder",
                "Check permissions",
                "Execute the operation",
                "Verify the result",
            ],
            "application_control": [
                "Identify the requested application",
                "Determine the requested action",
                "Check permissions",
                "Execute the action",
                "Verify the result",
            ],
            "calculation": [
                "Identify the mathematical operation",
                "Extract the required values",
                "Calculate the result",
                "Verify the result",
            ],
            "web_search": [
                "Understand the information request",
                "Create a search query",
                "Retrieve relevant information",
                "Evaluate the information",
                "Prepare the response",
            ],
            "system_info": [
                "Identify the requested system information",
                "Collect the required system data",
                "Verify the data",
                "Prepare the response",
            ],
            "memory_recall": [
                "Identify what the user wants to remember",
                "Search available conversation context",
                "Find the relevant information",
                "Return the information",
            ],
            "time_date": [
                "Identify the requested date or time",
                "Retrieve the current information",
                "Return the result",
            ],
        }

        return reasoning_steps.get(
            intent,
            [
                "Understand the user's request",
                "Determine the required action",
                "Process the request",
                "Verify the result",
            ],
        )

    def get_last_reasoning(self):
        return self.last_reasoning

    def clear(self):
        self.last_reasoning = None