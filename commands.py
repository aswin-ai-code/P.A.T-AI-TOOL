
class CommandHandler:
    def get_commands(self):
        return {
            # -----------------------------------------
            # GREETINGS
            # -----------------------------------------
            "hello": "greeting",
            "hi": "greeting",
            "hey": "greeting",
            "good morning": "greeting",
            "good afternoon": "greeting",
            "good evening": "greeting",

            # -----------------------------------------
            # CONVERSATION
            # -----------------------------------------
            "how are you": "how_are_you",
            "how are you doing": "how_are_you",
            "what is your name": "assistant_name",
            "who are you": "who_are_you",
            "thanks": "thanks",
            "thank you": "thanks",

            # -----------------------------------------
            # TIME
            # -----------------------------------------
            "what time is it": "time",
            "what is the time": "time",
            "tell me the time": "time",
            "current time": "time",

            # -----------------------------------------
            # DATE
            # -----------------------------------------
            "today's date": "date",
            "what is today's date": "date",
            "what date is today": "date",
            "tell me today's date": "date",
            "current date": "date",

            # -----------------------------------------
            # SYSTEM
            # -----------------------------------------
            "system info": "system_info",
            "my system": "system_info",
            "computer info": "system_info",
            "what system am i using": "system_info",

            # -----------------------------------------
            # APPLICATIONS
            # -----------------------------------------
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

            # -----------------------------------------
            # UNIVERSAL PC CONTROL
            # -----------------------------------------
            "close calculator": "close_calculator",
            "close notepad": "close_notepad",
            "close browser": "close_browser",

            "open file": "open_file",
            "open folder": "open_folder",

            "show desktop": "show_desktop",
            "minimize window": "minimize_window",
            "maximize window": "maximize_window",

            "lock computer": "lock_computer",
            "shutdown computer": "shutdown_computer",
            "restart computer": "restart_computer",

            # -----------------------------------------
            # DIRECTORY
            # -----------------------------------------
            "show current directory": "current_directory",
            "current directory": "current_directory",
            "where am i": "current_directory",

            # -----------------------------------------
            # FILES
            # -----------------------------------------
            "list files": "list_files",
            "show files": "list_files",

            "list folders": "list_folders",
            "show folders": "list_folders",

            "file count": "file_count",
            "folder count": "folder_count",

            # -----------------------------------------
            # UTILITY
            # -----------------------------------------
            "clear screen": "clear_screen",
            "status": "status",
            "help": "help",

            # -----------------------------------------
            # EXIT
            # -----------------------------------------
            "exit": "exit",
            "quit": "exit",
            "bye": "exit",
            "goodbye": "exit",
        }

    def normalize_command(self, command):
        if not isinstance(command, str):
            return ""

        command = command.lower().strip()

        # -----------------------------------------
        # REMOVE VOICE PUNCTUATION
        # -----------------------------------------
        for symbol in ["?", "!", ".", ",", ";", ":"]:
            command = command.replace(symbol, " ")

        # -----------------------------------------
        # NORMALIZE SPACES
        # -----------------------------------------
        command = " ".join(command.split())

        # -----------------------------------------
        # PHRASE-LEVEL SPEECH CORRECTIONS
        # -----------------------------------------
        phrase_replacements = {
            # Notepad Whisper variations
            "not pad": "notepad",
            "not bad": "notepad",
            "note pad": "notepad",
            "note bad": "notepad",

            # Calculator variations
            "cal culator": "calculator",

            # Browser variations
            "web browser": "browser",

            # YouTube variations
            "you tube": "youtube",

            # Goodbye variations
            "good bye": "goodbye",
            "bye bye": "bye",

            # P.A.T variations
            "p a t": "pat",
        }

        for wrong, correct in phrase_replacements.items():
            command = command.replace(wrong, correct)

        # -----------------------------------------
        # WORD-LEVEL SPEECH / TYPING CORRECTIONS
        # -----------------------------------------
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
            "bat": "pat",
            "p.a.t": "pat",
        }

        words = command.split()

        words = [
            replacements.get(word, word)
            for word in words
        ]

        return " ".join(words)

    def identify(self, command):
        command = self.normalize_command(command)

        if not command:
            return "unknown"

        commands = self.get_commands()

        return commands.get(command, "unknown")

