import platform
from datetime import datetime
from zoneinfo import ZoneInfo

import config
from ai.ai_engine import AIEngine
from commands import CommandHandler
from memory import Memory
from tools.app_tools import AppTools
from tools.file_tools import FileTools


class PAT:
    def __init__(self):
        self.name = config.APP_NAME
        self.full_name = config.FULL_NAME
        self.version = config.VERSION

        self.commands = CommandHandler()
        self.memory = Memory()
        self.ai_engine = AIEngine()
        self.app_tools = AppTools()
        self.file_tools = FileTools()

        self.user_name = self.memory.recall("user_name")

    def remember_name(self, name):
        self.user_name = name
        self.memory.remember("user_name", name)
        return f"Nice to meet you, {name}. I will remember your name."

    def greet(self):
        if self.user_name:
            return (
                f"Hello, {self.user_name}! "
                f"I am {self.name}, your Personal Assistant Tool."
            )

        return f"Hello! I am {self.name}, your Personal Assistant Tool."

    def status(self):
        return f"{self.name} v{self.version} is online and ready."

    def get_time(self):
        current_time = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).strftime("%I:%M:%S %p")

        return f"The current time is {current_time}."

    def get_date(self):
        current_date = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).strftime("%d %B %Y")

        return f"Today's date is {current_date}."

    def get_system_info(self):
        return (
            f"Operating System: {platform.system()} {platform.release()}\n"
            f"Computer: {platform.node()}\n"
            f"Processor: {platform.processor()}\n"
            f"Python Version: {platform.python_version()}"
        )

    def help(self):
        return (
            "Available commands:\n"
            "- hello\n"
            "- how are you\n"
            "- what is your name\n"
            "- who are you\n"
            "- thanks\n"
            "- what time is it\n"
            "- today's date\n"
            "- system info\n"
            "- my system\n"
            "- open calculator\n"
            "- open notepad\n"
            "- open browser\n"
            "- open youtube\n"
            "- open google\n"
            "- show current directory\n"
            "- clear screen\n"
            "- status\n"
            "- help\n"
            "- my name is <name>\n"
            "- what is my name\n"
            "- conversation status\n"
            "- clear conversation\n"
            "- exit"
        )

    def process_command(self, command):
        command = command.lower().strip()

        if command.startswith("my name is "):
            name = command.replace("my name is ", "", 1).strip()

            if name:
                return self.remember_name(name)

            return "Please tell me your name."

        if command == "what is my name":
            if self.user_name:
                return f"Your name is {self.user_name}."

            return "I don't know your name yet."

        action = self.commands.identify(command)

        if action == "greeting":
            return self.greet()

        if action == "how_are_you":
            return "I am doing great! I am ready to help you."

        if action == "assistant_name":
            return f"My name is {self.name}, Personal Assistant Tool."

        if action == "who_are_you":
            return "I am P.A.T, your Personal Assistant Tool."

        if action == "thanks":
            if self.user_name:
                return f"You're welcome, {self.user_name}!"

            return "You're welcome!"

        if action == "time":
            return self.get_time()

        if action == "date":
            return self.get_date()

        if action == "system_info":
            return self.get_system_info()

        if action == "status":
            return self.status()

        if action == "conversation_status":
            return (
                f"Conversation context contains "
                f"{self.ai_engine.get_context_count()} messages."
            )

        if action == "clear_conversation":
            self.ai_engine.clear_context()
            return "Conversation context cleared."

        if action == "help":
            return self.help()

        if action == "exit":
            return "Goodbye! P.A.T is shutting down."

        if action == "open_calculator":
            return self.app_tools.open_calculator()

        if action == "open_notepad":
            return self.app_tools.open_notepad()

        if action == "open_browser":
            return self.app_tools.open_browser()

        if action == "open_youtube":
            return self.app_tools.open_youtube()

        if action == "open_google":
            return self.app_tools.open_google()

        if action == "current_directory":
            return self.app_tools.current_directory()

        if action == "clear_screen":
            return self.app_tools.clear_screen()

        if action == "list_files":
            return self.file_tools.list_files()

        if action == "list_folders":
            return self.file_tools.list_folders()

        if action == "file_count":
            return self.file_tools.file_count()

        if action == "folder_count":
            return self.file_tools.folder_count()

        return self.ai_engine.generate_response(command)

