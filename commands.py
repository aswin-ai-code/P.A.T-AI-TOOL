
"""Root-level command handling for P.A.T."""

from __future__ import annotations

import re
from typing import Final


class CommandHandler:
    """Recognize direct commands and normalize spoken input."""

    COMMANDS: Final[dict[str, str]] = {
        # Greetings and conversation
        "hello": "greeting",
        "hi": "greeting",
        "hey": "greeting",
        "hello pat": "greeting",
        "hi pat": "greeting",
        "hey pat": "greeting",
        "good morning": "greeting",
        "good afternoon": "greeting",
        "good evening": "greeting",
        "how are you": "how_are_you",
        "how are you doing": "how_are_you",
        "what is your name": "assistant_name",
        "what's your name": "assistant_name",
        "who are you": "who_are_you",
        "thanks": "thanks",
        "thank you": "thanks",

        # Time and date
        "what time is it": "time",
        "what is the time": "time",
        "tell me the time": "time",
        "current time": "time",
        "time now": "time",
        "today's date": "date",
        "todays date": "date",
        "what is today's date": "date",
        "what date is today": "date",
        "tell me today's date": "date",
        "current date": "date",

        # System information
        "system info": "system_info",
        "system information": "system_info",
        "my system": "system_info",
        "computer info": "system_info",
        "what system am i using": "system_info",

        # Applications
        "open calculator": "open_calculator",
        "open notepad": "open_notepad",
        "open browser": "open_browser",
        "open chrome": "open_browser",
        "open youtube": "open_youtube",
        "open google": "open_google",

        # Files and directories
        "show current directory": "current_directory",
        "current directory": "current_directory",
        "where am i": "current_directory",
        "list files": "list_files",
        "show files": "list_files",
        "show me the files": "list_files",
        "list folders": "list_folders",
        "show folders": "list_folders",
        "show me the folders": "list_folders",
        "file count": "file_count",
        "count files": "file_count",
        "folder count": "folder_count",
        "count folders": "folder_count",

        # Conversation and utilities
        "clear screen": "clear_screen",
        "clear conversation": "clear_conversation",
        "clear chat": "clear_conversation",
        "status": "status",
        "pat status": "status",
        "help": "help",

        # Conversation completion
    "that's it": "conversation_done",
    "thats it": "conversation_done",
    "that is it": "conversation_done",
    "that's all": "conversation_done",
    "thats all": "conversation_done",
    "that is all": "conversation_done",
    # Exit
        "exit": "exit",
        "quit": "exit",
        "bye": "exit",
        "goodbye": "exit",
        "stop": "exit",
    }

    PREFIXES: Final[tuple[str, ...]] = ("p.a.t", "pat")

    @classmethod
    def normalize(cls, command: str) -> str:
        """Normalize text and remove an optional spoken P.A.T prefix."""
        if not isinstance(command, str):
            return ""

        text = command.casefold().strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[.!?,;:]+$", "", text).strip()

        for prefix in cls.PREFIXES:
            if text == prefix:
                return ""

            text = re.sub(
                rf"^{re.escape(prefix)}(?:[\s,.:!_-]+)",
                "",
                text,
                count=1,
            ).strip()

        text = re.sub(r"^(?:but|well|um|uh)\s+", "", text).strip()
        return text
    def get_commands(self) -> dict[str, str]:
        """Return a copy of the command map."""
        return dict(self.COMMANDS)

    def identify(self, command: str) -> str:
        """Identify normalized commands."""
        normalized = self.normalize(command)
        return self.COMMANDS.get(normalized, "unknown")

    def is_known(self, command: str) -> bool:
        """Return whether a command has a direct mapping."""
        return self.identify(command) != "unknown"

    def register(
        self,
        phrase: str,
        intent: str,
        *,
        overwrite: bool = False,
    ) -> bool:
        """Register an additional command phrase."""
        normalized_phrase = self.normalize(phrase)
        normalized_intent = intent.strip() if isinstance(intent, str) else ""

        if not normalized_phrase or not normalized_intent:
            return False

        if normalized_phrase in self.COMMANDS and not overwrite:
            return False

        # COMMANDS is intentionally mutable so custom commands can be added.
        self.COMMANDS[normalized_phrase] = normalized_intent
        return True

    def get_supported_commands(self) -> list[str]:
        """Return supported phrases in alphabetical order."""
        return sorted(self.COMMANDS)
