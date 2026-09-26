class ResponseProcessor:
    def __init__(self):
        self.responses = {
            "hello": "Hello! How can I help you?",
            "hi": "Hi! How can I help you?",
            "hey": "Hey! How can I help you?",
            "thanks": "You're welcome!",
            "thank you": "You're welcome!",
            "good morning": "Good morning! How can I help you today?",
            "good afternoon": "Good afternoon! How can I help you today?",
            "good evening": "Good evening! How can I help you today?",
        }

    def process(self, text, context=None):
        if not isinstance(text, str):
            return "Please enter a valid text message."

        if not text.strip():
            return "Please enter a message."

        cleaned_text = text.lower().strip()

        if cleaned_text in self.responses:
            return self.responses[cleaned_text]

        if "how are you" in cleaned_text:
            return "I am doing great! I am ready to help you."

        if "what can you do" in cleaned_text:
            return (
                "I can handle P.A.T commands, remember information, "
                "control supported applications, work with files, "
                "and process local conversations."
            )

        if "who made you" in cleaned_text or "who created you" in cleaned_text:
            return "I was created as a Personal Assistant Tool project."

        if "tell me something" in cleaned_text:
            return (
                "Sure! Every useful assistant starts with understanding "
                "the user and responding clearly."
            )

        if (
            "what did i just say" in cleaned_text
            or "what did i say" in cleaned_text
            or "what just i say" in cleaned_text
            or "what was my last message" in cleaned_text
            or "what did i tell you" in cleaned_text
            or "do you remember what i said" in cleaned_text
            or ("what" in cleaned_text and "say" in cleaned_text)
        ):
            if context:
                user_messages = [
                    message["content"]
                    for message in context
                    if message["role"] == "user"
                ]

                if len(user_messages) >= 2:
                    return f"You said: {user_messages[-2]}"

            return "I don't have a previous message to recall."

        return f"I received your message: {text}"
