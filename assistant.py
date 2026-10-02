import platform
import string
from datetime import datetime
from zoneinfo import ZoneInfo

from voice import PATVoice

import config
from ai.ai_engine import AIEngine
from ai.planner import TaskPlanner
from ai.task_engine import TaskEngine
from commands import CommandHandler
from memory import Memory
from tools.app_tools import AppTools
from tools.file_tools import FileTools


class PAT:
    def __init__(self):
        self.name = config.APP_NAME
        self.full_name = config.FULL_NAME
        self.version = config.VERSION
        self.voice = PATVoice()

        self.commands = CommandHandler()
        self.memory = Memory()
        self.ai_engine = AIEngine()
        self.app_tools = AppTools()
        self.file_tools = FileTools()

        self.task_planner = TaskPlanner()
        self.task_engine = TaskEngine()

        self.user_name = self.memory.recall("user_name")

        if self.user_name:
            self.user_name = self.user_name.rstrip(
                ".,!?"
            ).strip()

   
    def split_multiple_commands(self, command):
        """
        Split and expand multiple commands.

        Examples:
        open calculator and notepad
        -> open calculator
        -> open notepad

        close calculator and notepad
        -> close calculator
        -> close notepad
        """

        command = command.strip()

        separators = [
            " and then ",
            " then ",
            " and ",
        ]

        parts = [command]

        for separator in separators:
            new_parts = []

            for part in parts:
                new_parts.extend(part.split(separator))

            parts = new_parts

        parts = [
            part.strip(" .,!?;:")
            for part in parts
            if part.strip(" .,!?;:")
        ]

        if len(parts) <= 1:
            return parts

        # -----------------------------------------
        # INHERIT ACTION
        # -----------------------------------------

        first_words = parts[0].split()

        if not first_words:
            return parts

        action_words = {
            "open",
            "close",
            "show",
            "list",
            "start",
            "launch",
        }

        first_action = first_words[0]

        if first_action in action_words:
            expanded_parts = [parts[0]]

            for part in parts[1:]:
                part = part.strip()

                # Already has an action
                if part.split()[0] in action_words:
                    expanded_parts.append(part)
                else:
                    # Inherit action from first command
                    expanded_parts.append(
                        f"{first_action} {part}"
                    )

            return expanded_parts

        return parts
    # -----------------------------------------
    # CONVERSATION CONTEXT
    # -----------------------------------------

    def add_conversation(
        self,
        user_message,
        assistant_message
    ):
        self.ai_engine.context.add_message(
            "user",
            user_message
        )

        self.ai_engine.context.add_message(
            "assistant",
            assistant_message
        )

    def respond(
        self,
        user_message,
        response
    ):
        self.add_conversation(
            user_message,
            response
        )

        return response

    # -----------------------------------------
    # USER NAME
    # -----------------------------------------

    def remember_name(
        self,
        name,
        original_command=None
    ):
        self.user_name = name.rstrip(
            ".,!?"
        ).strip()

        self.memory.remember(
            "user_name",
            self.user_name
        )

        response = (
            f"Nice to meet you, {self.user_name}. "
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
                f"I am {self.name}, "
                "your Personal Assistant Tool."
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

        return (
            f"The current time is "
            f"{current_time}."
        )

    def get_date(self):
        current_date = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).strftime("%d %B %Y")

        return (
            f"Today's date is "
            f"{current_date}."
        )

    def get_system_info(self):
        return (
            f"Operating System: "
            f"{platform.system()} "
            f"{platform.release()}\n"
            f"Computer: {platform.node()}\n"
            f"Processor: {platform.processor()}\n"
            f"Python Version: "
            f"{platform.python_version()}"
        )

    # -----------------------------------------
    # HELP
    # -----------------------------------------

    def help(self):
        return (
            "I can help you with conversation, "
            "time and date, system information, "
            "applications, files, memory, "
            "and other supported tasks."
        )

    # -----------------------------------------
    # APPLICATION CONTROL
    # -----------------------------------------

    def handle_application_control(
        self,
        command
    ):
        command = command.lower().strip()

        command = command.rstrip(
            string.punctuation
        )

        command = command.replace(
            "opn",
            "open"
        )

        command = command.replace(
            "brower",
            "browser"
        )

        command = command.replace(
            "broser",
            "browser"
        )

        command = command.replace(
            "calclator",
            "calculator"
        )

        command = command.replace(
            "calculater",
            "calculator"
        )

        command = command.replace(
            "notpad",
            "notepad"
        )

        command = command.replace(
            "youtub",
            "youtube"
        )

        if (
            "calculator" in command
            or "calc" in command
        ):
            return (
                self.app_tools.open_calculator()
            )

        if "notepad" in command:
            return (
                self.app_tools.open_notepad()
            )

        if "youtube" in command:
            return (
                self.app_tools.open_youtube()
            )

        if "google" in command:
            return (
                self.app_tools.open_google()
            )

        if "browser" in command:
            return (
                self.app_tools.open_browser()
            )

        return (
            "I understood that you want "
            "to control an application, "
            "but I couldn't identify "
            "the application."
        )

    # -----------------------------------------
    # DAY 5 - TASK EXECUTION
    # -----------------------------------------

    def execute_task(self, user_input):
        """Plan and execute an AI task."""

        if not isinstance(
            user_input,
            str
        ):
            return None

        intent = (
            self.ai_engine.intent_engine
            .detect_intent(user_input)
        )

        plan = (
            self.task_planner.create_plan(
                intent,
                user_input
            )
        )

        if not plan:
            return None

        if not self.task_engine.start_task(
            intent,
            user_input,
            plan
        ):
            return None

        while True:
            step = (
                self.task_engine
                .get_current_step()
            )

            if step is None:
                break

            try:
                result = (
                    self._execute_task_step(
                        intent,
                        user_input,
                        step
                    )
                )

                if result is not None:
                    self.task_engine.complete_current_step()

                    if (
                        self.task_engine.get_status()
                        == "completed"
                    ):
                        return result

                else:
                    self.task_engine.fail_task(
                        f"Unable to execute step: "
                        f"{step}"
                    )

                    return None

            except (
                OSError,
                ValueError,
                RuntimeError
            ) as error:
                self.task_engine.fail_task(
                    str(error)
                )

                return None

        return None

    def _execute_task_step(
        self,
        intent,
        user_input,
        step
    ):
        """Execute a single task step."""

        command = (
            user_input.lower().strip()
        )

        step_text = step.lower()

        # -----------------------------------------
        # APPLICATION CONTROL
        # -----------------------------------------

        if intent == "application_control":

            if "execute the action" in step_text:
                return (
                    self.handle_application_control(
                        command
                    )
                )

            if (
                "identify the requested application"
                in step_text
            ):
                return (
                    "Application identified."
                )

            if (
                "determine the requested action"
                in step_text
            ):
                return (
                    "Application action identified."
                )

            if "check permissions" in step_text:
                return (
                    "Application permissions checked."
                )

            if "verify the result" in step_text:
                return (
                    "Application action verified."
                )

        # -----------------------------------------
        # FILE OPERATIONS
        # -----------------------------------------

        if intent == "file_operation":

            if (
                "list" in command
                and "file" in command
            ):
                return (
                    self.file_tools.list_files()
                )

            if (
                "list" in command
                and "folder" in command
            ):
                return (
                    self.file_tools.list_folders()
                )

            if "file count" in command:
                return (
                    self.file_tools.file_count()
                )

            if "folder count" in command:
                return (
                    self.file_tools.folder_count()
                )

            if (
                "execute the operation"
                in step_text
            ):
                return (
                    "File operation identified, "
                    "but a specific file action "
                    "is not currently available."
                )

            if (
                "identify the requested "
                "file operation"
                in step_text
            ):
                return (
                    "File operation identified."
                )

            if (
                "identify the target file "
                "or folder"
                in step_text
            ):
                return (
                    "File or folder target identified."
                )

            if "check permissions" in step_text:
                return (
                    "File operation permissions checked."
                )

            if "verify the result" in step_text:
                return (
                    "File operation verified."
                )

        # -----------------------------------------
        # SYSTEM INFORMATION
        # -----------------------------------------

        if intent == "system_info":

            if "collect" in step_text:
                return self.get_system_info()

            if "identify" in step_text:
                return (
                    "System information request "
                    "identified."
                )

            if "verify" in step_text:
                return (
                    "System information verified."
                )

            if "prepare" in step_text:
                return (
                    "System information prepared."
                )

        # -----------------------------------------
        # TIME / DATE
        # -----------------------------------------

        if intent == "time_date":

            if (
                "date" in command
                or "today" in command
                or "day" in command
            ):
                return self.get_date()

            if "time" in command:
                return self.get_time()

            if "identify" in step_text:
                return (
                    "Time or date request identified."
                )

            if "retrieve" in step_text:
                return self.get_time()

            if "return" in step_text:
                return self.get_time()

        # -----------------------------------------
        # MEMORY RECALL
        # -----------------------------------------

        if (
            intent == "memory_recall"
            and "name" in command
        ):
            if self.user_name:
                return (
                    f"Your name is "
                    f"{self.user_name}."
                )

            return (
                "I don't know your name yet."
            )

        # -----------------------------------------
        # GENERAL FALLBACK
        # -----------------------------------------

        if "understand" in step_text:
            return "Request understood."

        if "determine" in step_text:
            return "Required action determined."

        if "process" in step_text:
            return "Request processed."

        if "verify" in step_text:
            return "Task result verified."

        return None

    # -----------------------------------------
    # NATURAL CONVERSATION ENGINE
    # -----------------------------------------

    def natural_conversation(
        self,
        command
    ):
        text = (
            command.lower()
            .strip()
            .rstrip(string.punctuation)
        )

        # -----------------------------------------
        # HOW ARE YOU
        # -----------------------------------------

        if (
            "how are you" in text
            or "how are you doing" in text
        ):
            return (
                "I am doing great! "
                "I am here and ready to talk "
                "with you."
            )

        # -----------------------------------------
        # FEELING / MOOD
        # -----------------------------------------

        if (
            "i am tired" in text
            or "i'm tired" in text
            or "feeling tired" in text
        ):
            return (
                "You sound tired. "
                "Take a short break, relax for "
                "a while, and get some rest."
            )

        if (
            "i am happy" in text
            or "i'm happy" in text
            or "feeling happy" in text
        ):
            return (
                "That's great to hear! "
                "I am happy that you are feeling good."
            )

        if (
            "i am sad" in text
            or "i'm sad" in text
            or "feeling sad" in text
        ):
            return (
                "I am sorry you are feeling that way. "
                "You can talk to me about it if "
                "you want."
            )

        if (
            "i am bored" in text
            or "i'm bored" in text
        ):
            return (
                "If you're bored, we can talk, "
                "work on P.A.T, or do something "
                "productive."
            )

        # -----------------------------------------
        # WHAT CAN YOU DO
        # -----------------------------------------

        if (
            "what can you do" in text
            or "what are you capable of" in text
            or "what can you help me with" in text
        ):
            return (
                "I can talk with you, remember useful "
                "information, handle supported tasks, "
                "work with applications and files, "
                "give system information, and respond "
                "to your commands."
            )

        # -----------------------------------------
        # THANKS
        # -----------------------------------------

        if (
            "thank you" in text
            or "thanks" in text
        ):
            if self.user_name:
                return (
                    f"You're welcome, "
                    f"{self.user_name}!"
                )

            return "You're welcome!"

        # -----------------------------------------
        # IDENTITY
        # -----------------------------------------

        if (
            "who are you" in text
            or "tell me about yourself" in text
            or "tell me about you" in text
            or "tell me about p.a.t" in text
            or "tell me about pat" in text
        ):
            return (
                "I am P.A.T, your Personal Assistant "
                "Tool. I can communicate with you by "
                "voice, remember useful information, "
                "handle supported tasks, work with "
                "applications and files, provide "
                "system information, and respond to "
                "your commands."
            )

        # -----------------------------------------
        # USER NAME FLEXIBILITY
        # -----------------------------------------

        if (
            "call me " in text
            and len(text) > len("call me ")
        ):
            name = text.replace(
                "call me ",
                "",
                1
            ).strip()

            if name:
                return self.remember_name(
                    name,
                    command
                )

        if (
            text.startswith("i am ")
            and len(text) > len("i am ")
        ):
            possible_name = text.replace(
                "i am ",
                "",
                1
            ).strip()

            if (
                len(
                    possible_name.split()
                ) <= 3
                and possible_name not in {
                    "tired",
                    "happy",
                    "sad",
                    "bored",
                    "fine",
                    "good",
                    "okay",
                    "ok",
                }
            ):
                return self.remember_name(
                    possible_name,
                    command
                )

        # -----------------------------------------
        # NORMAL CONVERSATION
        # -----------------------------------------

        if (
            text.startswith("hello")
            or text.startswith("hi ")
            or text == "hi"
            or text.startswith("hey")
        ):
            return self.greet()

        if "good morning" in text:
            return (
                f"Good morning"
                + (
                    f", {self.user_name}"
                    if self.user_name
                    else ""
                )
                + "! How can I help you?"
            )

        if "good night" in text:
            return (
                "Good night! "
                "Take care and have a good rest."
            )

        # -----------------------------------------
        # UNKNOWN BUT CONVERSATIONAL
        # -----------------------------------------

        if (
            text.startswith("i ")
            or text.startswith("i'm ")
            or text.startswith("i am ")
        ):
            return (
                "I understand. "
                "Tell me more about that."
            )

        if (
            text.startswith("can you ")
            or text.startswith("could you ")
        ):
            return (
                "I can try to help with that. "
                "Tell me exactly what you would "
                "like me to do."
            )

        if (
            text.startswith("what ")
            or text.startswith("why ")
            or text.startswith("how ")
        ):
            return (
                "I understand your question. "
                "I am still expanding my knowledge "
                "and conversation capabilities, "
                "but I can help with the tasks "
                "currently available to me."
            )

        return (
            "I understand what you said. "
            "Tell me more, and I will try to help."
        )

    # -----------------------------------------
    # COMMAND PROCESSING
    # -----------------------------------------

    def process_command(
        self,
        command
    ):

        if not isinstance(command, str):
            return (
                "Please enter a valid message."
            )

        # Keep original Whisper text
        original_command = command.strip()

                # -----------------------------------------
        # MULTI-COMMAND PROCESSING
        # -----------------------------------------

        if isinstance(command, str):
            command_parts = self.split_multiple_commands(command)

            if len(command_parts) > 1:
                responses = []

                for part in command_parts:
                    result = self.process_command(part)

                    if result:
                        responses.append(result)

                return " ".join(responses)

        # Normalize command
        command = command.lower().strip()

        # -----------------------------------------
        # REMOVE P.A.T WAKE WORD
        # -----------------------------------------

        wake_words = (
            "p.a.t",
            "p.a.t.",
            "pat",
            "pat.",
            "p a t",
            "p a t.",
        )

        for wake_word in wake_words:
            if command.startswith(
                wake_word
            ):
                command = command[
                    len(wake_word):
                ].strip()

                break

        # Remove punctuation at the end
        command = command.rstrip(
            string.punctuation
        ).strip()

        if not command:
            return (
                "I am listening. "
                "What would you like to talk about?"
            )

        # -----------------------------------------
        # USER NAME
        # -----------------------------------------

        if command.startswith(
            "my name is "
        ):

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

        # -----------------------------------------
        # MEMORY NAME RECALL
        # -----------------------------------------

        name_questions = {
            "what is my name",
            "but what is my name",
            "what's my name",
            "whats my name",
            "tell me my name",
            "do you know my name",
            "do you remember my name",
        }

        if command in name_questions:

            if self.user_name:
                response = (
                    f"Your name is "
                    f"{self.user_name}."
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

        action = self.commands.identify(
            command
        )

        if action == "greeting":
            return self.respond(
                original_command,
                self.greet()
            )

        if action == "how_are_you":
            return self.respond(
                original_command,
                (
                    "I am doing great! "
                    "I am ready to help you."
                )
            )

        if action == "assistant_name":
            return self.respond(
                original_command,
                (
                    f"My name is {self.name}, "
                    "Personal Assistant Tool."
                )
            )

        if action == "who_are_you":
            return self.respond(
                original_command,
                (
                    "I am P.A.T, your Personal "
                    "Assistant Tool."
                )
            )

        if action == "thanks":

            if self.user_name:
                response = (
                    f"You're welcome, "
                    f"{self.user_name}!"
                )

            else:
                response = (
                    "You're welcome!"
                )

            return self.respond(
                original_command,
                response
            )

        if action == "time":
            return self.respond(
                original_command,
                self.get_time()
            )

        # -----------------------------------------
        # DATE
        # -----------------------------------------

        if action == "date":
            return self.respond(
                original_command,
                self.get_date()
            )

        # -----------------------------------------
        # SYSTEM INFORMATION
        # -----------------------------------------

        if action == "system_info":
            return self.respond(
                original_command,
                self.get_system_info()
            )

        # -----------------------------------------
        # STATUS
        # -----------------------------------------

        if action == "status":
            return self.respond(
                original_command,
                self.status()
            )

        # -----------------------------------------
        # HELP
        # -----------------------------------------

        if action == "help":
            return self.respond(
                original_command,
                self.help()
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
        # UNIVERSAL PC CONTROL
        # -----------------------------------------

        if action == "close_calculator":
            return self.respond(
                original_command,
                self.app_tools.close_calculator()
            )

        if action == "close_notepad":
            return self.respond(
                original_command,
                self.app_tools.close_notepad()
            )

        if action == "close_browser":
            return self.respond(
                original_command,
                self.app_tools.close_browser()
            )

        if action == "show_desktop":
            return self.respond(
                original_command,
                self.app_tools.show_desktop()
            )

        if action == "minimize_window":
            return self.respond(
                original_command,
                self.app_tools.minimize_window()
            )

        if action == "maximize_window":
            return self.respond(
                original_command,
                self.app_tools.maximize_window()
            )

        if action == "lock_computer":
            return self.respond(
                original_command,
                self.app_tools.lock_computer()
            )

        # -----------------------------------------
        # SPECIFIC FILE / FOLDER CONTROL
        # -----------------------------------------

        cleaned_command = command.strip(
            " .,!?;"
        )

        # -----------------------------------------
        # OPEN SPECIFIC FILE
        # -----------------------------------------

        if cleaned_command.startswith(
            "open file"
        ):

            target = cleaned_command[
                len("open file"):
            ].strip(
                " .,!?;"
            )

            if target:
                return self.respond(
                    original_command,
                    self.app_tools.open_specific_file(
                        target
                    )
                )

        # -----------------------------------------
        # OPEN SPECIFIC FOLDER
        # -----------------------------------------

        folder_command = cleaned_command

        # Common Whisper mistake:
        # "holder tools" -> "open folder tools"
        if folder_command.startswith(
            "holder "
        ):
            folder_command = (
                "open folder "
                + folder_command[
                    len("holder "):
                ]
            )

        # "folder tools" -> "open folder tools"
        elif folder_command.startswith(
            "folder "
        ):
            folder_command = (
                "open folder "
                + folder_command[
                    len("folder "):
                ]
            )

        if folder_command.startswith(
            "open folder"
        ):

            target = folder_command[
                len("open folder"):
            ].strip(
                " .,!?;"
            )

            # Convert internal commas to spaces.
            # Example:
            # "tools, open" -> "tools open"
            target = target.replace(
                ",",
                " "
            )

            target = " ".join(
                target.split()
            )

            # Remove accidental trailing words
            # produced by Whisper.
            trailing_words = (
                "open",
                "please",
                "now",
            )

            for word in trailing_words:

                if target.endswith(
                    " " + word
                ):
                    target = target[
                        :-len(word)
                    ].strip()

            # Whisper may recognize A.I.
            # as a folder name.
            target = target.replace(
                "a.i.",
                "ai"
            )

            target = target.replace(
                "a.i",
                "ai"
            )

            if target:
                return self.respond(
                    original_command,
                    self.app_tools.open_specific_folder(
                        target
                    )
                )
        # -----------------------------------------
        # CLOSE SPECIFIC FOLDER
        # -----------------------------------------

        close_folder_command = cleaned_command

        # "close tools folder"
        if (
            close_folder_command.startswith("close ")
            and close_folder_command.endswith(" folder")
        ):
            target = close_folder_command[
                len("close "):-len(" folder")
            ].strip()

        # "close folder tools"
        elif close_folder_command.startswith(
            "close folder "
        ):
            target = close_folder_command[
                len("close folder "):
            ].strip()

        else:
            target = ""

        if target:
            target = target.replace(",", " ")
            target = " ".join(target.split())

            # Handle Whisper variations
            target = target.replace("a.i.", "ai")
            target = target.replace("a.i", "ai")

            return self.respond(
                original_command,
                self.app_tools.close_specific_folder(
                    target
                )
            )

        # -----------------------------------------
        # GENERIC FILE / FOLDER COMMANDS
        # -----------------------------------------

        if action == "open_file":
            return self.respond(
                original_command,
                self.app_tools.open_file()
            )

        if action == "open_folder":
            return self.respond(
                original_command,
                self.app_tools.open_folder()
            )

        # -----------------------------------------
        # FILE OPERATIONS
        # -----------------------------------------

        if action == "file_operation":

            response = self.execute_task(
                original_command
            )

            if response:
                return self.respond(
                    original_command,
                    response
                )

        # -----------------------------------------
        # SYSTEM / TASK EXECUTION
        # -----------------------------------------

        task_response = self.execute_task(
            original_command
        )

        if task_response:
            return self.respond(
                original_command,
                task_response
            )

        # -----------------------------------------
        # NATURAL CONVERSATION
        # -----------------------------------------

        response = self.natural_conversation(
            original_command
        )

        return self.respond(
            original_command,
            response
        )