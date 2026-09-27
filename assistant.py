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

    # -----------------------------------------
    # CONVERSATION CONTEXT
    # -----------------------------------------

    def add_conversation(self, user_message, assistant_message):
        self.ai_engine.context.add_message(
            "user",
            user_message
        )

        self.ai_engine.context.add_message(
            "assistant",
            assistant_message
        )

    def respond(self, user_message, response):
        self.add_conversation(
            user_message,
            response
        )

        return response

    # -----------------------------------------
    # USER NAME
    # -----------------------------------------

    def remember_name(self, name, original_command=None):
        self.user_name = name

        self.memory.remember(
            "user_name",
            name
        )

        response = (
            f"Nice to meet you, {name}. "
            "I will remember your name."
        )

        if original_command:
            return self.respond(
                original_command,
                response
            )

        return response

    # -----------------------------------------
    # BASIC INFORMATION
    # -----------------------------------------

    def greet(self):
        if self.user_name:
            return (
                f"Hello, {self.user_name}! "
                f"I am {self.name}, your Personal Assistant Tool."
            )

        return (
            f"Hello! I am {self.name}, "
            "your Personal Assistant Tool."
        )

    def status(self):
        return (
            f"{self.name} v{self.version} "
            "is online and ready."
        )

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
            f"Operating System: "
            f"{platform.system()} {platform.release()}\n"
            f"Computer: {platform.node()}\n"
            f"Processor: {platform.processor()}\n"
            f"Python Version: {platform.python_version()}"
        )

    # -----------------------------------------
    # HELP
    # -----------------------------------------

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

    # -----------------------------------------
    # APPLICATION CONTROL
    # -----------------------------------------

    def handle_application_control(self, command):
        command = command.lower().strip()

        command = command.replace("opn", "open")
        command = command.replace("brower", "browser")
        command = command.replace("broser", "browser")
        command = command.replace("calclator", "calculator")
        command = command.replace("calculater", "calculator")
        command = command.replace("notpad", "notepad")
        command = command.replace("youtub", "youtube")

        if "calculator" in command or "calc" in command:
            return self.app_tools.open_calculator()

        if "notepad" in command:
            return self.app_tools.open_notepad()

        if "youtube" in command:
            return self.app_tools.open_youtube()

        if "google" in command:
            return self.app_tools.open_google()

        if "browser" in command:
            return self.app_tools.open_browser()

        return (
            "I understood that you want to control "
            "an application, but I couldn't identify "
            "the application."
        )

    # -----------------------------------------
    # COMMAND PROCESSING
    # -----------------------------------------

    def process_command(self, command):
        if not isinstance(command, str):
            return "Please enter a valid message."

        original_command = command.strip()
        command = command.lower().strip()

        if not command:
            return "Please enter a message."

        # -----------------------------------------
        # USER NAME
        # -----------------------------------------

        if command.startswith("my name is "):
            name = command.replace(
                "my name is ",
                "",
                1
            ).strip()

            if name:
                return self.remember_name(
                    name,
                    original_command
                )

            return self.respond(
                original_command,
                "Please tell me your name."
            )

        if command == "what is my name":
            if self.user_name:
                response = (
                    f"Your name is {self.user_name}."
                )
            else:
                response = (
                    "I don't know your name yet."
                )

            return self.respond(
                original_command,
                response
            )

        # -----------------------------------------
        # EXACT COMMAND IDENTIFICATION
        # -----------------------------------------

        action = self.commands.identify(command)

        if action == "greeting":
            return self.respond(
                original_command,
                self.greet()
            )

        if action == "how_are_you":
            return self.respond(
                original_command,
                "I am doing great! I am ready to help you."
            )

        if action == "assistant_name":
            return self.respond(
                original_command,
                f"My name is {self.name}, Personal Assistant Tool."
            )

        if action == "who_are_you":
            return self.respond(
                original_command,
                "I am P.A.T, your Personal Assistant Tool."
            )

        if action == "thanks":
            if self.user_name:
                response = (
                    f"You're welcome, {self.user_name}!"
                )
            else:
                response = "You're welcome!"

            return self.respond(
                original_command,
                response
            )

        if action == "time":
            return self.respond(
                original_command,
                self.get_time()
            )

        if action == "date":
            return self.respond(
                original_command,
                self.get_date()
            )

        if action == "system_info":
            return self.respond(
                original_command,
                self.get_system_info()
            )

        if action == "status":
            return self.respond(
                original_command,
                self.status()
            )

        if action == "conversation_status":
            response = (
                "Conversation context contains "
                f"{self.ai_engine.get_context_count()} "
                "messages."
            )

            return self.respond(
                original_command,
                response
            )

        if action == "clear_conversation":
            self.ai_engine.clear_context()

            return self.respond(
                original_command,
                "Conversation context cleared."
            )

        if action == "help":
            return self.respond(
                original_command,
                self.help()
            )

        if action == "exit":
            return self.respond(
                original_command,
                "Goodbye! P.A.T is shutting down."
            )

        # -----------------------------------------
        # APPLICATION CONTROL
        # -----------------------------------------

        if action == "open_calculator":
            return self.respond(
                original_command,
                self.app_tools.open_calculator()
            )

        if action == "open_notepad":
            return self.respond(
                original_command,
                self.app_tools.open_notepad()
            )

        if action == "open_browser":
            return self.respond(
                original_command,
                self.app_tools.open_browser()
            )

        if action == "open_youtube":
            return self.respond(
                original_command,
                self.app_tools.open_youtube()
            )

        if action == "open_google":
            return self.respond(
                original_command,
                self.app_tools.open_google()
            )

        # -----------------------------------------
        # DIRECTORY
        # -----------------------------------------

        if action == "current_directory":
            return self.respond(
                original_command,
                self.app_tools.current_directory()
            )

        if action == "clear_screen":
            return self.respond(
                original_command,
                self.app_tools.clear_screen()
            )

        # -----------------------------------------
        # FILE OPERATIONS
        # -----------------------------------------

        if action == "list_files":
            return self.respond(
                original_command,
                self.file_tools.list_files()
            )

        if action == "list_folders":
            return self.respond(
                original_command,
                self.file_tools.list_folders()
            )

        if action == "file_count":
            return self.respond(
                original_command,
                self.file_tools.file_count()
            )

        if action == "folder_count":
            return self.respond(
                original_command,
                self.file_tools.folder_count()
            )

        # -----------------------------------------
        # NATURAL LANGUAGE INTENT ROUTING
        # -----------------------------------------

        if action == "unknown":
            intent = (
                self.ai_engine.intent_engine.detect_intent(
                    command
                )
            )

            if intent == "application_control":
                response = self.handle_application_control(
                    command
                )

                return self.respond(
                    original_command,
                    response
                )

            if intent == "time_date":
                if (
                    "date" in command
                    or "today" in command
                    or "day" in command
                ):
                    response = self.get_date()
                else:
                    response = self.get_time()

                return self.respond(
                    original_command,
                    response
                )

            if intent == "greeting":
                return self.respond(
                    original_command,
                    self.greet()
                )

            if intent == "help":
                return self.respond(
                    original_command,
                    self.help()
                )

            if intent == "exit":
                return self.respond(
                    original_command,
                    "Goodbye! P.A.T is shutting down."
                )

        # -----------------------------------------
        # AI FALLBACK
        # -----------------------------------------

        return self.ai_engine.generate_response(
            original_command
        )


if __name__ == "__main__":
    pat = PAT()

    print(pat.process_command("Hello"))
    print(pat.process_command("My name is Aswin"))
    print(pat.process_command("What is my name"))

    print(
        "Context:",
        pat.ai_engine.get_context_count()
    )

    print(
        pat.ai_engine.get_context()
    )