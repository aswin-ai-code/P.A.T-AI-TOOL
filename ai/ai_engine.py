from ai.context import ConversationContext
from ai.intent_engine import IntentEngine
from ai.reasoning_engine import ReasoningEngine
from ai.response import ResponseProcessor


class AIEngine:
    def __init__(self):
        self.mode = "local"

        # Core AI modules
        self.context = ConversationContext()
        self.response_processor = ResponseProcessor()
        self.intent_engine = IntentEngine()
        self.reasoning_engine = ReasoningEngine()

        # Runtime state
        self.last_intent = "unknown"
        self.last_reasoning = None

    def is_available(self):
        return True

    def generate_response(self, prompt):
        # Validate input
        if not isinstance(prompt, str):
            return "Please enter a valid text message."

        if not prompt.strip():
            return "Please enter a message."

        try:
            # -------------------------------------------------
            # STEP 1: Detect user intent
            # -------------------------------------------------
            self.last_intent = self.intent_engine.detect_intent(prompt)

            # -------------------------------------------------
            # STEP 2: Get previous conversation context
            # -------------------------------------------------
            context = self.context.get_messages()

            # -------------------------------------------------
            # STEP 3: Analyze / reason about the request
            # -------------------------------------------------
            self.last_reasoning = self.reasoning_engine.analyze(
                prompt, self.last_intent, context
            )

            # -------------------------------------------------
            # STEP 4: Generate response
            #
            # ResponseProcessor currently accepts:
            # process(text, context=None)
            # -------------------------------------------------
            response = self.response_processor.process(prompt, context)

            # -------------------------------------------------
            # STEP 5: Save conversation
            # -------------------------------------------------
            self.context.add_message("user", prompt)
            self.context.add_message("assistant", response)

            return response

        except (TypeError, ValueError, KeyError)  as error:
            print("AI ERROR:", error)

            return "Sorry, I couldn't process that message."

    # ---------------------------------------------------------
    # AI STATUS
    # ---------------------------------------------------------

    def get_mode(self):
        return self.mode

    def get_intent(self):
        return self.last_intent

    def get_reasoning(self):
        return self.last_reasoning

    # ---------------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------------

    def get_context_count(self):
        return self.context.count()

    def get_context(self):
        return self.context.get_messages()

    def clear_context(self):
        self.context.clear()

        self.last_intent = "unknown"
        self.last_reasoning = None

    # ---------------------------------------------------------
    # TEST
    # ---------------------------------------------------------


if __name__ == "__main__":
    engine = AIEngine()

    print("P.A.T AI Engine Test")
    print("--------------------")

    test_messages = [
        "hello",
        "what did I say",
        "calculate 25 plus 10",
        "open a file",
        "what time is it",
    ]

    for message in test_messages:
        response = engine.generate_response(message)

        print("User:", message)
        print("Intent:", engine.get_intent())
        print("Reasoning:", engine.get_reasoning())
        print("P.A.T:", response)
        print()
