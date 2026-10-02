class CommandHandler:
    def get_commands(self):
        return {
            # Greetings
            "hello": "greeting",
            "hi": "greeting",
            "hey": "greeting",
            "good morning": "greeting",
            "good afternoon": "greeting",
            "good evening": "greeting",
            # Conversation
            "how are you": "how_are_you",
            "how are you doing": "how_are_you",
            "what is your name": "assistant_name",
            "who are you": "who_are_you",
            "thanks": "thanks",
            "thank you": "thanks",
            # Time
            "what time is it": "time",
            "what is the time": "time",
            "tell me the time": "time",
            "current time": "time",
            # Date
            "today's date": "date",
            "what is today's date": "date",
            "what date is today": "date",
            "tell me today's date": "date",
            "current date": "date",
            # System
            "system info": "system_info",
            "my system": "system_info",
            "computer info": "system_info",
            "what system am i using": "system_info",
            # Applications
            "open calculator": "open_calculator",
            "open calc": "open_calculator",
            "calculator open": "open_calculator",
            "open notepad": "open_notepad",
            "notepad open": "open_notepad",
            "open browser": "open_browser",
            "browser open": "open_browser",
            "open youtube": "open_youtube",
            "youtube open": "open_youtube",
            "open google": "open_google",
            "google open": "open_google",
            # Directory
            "show current directory": "current_directory",
            "current directory": "current_directory",
            "where am i": "current_directory",
            # Files
            "list files": "list_files",
            "show files": "list_files",
            "list folders": "list_folders",
            "show folders": "list_folders",
            "file count": "file_count",
            "folder count": "folder_count",
            # Utility
            "clear screen": "clear_screen",
            "status": "status",
            "help": "help",
            # Exit
            "exit": "exit",
            "quit": "exit",
            "bye": "exit",
            "goodbye": "exit",
        }

    def normalize_command(self, command):
        if not isinstance(command, str):
            return ""

        command = command.lower().strip()

        # Remove common voice punctuation
        for symbol in ["?", "!", ".", ",", ";", ":"]:
            command = command.replace(symbol, "")

        # Normalize spaces
        command = " ".join(command.split())

        # Common speech/typing corrections
        replacements = {
            "opn": "open",
            "brower": "browser",
            "broser": "browser",
            "calclator": "calculator",
            "calculater": "calculator",
            "calcultor": "calculator",
            "notpad": "notepad",
            "youtub": "youtube",
            # P.A.T speech recognition
            "bad": "pat",
            "bat": "pat",
            "p a t": "pat",
            "p.a.t": "pat",
            # Common conversation variations
            "good bye": "goodbye",
            "bye bye": "bye",
        }

        words = command.split()

        words = [replacements.get(word, word) for word in words]

        return " ".join(words)

    def identify(self, command):
        command = self.normalize_command(command)

        if not command:
            return "unknown"

        commands = self.get_commands()

        return commands.get(command, "unknown")
