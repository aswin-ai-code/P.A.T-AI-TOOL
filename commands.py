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
            "open notepad": "open_notepad",
            "open browser": "open_browser",
            "open youtube": "open_youtube",
            "open google": "open_google",
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

    def identify(self, command):
        command = command.lower().strip()

        commands = self.get_commands()

        return commands.get(command, "unknown")
