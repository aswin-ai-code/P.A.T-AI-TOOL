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

    def process(self, text, context=None, intent="unknown"):
        if not isinstance(text, str):
            return "Please enter a valid text message."

        if not text.strip():
            return "Please enter a message."

        cleaned_text = text.lower().strip()

        # Remove common punctuation
        for symbol in ["?", "!", ".", ",", ";", ":"]:
            cleaned_text = cleaned_text.replace(symbol, "")

        cleaned_text = " ".join(cleaned_text.split())

        # -----------------------------------------
        # DIRECT COMMON RESPONSES
        # -----------------------------------------

        if cleaned_text in self.responses:
            return self.responses[cleaned_text]

        # Thank-you variations
        thank_you_phrases = [
            "thank you",
            "thanks",
            "thank you very much",
            "thanks a lot",
            "many thanks",
            "thank u",
            "thanks pat",
            "thank you pat",
        ]

        if any(
            phrase in cleaned_text
            for phrase in thank_you_phrases
        ):
            return "You're welcome! I'm happy to help."

        # Greeting
        if intent == "greeting":
            return "Hello! How can I help you?"

        # How are you
        if intent == "how_are_you":
            return "I am doing great! I am ready to help you."

        # Assistant name
        if intent == "assistant_name":
            return "My name is P.A.T, your Personal Assistant Tool."

        # Who are you
        if intent == "who_are_you":
            return (
                "I am P.A.T, a Personal AI Technology "
                "and Personal Assistant Tool."
            )

        # -----------------------------------------
        # TIME / DATE
        # -----------------------------------------

        if intent == "time_date":
            if (
                "date" in cleaned_text
                or "today" in cleaned_text
                or "day" in cleaned_text
            ):
                return "I understand that you are asking for today's date."

            return "I understand that you are asking for the current time."

        # -----------------------------------------
        # MEMORY
        # -----------------------------------------

        if intent == "memory_recall":
            if context:
                user_messages = [
                    message["content"]
                    for message in context
                    if message["role"] == "user"
                ]

                if len(user_messages) >= 2:
                    return f"You said: {user_messages[-2]}"

            return "I don't have a previous message to recall."

        # -----------------------------------------
        # SYSTEM
        # -----------------------------------------

        if intent == "system_info":
            return (
                "I understand that you want information "
                "about your computer system."
            )

        # -----------------------------------------
        # FILES
        # -----------------------------------------

        if intent == "file_operation":
            return (
                "I understand that you want to perform "
                "a file operation."
            )

        # -----------------------------------------
        # APPLICATIONS
        # -----------------------------------------

        if intent == "application_control":
            return (
                "I understand that you want to control "
                "an application."
            )

        # -----------------------------------------
        # CALCULATION
        # -----------------------------------------

        if intent == "calculation":
            return (
                "I understand that you want me to "
                "calculate something."
            )

        # -----------------------------------------
        # WEB SEARCH
        # -----------------------------------------

        if intent == "web_search":
            return (
                "I understand that you want me to "
                "search for information online."
            )

        # -----------------------------------------
        # HELP
        # -----------------------------------------

        if intent == "help":
            return (
                "I can understand commands, remember information, "
                "work with files, control supported applications, "
                "and handle normal conversations."
            )

        # -----------------------------------------
        # EXIT
        # -----------------------------------------

        if intent == "exit":
            return "Goodbye! P.A.T is shutting down."

        # -----------------------------------------
        # GENERAL CONVERSATION
        # -----------------------------------------

        if "how are you" in cleaned_text:
            return "I am doing great! I am ready to help you."

        if (
            "who made you" in cleaned_text
            or "who created you" in cleaned_text
        ):
            return (
                "I was created as a Personal AI Technology "
                "project."
            )

        if "tell me something" in cleaned_text:
            return (
                "Sure! Every useful assistant starts with "
                "understanding the user and responding clearly."
            )

        if (
            "bye" in cleaned_text
            or "goodbye" in cleaned_text
            or "see you" in cleaned_text
        ):
            return "Goodbye! See you soon."

        # -----------------------------------------
        # FALLBACK
        # -----------------------------------------

        return f"I received your message: {text}"