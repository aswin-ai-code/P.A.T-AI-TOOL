"""P.A.T Automation Engine — discover AppTools methods."""

import inspect
from collections.abc import Callable
from typing import Any

from tools.app_tools import AppTools


class AutomationEngine:
    def __init__(self) -> None:
        self.app_tools = AppTools()
        self.actions: dict[str, Callable[..., Any]] = {}
        self.discover_actions()

    def discover_actions(self) -> int:
        """Register public methods defined by AppTools."""
        self.actions.clear()

        for name, method in inspect.getmembers(self.app_tools, predicate=callable):
            if name.startswith("_"):
                continue

            # Register only methods defined by AppTools.
            class_method = getattr(AppTools, name, None)
            if class_method is None:
                continue

            if not callable(class_method):
                continue

            self.actions[name.lower()] = method

        return len(self.actions)

    def list_actions(self) -> list[str]:
        return sorted(self.actions)

    def run(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Run a registered method by its exact name."""
        key = name.lower().strip()

        if key not in self.actions:
            return f"Unknown action: {name}"

        return self.actions[key](*args, **kwargs)


if __name__ == "__main__":
    engine = AutomationEngine()
    print(f"Loaded {engine.discover_actions()} actions from AppTools")

    for action in engine.list_actions():
        print(" -", action)
