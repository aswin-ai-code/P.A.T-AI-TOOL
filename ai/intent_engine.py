class IntentEngine:

    def __init__(self):
        self.intent_keywords = {
            "greeting": [
                "hello",
                "hi",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
            ],

            "memory_recall": [
                "remember",
                "what did i say",
                "what did i tell you",
                "last message",
                "do you remember",
            ],

            "system_info": [
                "system information",
                "computer information",
                "pc information",
                "my system",
                "ram",
                "cpu",
                "storage",
            ],

            "file_operation": [
                "open file",
                "read file",
                "find file",
                "search file",
                "create file",
                "delete file",
                "rename file",
            ],

            "application_control": [
                "open app",
                "open application",
                "close app",
                "launch",
                "start application",
            ],

            "calculation": [
                "calculate",
                "solve",
                "how much is",
                "plus",
                "minus",
                "multiply",
                "divide",
            ],

            "time_date": [
                "what time",
                "current time",
                "today",
                "what date",
                "current date",
            ],

            "web_search": [
                "search web",
                "search online",
                "search internet",
                "look up",
                "find online",
            ],

            "help": [
                "help",
                "what can you do",
                "commands",
                "features",
            ],

            "exit": [
                "exit",
                "quit",
                "close pat",
                "shutdown pat",
            ],
        }

    def detect_intent(self, text):
        if not isinstance(text, str):
            return "unknown"

        cleaned_text = text.lower().strip()

        if not cleaned_text:
            return "unknown"

        for intent, keywords in self.intent_keywords.items():

            for keyword in keywords:

                if keyword in cleaned_text:
                    return intent

        return "general_conversation"


if __name__ == "__main__":

    engine = IntentEngine()

    test_messages = [
        "hello",
        "what did I say",
        "open a file",
        "calculate 25 plus 10",
        "what time is it",
        "search internet for Python",
        "what can you do",
        "bye",
    ]

    for message in test_messages:
        intent = engine.detect_intent(message)
        print(f"User: {message}")
        print(f"Intent: {intent}")
        print()