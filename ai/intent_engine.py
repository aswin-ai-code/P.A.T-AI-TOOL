import re


class IntentEngine:
    def __init__(self):

        self.intent_keywords = {

            # -------------------------------------------------
            # GREETING
            # -------------------------------------------------

            "greeting": [
                "hello",
                "hi",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
                "vanakkam",
                "vanakam",
                "vanakkam pat",
                "vanakam pat",
            ],

            # -------------------------------------------------
            # HOW ARE YOU
            # -------------------------------------------------

            "how_are_you": [
                "how are you",
                "how are you doing",
                "how r u",
                "epdi iruka",
                "eppadi iruka",
                "epdi irukke",
                "eppadi irukke",
            ],

            # -------------------------------------------------
            # ASSISTANT NAME
            # -------------------------------------------------

            "assistant_name": [
                "what is your name",
                "what's your name",
                "whats your name",
                "tell me your name",
                "your name",
                "what are you called",
            ],

            # -------------------------------------------------
            # WHO ARE YOU
            # -------------------------------------------------

            "who_are_you": [
                "who are you",
                "what are you",
                "tell me about yourself",
                "who made you",
                "who created you",
            ],

            # -------------------------------------------------
            # MEMORY
            # -------------------------------------------------

            "memory_recall": [
                "remember",
                "what did i say",
                "what did i tell you",
                "last message",
                "do you remember",
                "do you remember what i said",
                "what did i just say",
                "what was my last message",
                "nyabagam iruka",
                "nyabagam irukka",
            ],

            # -------------------------------------------------
            # SYSTEM INFORMATION
            # -------------------------------------------------

            "system_info": [
                "system information",
                "system info",
                "computer information",
                "computer info",
                "pc information",
                "pc info",
                "my system",
                "what system am i using",
                "ram",
                "cpu",
                "processor",
                "storage",
            ],

            # -------------------------------------------------
            # FILE OPERATIONS
            # -------------------------------------------------

            "file_operation": [
                "open file",
                "read file",
                "find file",
                "search file",
                "create file",
                "delete file",
                "rename file",
                "show files",
                "list files",
                "files kaatu",
                "file kaatu",
                "files show pannu",
                "file show pannu",
            ],

            # -------------------------------------------------
            # APPLICATION CONTROL
            # -------------------------------------------------

            "application_control": [
                "open app",
                "open application",
                "close app",
                "close application",
                "launch",
                "start application",
                "open calculator",
                "open calc",
                "calculator open",
                "open notepad",
                "notepad open",
                "open browser",
                "browser open",
                "open youtube",
                "youtube open",
                "open google",
                "google open",
                "calculator ah open pannu",
                "calculator open pannu",
                "browser ah open pannu",
                "browser open pannu",
                "youtube ah open pannu",
                "youtube open pannu",
            ],

            # -------------------------------------------------
            # CALCULATION
            # -------------------------------------------------

            "calculation": [
                "calculate",
                "calc",
                "solve",
                "how much is",
                "plus",
                "minus",
                "multiply",
                "times",
                "divide",
                "add",
                "subtract",
            ],

            # -------------------------------------------------
            # TIME / DATE
            # -------------------------------------------------

            "time_date": [
                "what time",
                "current time",
                "tell me the time",
                "tell me current time",
                "time now",
                "what is the time",
                "time enna",
                "neram enna",
                "ippo time enna",
                "now time enna",
                "what date",
                "current date",
                "today's date",
                "date today",
                "what day",
                "what day is it",
                "what day is it today",
                "which day",
                "which day is it",
                "date enna",
                "innaiku date enna",
                "indhaiku date enna",
                "today date enna",
            ],

            # -------------------------------------------------
            # WEB SEARCH
            # -------------------------------------------------

            "web_search": [
                "search web",
                "search online",
                "search internet",
                "look up",
                "find online",
                "search for",
                "search",
                "google search",
                "online la search pannu",
                "internet la search pannu",
            ],

            # -------------------------------------------------
            # HELP
            # -------------------------------------------------

            "help": [
                "help",
                "what can you do",
                "what can u do",
                "commands",
                "features",
                "help me",
                "help pannu",
                "help pannunga",
                "enna panna mudiyum",
                "enna lam panna mudiyum",
                "enna seiya mudiyum",
            ],

            # -------------------------------------------------
            # EXIT
            # -------------------------------------------------

            "exit": [
                "exit",
                "quit",
                "close pat",
                "shutdown pat",
                "goodbye",
                "bye",
                "bye pat",
                "poitu varen",
            ],
        }

        # Common filler words
        self.filler_words = {
            "please",
            "can",
            "you",
            "could",
            "would",
            "will",
            "pat",
            "hey",
            "kindly",
            "just",
            "me",
        }

        # Common spelling / speech variations
        self.spelling_aliases = {
            "wat": "what",
            "wht": "what",
            "pls": "please",
            "plz": "please",
            "u": "you",
            "ur": "your",
            "calclator": "calculator",
            "calculater": "calculator",
            "calcultor": "calculator",
            "brower": "browser",
            "broser": "browser",
            "notpad": "notepad",
            "youtub": "youtube",
            "todays": "today's",
            "opn": "open",
        }

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def _normalize(self, text):

        if not isinstance(text, str):
            return ""

        text = text.lower().strip()

        # Apply spelling aliases
        words = text.split()

        words = [
            self.spelling_aliases.get(word, word)
            for word in words
        ]

        text = " ".join(words)

        # Remove punctuation
        text = re.sub(r"[^\w\s']", " ", text)

        # Normalize spaces
        text = re.sub(r"\s+", " ", text).strip()

        return text

    # ---------------------------------------------------------
    # SAFE PHRASE MATCHING
    # ---------------------------------------------------------

    def _contains_phrase(self, text, phrase):

        if not text or not phrase:
            return False

        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"

        return re.search(pattern, text) is not None

    # ---------------------------------------------------------
    # FILLER WORD REMOVAL
    # ---------------------------------------------------------

    def _remove_filler_words(self, text):

        words = text.split()

        filtered_words = [
            word
            for word in words
            if word not in self.filler_words
        ]

        return " ".join(filtered_words)

    # ---------------------------------------------------------
    # INTENT DETECTION
    # ---------------------------------------------------------

    def detect_intent(self, text):

        if not isinstance(text, str):
            return "unknown"

        cleaned_text = self._normalize(text)

        if not cleaned_text:
            return "unknown"

        # -------------------------------------------------
        # HIGH PRIORITY INTENTS
        # -------------------------------------------------

        priority_intents = [
            "time_date",
            "assistant_name",
            "who_are_you",
            "how_are_you",
            "memory_recall",
            "application_control",
            "file_operation",
            "system_info",
            "help",
            "exit",
            "web_search",
            "calculation",
        ]

        # -------------------------------------------------
        # DIRECT MATCH
        # -------------------------------------------------

        for intent in priority_intents:

            for keyword in self.intent_keywords.get(
                intent,
                []
            ):

                if self._contains_phrase(
                    cleaned_text,
                    keyword
                ):
                    return intent

        # -------------------------------------------------
        # GREETING
        # -------------------------------------------------

        for keyword in self.intent_keywords.get(
            "greeting",
            []
        ):

            if self._contains_phrase(
                cleaned_text,
                keyword
            ):
                return "greeting"

        # -------------------------------------------------
        # REMOVE FILLER WORDS
        # -------------------------------------------------

        simplified_text = self._remove_filler_words(
            cleaned_text
        )

        # -------------------------------------------------
        # MATCH AFTER CLEANUP
        # -------------------------------------------------

        for intent in priority_intents:

            for keyword in self.intent_keywords.get(
                intent,
                []
            ):

                if self._contains_phrase(
                    simplified_text,
                    keyword
                ):
                    return intent

        # -------------------------------------------------
        # GREETING AFTER CLEANUP
        # -------------------------------------------------

        for keyword in self.intent_keywords.get(
            "greeting",
            []
        ):

            if self._contains_phrase(
                simplified_text,
                keyword
            ):
                return "greeting"

        return "general_conversation"


# -------------------------------------------------------------
# TEST
# -------------------------------------------------------------

if __name__ == "__main__":

    engine = IntentEngine()

    print("P.A.T Intent Engine Test")
    print("------------------------")

    test_messages = [

        # English
        "hello",
        "Hey PAT!",
        "Pat, can you tell me the time please?",
        "what time is it?",
        "please tell me the current time",

        # Assistant
        "what is your name?",
        "who are you?",
        "tell me your name",

        # How are you
        "how are you?",
        "how are you doing?",

        # Calculation
        "calculate 25 plus 10",
        "Can you calculate 25 plus 10?",

        # Web
        "search internet for Python",

        # Help
        "what can you do?",

        # Memory
        "what did I say?",

        # Exit
        "bye",

        # Date
        "Pat, can you tell me what day it is today?",
        "Hey PAT, what is the date today please?",

        # Tamil / Tanglish
        "Vanakkam PAT",
        "PAT, epdi iruka?",
        "time enna PAT?",
        "innaiku date enna?",
        "calculator open pannu",
        "browser ah open pannu",
        "enna panna mudiyum?",

        # Typing mistakes
        "wat time is it",
        "calclator open",
        "opn browser",
    ]

    for message in test_messages:

        intent = engine.detect_intent(message)

        print("User:", message)
        print("Intent:", intent)
        print()