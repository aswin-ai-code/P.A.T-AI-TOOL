class TaskEngine:

    def __init__(self):
        self.current_task = None
        self.status = "idle"

    def start_task(self, intent, user_input, plan):
        if not isinstance(intent, str):
            return False

        if not isinstance(user_input, str):
            return False

        if not isinstance(plan, list) or not plan:
            return False

        self.current_task = {
            "intent": intent,
            "input": user_input,
            "plan": plan,
            "current_step": 0,
            "completed_steps": [],
            "status": "running",
        }

        self.status = "running"

        return True

    def get_current_step(self):
        if not self.current_task:
            return None

        steps = self.current_task["plan"]
        current_step = self.current_task["current_step"]

        if current_step >= len(steps):
            return None

        return steps[current_step]

    def complete_current_step(self):
        if not self.current_task:
            return False

        steps = self.current_task["plan"]
        current_step = self.current_task["current_step"]

        if current_step >= len(steps):
            return False

        completed_step = steps[current_step]

        self.current_task["completed_steps"].append(
            completed_step
        )

        self.current_task["current_step"] += 1

        if self.current_task["current_step"] >= len(steps):
            self.complete_task()

        return True

    def complete_task(self):
        if self.current_task:
            self.current_task["status"] = "completed"

        self.status = "completed"

    def fail_task(self, error_message):
        if self.current_task:
            self.current_task["status"] = "failed"
            self.current_task["error"] = str(error_message)

        self.status = "failed"

    def get_status(self):
        return self.status

    def get_task(self):
        return self.current_task

    def reset(self):
        self.current_task = None
        self.status = "idle"


if __name__ == "__main__":

    engine = TaskEngine()

    test_plan = [
        "Understand the request",
        "Identify the required action",
        "Execute the action",
        "Verify the result",
    ]

    started = engine.start_task(
        "file_operation",
        "Open my project file",
        test_plan,
    )

    print("P.A.T Task Engine Test")
    print("----------------------")

    print("Task Started:", started)
    print("Status:", engine.get_status())
    print()

    while engine.get_current_step():

        print("Current Step:")
        print(engine.get_current_step())

        engine.complete_current_step()

        print("Status:", engine.get_status())
        print()

    print("Final Status:", engine.get_status())