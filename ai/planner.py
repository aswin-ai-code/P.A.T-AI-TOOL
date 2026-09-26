class TaskPlanner:

    def __init__(self):
        self.active_plan = None

    def create_plan(self, intent, user_input):
        if not isinstance(user_input, str):
            return []

        user_input = user_input.strip()

        if not user_input:
            return []

        plans = {
            "file_operation": [
                "Understand the requested file operation",
                "Identify the target file or folder",
                "Check required permissions",
                "Execute the file operation",
                "Verify the result",
                "Report the result to the user",
            ],

            "application_control": [
                "Understand the requested application action",
                "Identify the target application",
                "Check whether the action is permitted",
                "Execute the application action",
                "Verify the result",
                "Report the result to the user",
            ],

            "calculation": [
                "Understand the calculation request",
                "Extract the required values and operation",
                "Perform the calculation",
                "Verify the result",
                "Return the result to the user",
            ],

            "web_search": [
                "Understand the information request",
                "Prepare the search query",
                "Search for relevant information",
                "Evaluate the retrieved information",
                "Prepare a clear response",
            ],

            "system_info": [
                "Understand the requested system information",
                "Collect the required system data",
                "Verify the collected information",
                "Return the result to the user",
            ],

            "time_date": [
                "Understand the requested date or time information",
                "Retrieve the required information",
                "Return the result to the user",
            ],

            "memory_recall": [
                "Understand what information the user wants to recall",
                "Search the available conversation context",
                "Identify the relevant information",
                "Return the information to the user",
            ],

            "general_conversation": [
                "Understand the user's message",
                "Generate an appropriate response",
                "Return the response to the user",
            ],
        }

        plan = plans.get(
            intent,
            [
                "Understand the user's request",
                "Determine the required action",
                "Process the request",
                "Verify the result",
                "Respond to the user",
            ],
        )

        self.active_plan = {
            "intent": intent,
            "input": user_input,
            "steps": plan,
            "current_step": 0,
            "status": "planned",
        }

        return plan

    def get_active_plan(self):
        return self.active_plan

    def get_current_step(self):
        if not self.active_plan:
            return None

        steps = self.active_plan["steps"]
        current_step = self.active_plan["current_step"]

        if current_step >= len(steps):
            return None

        return steps[current_step]

    def next_step(self):
        if not self.active_plan:
            return None

        self.active_plan["current_step"] += 1

        if self.active_plan["current_step"] >= len(
            self.active_plan["steps"]
        ):
            self.active_plan["status"] = "completed"
            return None

        return self.get_current_step()

    def complete_plan(self):
        if self.active_plan:
            self.active_plan["current_step"] = len(
                self.active_plan["steps"]
            )
            self.active_plan["status"] = "completed"

    def clear_plan(self):
        self.active_plan = None


if __name__ == "__main__":

    planner = TaskPlanner()

    test_intent = "file_operation"
    test_input = "Open my project file"

    plan = planner.create_plan(
        test_intent,
        test_input,
    )

    print("P.A.T Task Planner Test")
    print("-----------------------")

    print("User:", test_input)
    print("Intent:", test_intent)
    print()

    print("Generated Plan:")

    for number, step in enumerate(plan, start=1):
        print(f"{number}. {step}")

    print()
    print("Current Step:")
    print(planner.get_current_step())