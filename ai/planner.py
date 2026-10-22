
"""
P.A.T Advanced Task Planner
===========================

Converts user goals into structured, dependency-aware execution plans.

Features:
- Intent-aware planning.
- Task decomposition and dependency tracking.
- Priority and risk classification.
- Approval requirements for sensitive actions.
- Cycle detection and execution-order generation.
- Plan validation, status updates, and serialization.
- Thread-safe in-memory plan management.

This module creates plans only. It does not execute commands or operate
the computer directly. Execution belongs to an authorized task engine.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


@dataclass(slots=True)
class PlanStep:
    """One step in a planned task."""

    step_id: str
    description: str
    action_type: str = "general"
    priority: int = 3
    risk: str = "low"
    requires_approval: bool = False
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TaskPlan:
    """Complete execution plan for a user goal."""

    plan_id: str
    goal: str
    intent: str
    created_at: float
    steps: list[PlanStep] = field(default_factory=list)
    status: str = "pending"
    requires_approval: bool = False
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        return result


class Planner:
    """Dependency-aware planning engine for P.A.T."""

    INTENT_STEPS: ClassVar[dict[str, list[str]]] = {
        "coding": [
            "Clarify requirements and expected behavior.",
            "Inspect the relevant project files and dependencies.",
            "Design the implementation and compatibility approach.",
            "Implement the changes while preserving required features.",
            "Review error handling, security, and edge cases.",
            "Run the relevant tests and verify the results.",
        ],
        "planning": [
            "Clarify the desired outcome and constraints.",
            "Break the goal into smaller actionable tasks.",
            "Identify dependencies, resources, and risks.",
            "Order tasks by priority and dependency.",
            "Define completion criteria and verification steps.",
        ],
        "browser_search": [
            "Clarify the search topic and required information.",
            "Search appropriate sources using an authorized browser tool.",
            "Compare source credibility and freshness.",
            "Summarize findings with supporting references.",
        ],
        "download": [
            "Identify the requested file and trusted source.",
            "Check destination, file type, and available disk space.",
            "Request approval if required by the action policy.",
            "Download using an authorized tool.",
            "Verify file integrity and report the outcome.",
        ],
        "file_operation": [
            "Identify the target file or folder.",
            "Validate the requested operation and target path.",
            "Check whether the operation is destructive.",
            "Request approval when required.",
            "Perform the operation through an authorized tool.",
            "Verify the result and report any errors.",
        ],
        "app_control": [
            "Identify the application and requested operation.",
            "Validate the application and execution method.",
            "Request approval if the operation is sensitive.",
            "Perform the action through an authorized tool.",
            "Verify the observed result.",
        ],
        "security_check": [
            "Define the defensive monitoring scope and permissions.",
            "Collect relevant system and network telemetry.",
            "Correlate indicators and assess risk with uncertainty.",
            "Apply authorized defensive controls when permitted.",
            "Preserve relevant evidence and document the timeline.",
            "Generate a report with findings and limitations.",
        ],
        "automation": [
            "Describe the workflow and desired end state.",
            "Identify inputs, actions, and expected outputs.",
            "Check permissions, dependencies, and failure conditions.",
            "Build a bounded workflow with safe checkpoints.",
            "Require approval for consequential external actions.",
            "Validate the workflow in a controlled test environment.",
        ],
        "memory_store": [
            "Identify the information the user wants to remember.",
            "Check whether the information is appropriate to store.",
            "Save it using the authorized memory interface.",
            "Confirm what was saved without overstating persistence.",
        ],
        "memory_recall": [
            "Identify the requested prior information.",
            "Search the authorized conversation or memory source.",
            "Check the retrieved information for relevance.",
            "Present the result and clearly state any uncertainty.",
        ],
    }

    VALID_STATUSES: ClassVar[set[str]] = {
        "pending",
        "ready",
        "running",
        "completed",
        "failed",
        "cancelled",
        "blocked",
    }

    VALID_RISKS: ClassVar[set[str]] = {
        "low",
        "medium",
        "high",
        "critical",
    }

    def __init__(
        self,
        *,
        max_steps: int = 30,
        require_approval_for_high_risk: bool = True,
    ) -> None:
        self.max_steps = max(1, int(max_steps))
        self.require_approval_for_high_risk = require_approval_for_high_risk
        self._plans: dict[str, TaskPlan] = {}
        self._lock = threading.RLock()

    # ---------------------------------------------------------------
    # Public planning API
    # ---------------------------------------------------------------

    def create_plan(
        self,
        goal: str,
        *,
        intent: str = "general",
        context: Mapping[str, Any] | None = None,
        steps: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create and register a structured plan."""
        normalized_goal = self._validate_goal(goal)
        normalized_intent = str(intent).strip().casefold() or "general"
        context_data = dict(context or {})
        plan_metadata = dict(metadata or {})

        descriptions = self._normalize_steps(steps)
        if not descriptions:
            descriptions = self._derive_steps(
                normalized_goal, normalized_intent, context_data
            )

        if len(descriptions) > self.max_steps:
            descriptions = descriptions[: self.max_steps]

        plan = TaskPlan(
            plan_id=uuid.uuid4().hex,
            goal=normalized_goal,
            intent=normalized_intent,
            created_at=time.time(),
            metadata=plan_metadata,
        )

        plan.steps = self._build_steps(descriptions, normalized_intent)

        if not plan.steps:
            plan.warnings.append(
                "No actionable steps were generated; more detail may be needed."
            )

        plan.requires_approval = any(
            step.requires_approval for step in plan.steps
        )

        if self._contains_ambiguous_goal(normalized_goal):
            plan.warnings.append(
                "The goal may be ambiguous. Clarify requirements before execution."
            )

        with self._lock:
            self._plans[plan.plan_id] = plan

        return plan.to_dict()

    def plan(
        self,
        goal: str,
        *,
        intent: str = "general",
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compatibility alias for create_plan()."""
        return self.create_plan(goal, intent=intent, context=context)

    def build_plan(
        self,
        goal: str,
        *,
        intent: str = "general",
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compatibility alias for create_plan()."""
        return self.create_plan(goal, intent=intent, context=context)

    def get_plan(self, plan_id: str) -> dict[str, Any] | None:
        with self._lock:
            plan = self._plans.get(str(plan_id))
            return plan.to_dict() if plan is not None else None

    def list_plans(self) -> list[dict[str, Any]]:
        with self._lock:
            return [plan.to_dict() for plan in self._plans.values()]

    def delete_plan(self, plan_id: str) -> bool:
        with self._lock:
            return self._plans.pop(str(plan_id), None) is not None

    # ---------------------------------------------------------------
    # Dependency and status management
    # ---------------------------------------------------------------

    def set_dependencies(
        self,
        plan_id: str,
        step_id: str,
        dependencies: Sequence[str],
    ) -> dict[str, Any]:
        with self._lock:
            plan = self._require_plan(plan_id)
            step = self._require_step(plan, step_id)

            dependency_ids = list(dict.fromkeys(map(str, dependencies)))
            known_ids = {item.step_id for item in plan.steps}

            if step_id in dependency_ids:
                raise ValueError("A step cannot depend on itself")

            missing = set(dependency_ids) - known_ids
            if missing:
                raise ValueError(
                    f"Unknown dependency step IDs: {sorted(missing)}"
                )

            original = step.dependencies
            step.dependencies = dependency_ids

            if self._has_cycle(plan.steps):
                step.dependencies = original
                raise ValueError("Dependency change would create a cycle")

            return plan.to_dict()

    def get_execution_order(self, plan_id: str) -> list[str]:
        """Return step IDs in dependency-safe order."""
        with self._lock:
            plan = self._require_plan(plan_id)
            ordered = self._topological_sort(plan.steps)
            return [step.step_id for step in ordered]

    def get_ready_steps(self, plan_id: str) -> list[dict[str, Any]]:
        """Return pending steps whose dependencies are completed."""
        with self._lock:
            plan = self._require_plan(plan_id)
            completed = {
                step.step_id
                for step in plan.steps
                if step.status == "completed"
            }

            ready = [
                step.to_dict()
                for step in plan.steps
                if step.status in {"pending", "ready"}
                and set(step.dependencies).issubset(completed)
                and not step.requires_approval
            ]
            return ready

    def update_step_status(
        self,
        plan_id: str,
        step_id: str,
        status: str,
        *,
        result: Any = None,
    ) -> dict[str, Any]:
        """Update a step status after a trusted executor reports its outcome."""
        normalized_status = str(status).strip().casefold()
        if normalized_status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status {status!r}; expected one of "
                f"{sorted(self.VALID_STATUSES)}"
            )

        with self._lock:
            plan = self._require_plan(plan_id)
            step = self._require_step(plan, step_id)

            if normalized_status == "running":
                completed = {
                    item.step_id
                    for item in plan.steps
                    if item.status == "completed"
                }
                if not set(step.dependencies).issubset(completed):
                    raise ValueError(
                        "Cannot start a step before its dependencies complete"
                    )
                if step.requires_approval:
                    raise PermissionError(
                        "This step requires approval before execution"
                    )

            step.status = normalized_status
            if result is not None:
                step.metadata["last_result"] = result

            statuses = {item.status for item in plan.steps}
            if statuses and statuses.issubset({"completed"}):
                plan.status = "completed"
            elif "failed" in statuses:
                plan.status = "failed"
            elif "running" in statuses:
                plan.status = "running"
            elif "cancelled" in statuses:
                plan.status = "cancelled"
            elif "blocked" in statuses:
                plan.status = "blocked"
            else:
                plan.status = "pending"

            return plan.to_dict()

    # ---------------------------------------------------------------
    # Plan generation
    # ---------------------------------------------------------------

    def _derive_steps(
        self,
        goal: str,
        intent: str,
        context: Mapping[str, Any],
    ) -> list[str]:
        provided = context.get("plan") or context.get("steps")
        if isinstance(provided, Sequence) and not isinstance(
            provided, (str, bytes)
        ):
            normalized = self._normalize_steps(provided)
            if normalized:
                return normalized

        for key, templates in self.INTENT_STEPS.items():
            if intent == key:
                return list(templates)

        return [
            f"Clarify the expected outcome for: {goal}",
            "Identify the required resources, constraints, and permissions.",
            "Break the goal into small, verifiable actions.",
            "Review the plan for dependencies and risks.",
            "Execute approved actions using authorized tools.",
            "Verify the results and report any limitations.",
        ]

    def _build_steps(
        self,
        descriptions: list[str],
        intent: str,
    ) -> list[PlanStep]:
        result: list[PlanStep] = []

        for index, description in enumerate(descriptions, start=1):
            action_type = self._classify_action(description, intent)
            risk = self._assess_risk(description, action_type)
            approval = (
                self.require_approval_for_high_risk
                and risk in {"high", "critical"}
            )

            result.append(
                PlanStep(
                    step_id=f"step_{index:03d}",
                    description=description,
                    action_type=action_type,
                    priority=self._priority_for(action_type, risk),
                    risk=risk,
                    requires_approval=approval,
                    dependencies=(
                        [f"step_{index - 1:03d}"] if index > 1 else []
                    ),
                    metadata={"source": "planner"},
                )
            )

        return result

    @staticmethod
    def _classify_action(description: str, intent: str) -> str:
        text = description.casefold()

        categories = (
            ("verification", ("verify", "test", "validate", "confirm")),
            ("security", ("security", "threat", "incident", "block")),
            ("file_operation", ("delete", "move file", "rename", "copy file")),
            ("download", ("download", "install package")),
            ("browser", ("search", "browse", "web", "internet")),
            ("coding", ("code", "implement", "debug", "program")),
            ("approval", ("approval", "approve", "permission")),
            ("analysis", ("analyze", "inspect", "compare", "review")),
        )

        for category, phrases in categories:
            if any(phrase in text for phrase in phrases):
                return category

        return intent if intent != "general" else "general"

    @staticmethod
    def _assess_risk(description: str, action_type: str) -> str:
        text = description.casefold()

        critical_phrases = (
            "wipe all data",
            "format entire drive",
            "disable all security",
            "delete all backups",
        )
        high_phrases = (
            "delete",
            "overwrite",
            "format disk",
            "change permissions",
            "publish",
            "send payment",
            "modify firewall",
            "block network",
            "install software",
            "administrator",
            "admin privileges",
        )

        if any(phrase in text for phrase in critical_phrases):
            return "critical"

        if any(phrase in text for phrase in high_phrases):
            return "high"

        if action_type in {"file_operation", "download", "security"}:
            return "medium"

        return "low"

    @staticmethod
    def _priority_for(action_type: str, risk: str) -> int:
        if risk == "critical":
            return 1
        if risk == "high":
            return 2
        if action_type in {"analysis", "verification", "security"}:
            return 2
        if action_type == "approval":
            return 1
        return 3

    # ---------------------------------------------------------------
    # Validation and graph algorithms
    # ---------------------------------------------------------------

    @staticmethod
    def _validate_goal(goal: str) -> str:
        if not isinstance(goal, str):
            raise TypeError("goal must be a string")

        normalized = goal.strip()
        if not normalized:
            raise ValueError("goal cannot be empty")
        if len(normalized) > 12_000:
            raise ValueError("goal exceeds the maximum supported length")

        return normalized

    @staticmethod
    def _normalize_steps(
        steps: Sequence[str] | None,
    ) -> list[str]:
        if steps is None:
            return []
        if isinstance(steps, (str, bytes)):
            raise TypeError("steps must be a sequence of step descriptions")

        normalized: list[str] = []
        for step in steps:
            if isinstance(step, str) and step.strip():
                normalized.append(step.strip())

        return normalized

    @staticmethod
    def _contains_ambiguous_goal(goal: str) -> bool:
        normalized = goal.casefold()
        ambiguous_phrases = (
            "do it",
            "fix it",
            "open it",
            "download that",
            "delete that",
            "அதை செய்",
            "அதை பண்ணு",
        )
        return (
            normalized in ambiguous_phrases
            or len(normalized.split()) <= 2
        )

    @staticmethod
    def _has_cycle(steps: list[PlanStep]) -> bool:
        try:
            Planner._topological_sort(steps)
            return False
        except ValueError:
            return True

    @staticmethod
    def _topological_sort(steps: list[PlanStep]) -> list[PlanStep]:
        step_map = {step.step_id: step for step in steps}
        indegree = {step.step_id: 0 for step in steps}
        dependents: dict[str, list[str]] = {
            step.step_id: [] for step in steps
        }

        for step in steps:
            for dependency in step.dependencies:
                if dependency not in step_map:
                    raise ValueError(
                        f"Unknown dependency {dependency!r} "
                        f"for step {step.step_id!r}"
                    )
                indegree[step.step_id] += 1
                dependents[dependency].append(step.step_id)

        ready = [
            step.step_id
            for step in steps
            if indegree[step.step_id] == 0
        ]
        ordered: list[PlanStep] = []

        while ready:
            current_id = ready.pop(0)
            ordered.append(step_map[current_id])

            for dependent_id in dependents[current_id]:
                indegree[dependent_id] -= 1
                if indegree[dependent_id] == 0:
                    ready.append(dependent_id)

        if len(ordered) != len(steps):
            raise ValueError("Plan contains a dependency cycle")

        return ordered

    def _require_plan(self, plan_id: str) -> TaskPlan:
        plan = self._plans.get(str(plan_id))
        if plan is None:
            raise KeyError(f"Plan not found: {plan_id}")
        return plan

    @staticmethod
    def _require_step(plan: TaskPlan, step_id: str) -> PlanStep:
        for step in plan.steps:
            if step.step_id == step_id:
                return step
        raise KeyError(f"Step not found: {step_id}")


TaskPlanner = Planner

__all__ = [
    "PlanStep",
    "Planner",
    "TaskPlan",
    "TaskPlanner",
]
