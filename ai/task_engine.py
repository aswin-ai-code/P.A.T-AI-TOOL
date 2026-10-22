
"""
P.A.T Advanced Task Engine
-------------------------
Manages task lifecycle, step execution, approvals, retries, dependencies,
results, cancellation, and task history.

Safety principles:
- Never execute arbitrary code or shell commands directly.
- Use explicitly registered, trusted handlers for execution.
- Require approval for steps marked as approval-required.
- Do not report success unless a handler confirms success.
- Keep planning and execution separate.
"""

from __future__ import annotations

import threading
import uuid
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, ClassVar

TaskHandler = Callable[..., Any]


@dataclass(slots=True)
class TaskStep:
    """A single executable or informational task step."""

    step_id: str
    description: str
    action: str = "general"
    status: str = "pending"
    depends_on: list[str] = field(default_factory=list)
    requires_approval: bool = False
    approved: bool = False
    attempts: int = 0
    max_retries: int = 0
    result: Any = None
    error: str | None = None
    created_at: str = field(default_factory=lambda: _utc_now())
    started_at: str | None = None
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable step snapshot."""
        return asdict(self)


@dataclass(slots=True)
class TaskRecord:
    """Tracks one task from creation to its final state."""

    task_id: str
    title: str
    user_input: str
    intent: str = "general"
    status: str = "pending"
    steps: list[TaskStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: _utc_now())
    updated_at: str = field(default_factory=lambda: _utc_now())
    started_at: str | None = None
    completed_at: str | None = None
    result: Any = None
    error: str | None = None
    requires_approval: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable task snapshot."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "user_input": self.user_input,
            "intent": self.intent,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": _safe_value(self.result),
            "error": self.error,
            "requires_approval": self.requires_approval,
            "metadata": dict(self.metadata),
        }


class TaskEngine:
    """
    Task orchestration and lifecycle manager for P.A.T.

    Registered handlers are trusted integration points. Each handler is
    responsible for its own authorization, input validation, and safe
    interaction with external resources.

    The engine does not automatically execute arbitrary plan descriptions.
    """

    TASK_STATUSES: ClassVar[frozenset[str]] = frozenset({
        "pending",
        "ready",
        "running",
        "awaiting_approval",
        "completed",
        "failed",
        "cancelled",
        "blocked",
    })

    STEP_STATUSES: ClassVar[frozenset[str]] = frozenset({
        "pending",
        "ready",
        "running",
        "awaiting_approval",
        "completed",
        "failed",
        "cancelled",
        "blocked",
        "skipped",
    })

    TERMINAL_TASK_STATUSES: ClassVar[frozenset[str]] = frozenset({
        "completed",
        "failed",
        "cancelled",
    })

    def __init__(
        self,
        *,
        handlers: Mapping[str, TaskHandler] | None = None,
        max_history: int = 200,
        default_retries: int = 0,
        stop_on_error: bool = True,
    ) -> None:
        self.max_history = max(1, int(max_history))
        self.default_retries = max(0, int(default_retries))
        self.stop_on_error = bool(stop_on_error)

        self._handlers: dict[str, TaskHandler] = {}
        self._tasks: dict[str, TaskRecord] = {}
        self._history: deque[str] = deque(maxlen=self.max_history)
        self._lock = threading.RLock()

        for action, handler in (handlers or {}).items():
            self.register_handler(action, handler)

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def register_handler(
        self,
        action: str,
        handler: TaskHandler,
        *,
        replace: bool = False,
    ) -> None:
        """Register an explicit trusted handler for a named action."""
        name = self._normalize_action(action)

        if not name:
            raise ValueError("Handler action must not be empty.")
        if not callable(handler):
            raise TypeError("Handler must be callable.")

        with self._lock:
            if name in self._handlers and not replace:
                raise ValueError(f"A handler is already registered for '{name}'.")

            self._handlers[name] = handler

    def unregister_handler(self, action: str) -> bool:
        """Remove a registered handler."""
        name = self._normalize_action(action)

        with self._lock:
            return self._handlers.pop(name, None) is not None

    def get_registered_actions(self) -> list[str]:
        """List available handler names."""
        with self._lock:
            return sorted(self._handlers)

    # ------------------------------------------------------------------
    # Task creation and plan import
    # ------------------------------------------------------------------

    def create_task(
        self,
        user_input: str,
        *,
        intent: str = "general",
        title: str | None = None,
        steps: Sequence[Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        requires_approval: bool = False,
    ) -> dict[str, Any]:
        """Create a task from a request and optional planner steps."""
        request = str(user_input or "").strip()
        if not request:
            raise ValueError("Task input must not be empty.")

        normalized_steps = self._normalize_steps(steps or [])
        task_id = uuid.uuid4().hex

        task = TaskRecord(
            task_id=task_id,
            title=str(title or self._make_title(request)).strip(),
            user_input=request,
            intent=str(intent or "general").strip().casefold(),
            steps=normalized_steps,
            requires_approval=bool(requires_approval)
            or any(step.requires_approval for step in normalized_steps),
            metadata=dict(metadata or {}),
        )

        self._validate_dependencies(task.steps)

        with self._lock:
            self._tasks[task_id] = task
            self._history.append(task_id)
            self._refresh_task_status(task)

            return task.to_dict()

    def create_task_from_plan(
        self,
        plan: Any,
        *,
        user_input: str = "",
        intent: str = "general",
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a task from a TaskPlan, dictionary, or plan-like object."""
        plan_steps = self._get_value(plan, "steps", [])
        plan_title = (
            self._get_value(plan, "title")
            or self._get_value(plan, "goal")
            or user_input
            or "P.A.T task"
        )
        plan_id = self._get_value(plan, "plan_id")

        if not user_input:
            user_input = str(
                self._get_value(plan, "user_input")
                or self._get_value(plan, "goal")
                or plan_title
            )

        combined_metadata = dict(metadata or {})
        if plan_id:
            combined_metadata["source_plan_id"] = str(plan_id)

        return self.create_task(
            user_input,
            intent=intent,
            title=str(plan_title),
            steps=plan_steps if isinstance(plan_steps, Sequence) else [],
            metadata=combined_metadata,
            requires_approval=bool(
                self._get_value(plan, "requires_approval", False)
            ),
        )

    # ------------------------------------------------------------------
    # Task and step retrieval
    # ------------------------------------------------------------------

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get a task snapshot by its identifier."""
        with self._lock:
            task = self._tasks.get(str(task_id))
            return task.to_dict() if task else None

    def get_task_status(self, task_id: str) -> str | None:
        """Return the current status of a task."""
        with self._lock:
            task = self._tasks.get(str(task_id))
            return task.status if task else None

    def list_tasks(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List recent tasks, optionally filtered by status."""
        maximum = max(0, int(limit))
        normalized_status = str(status).casefold() if status else None

        with self._lock:
            records = [
                self._tasks[task_id]
                for task_id in reversed(self._history)
                if task_id in self._tasks
                and (
                    normalized_status is None
                    or self._tasks[task_id].status == normalized_status
                )
            ]
            return [task.to_dict() for task in records[:maximum]]

    def get_ready_steps(self, task_id: str) -> list[dict[str, Any]]:
        """Return steps whose dependencies are completed and approvals satisfied."""
        with self._lock:
            task = self._require_task(task_id)
            ready = self._ready_steps(task)
            return [step.to_dict() for step in ready]

    # ------------------------------------------------------------------
    # Approval management
    # ------------------------------------------------------------------

    def approve_step(
        self,
        task_id: str,
        step_id: str,
        *,
        approved: bool = True,
    ) -> dict[str, Any]:
        """
        Record an explicit approval decision.

        Calling this method does not execute the step. A trusted caller
        should invoke it only after the required user approval is obtained.
        """
        with self._lock:
            task = self._require_task(task_id)
            step = self._require_step(task, step_id)

            if task.status in self.TERMINAL_TASK_STATUSES:
                raise ValueError("Cannot approve a step in a finished task.")

            if step.status in {"completed", "running"}:
                raise ValueError(
                    f"Cannot change approval for a '{step.status}' step."
                )

            if not approved:
                step.approved = False
                step.status = "cancelled"
                step.error = "Approval denied."
                step.completed_at = _utc_now()

                if self.stop_on_error:
                    task.status = "blocked"
                    task.error = f"Approval denied for step '{step.step_id}'."
            else:
                step.approved = True
                if step.status == "awaiting_approval":
                    step.status = "pending"
                step.error = None

            self._refresh_task_status(task)
            return task.to_dict()

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute_task(
        self,
        task_id: str,
        *,
        dry_run: bool = False,
        max_steps: int | None = None,
    ) -> dict[str, Any]:
        """
        Execute eligible steps using registered handlers.

        A dry run reports what is ready without invoking handlers.
        Approval-required steps remain blocked until explicitly approved.
        """
        step_limit = None if max_steps is None else max(0, int(max_steps))
        executed = 0

        with self._lock:
            task = self._require_task(task_id)

            if task.status in self.TERMINAL_TASK_STATUSES:
                return self._execution_result(
                    task,
                    message="Task is already in a terminal state.",
                    executed=0,
                )

            if task.status == "blocked" and task.error:
                return self._execution_result(
                    task,
                    message="Task is blocked. Review the error or create a new task.",
                    executed=0,
                )

            if task.started_at is None and not dry_run:
                task.started_at = _utc_now()

            task.status = "ready"
            task.updated_at = _utc_now()

            if dry_run:
                ready = self._ready_steps(task)
                return self._execution_result(
                    task,
                    message="Dry run only; no handlers were invoked.",
                    executed=0,
                    ready_steps=[step.step_id for step in ready],
                )

        while step_limit is None or executed < step_limit:
            with self._lock:
                task = self._require_task(task_id)

                if task.status in self.TERMINAL_TASK_STATUSES:
                    break

                if task.status == "blocked" and task.error:
                    break

                ready = self._ready_steps(task)

                if not ready:
                    self._refresh_task_status(task)
                    break

                step = ready[0]
                handler = self._handlers.get(self._normalize_action(step.action))

                if handler is None:
                    step.status = "blocked"
                    step.error = (
                        f"No registered handler for action '{step.action}'."
                    )
                    step.completed_at = _utc_now()

                    if self.stop_on_error:
                        task.status = "blocked"
                        task.error = step.error
                        task.updated_at = _utc_now()
                        break

                    continue

                step.status = "running"
                step.started_at = step.started_at or _utc_now()
                step.attempts += 1
                task.status = "running"
                task.updated_at = _utc_now()

                # Capture immutable inputs before releasing the lock.
                task_snapshot = task.to_dict()
                step_snapshot = step.to_dict()

            try:
                handler_result = self._invoke_handler(
                    handler,
                    task_snapshot,
                    step_snapshot,
                )
                success, payload, error = self._interpret_handler_result(
                    handler_result
                )
            except Exception as exc:  # noqa: BLE001 - task handler boundary
                success = False
                payload = None
                error = f"{type(exc).__name__}: {exc}"

            with self._lock:
                task = self._require_task(task_id)
                step = self._require_step(task, step_snapshot["step_id"])

                if step.status == "cancelled" or task.status == "cancelled":
                    break

                if success:
                    step.status = "completed"
                    step.result = _safe_value(payload)
                    step.error = None
                    step.completed_at = _utc_now()
                    executed += 1
                else:
                    step.error = error or "Handler did not confirm success."

                    if step.attempts <= step.max_retries:
                        step.status = "pending"
                    else:
                        step.status = "failed"
                        step.completed_at = _utc_now()

                        if self.stop_on_error:
                            task.status = "failed"
                            task.error = step.error

                    task.updated_at = _utc_now()

                self._refresh_task_status(task)

                if task.status in {"failed", "blocked", "cancelled"}:
                    break

        with self._lock:
            task = self._require_task(task_id)
            self._refresh_task_status(task)

            return self._execution_result(
                task,
                message=self._status_message(task.status),
                executed=executed,
            )

    def execute_plan(
        self,
        plan: Any,
        *,
        user_input: str = "",
        intent: str = "general",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Compatibility entry point for AIEngine integrations.

        This method creates a task from the plan and delegates execution
        to registered handlers. Unknown actions are never executed.
        """
        task_data = self.create_task_from_plan(
            plan,
            user_input=user_input,
            intent=intent,
        )
        if dry_run:
            return self.execute_task(task_data["task_id"], dry_run=True)

        return self.execute_task(task_data["task_id"])

    def run_task(
        self,
        task_id: str,
        *,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Compatibility alias for execute_task."""
        return self.execute_task(task_id, dry_run=dry_run)

    # ------------------------------------------------------------------
    # Retry and cancellation
    # ------------------------------------------------------------------

    def retry_step(
        self,
        task_id: str,
        step_id: str,
    ) -> dict[str, Any]:
        """Reset a failed step for an explicit retry."""
        with self._lock:
            task = self._require_task(task_id)
            step = self._require_step(task, step_id)

            if task.status == "cancelled":
                raise ValueError("Cannot retry a cancelled task.")

            if step.status not in {"failed", "blocked"}:
                raise ValueError("Only failed or blocked steps can be retried.")

            if self._normalize_action(step.action) not in self._handlers:
                raise ValueError(
                    f"No registered handler for action '{step.action}'."
                )

            step.status = "pending"
            step.error = None
            step.completed_at = None
            task.status = "pending"
            task.error = None
            task.completed_at = None
            task.updated_at = _utc_now()

            return task.to_dict()

    def cancel_task(
        self,
        task_id: str,
        *,
        reason: str = "Cancelled by user.",
    ) -> dict[str, Any]:
        """
        Cancel a task and mark pending steps as cancelled.

        A currently running handler cannot be forcibly interrupted by
        this synchronous engine. Handlers should implement their own
        cooperative cancellation when needed.
        """
        with self._lock:
            task = self._require_task(task_id)

            if task.status in self.TERMINAL_TASK_STATUSES:
                return task.to_dict()

            task.status = "cancelled"
            task.error = str(reason)
            task.completed_at = _utc_now()
            task.updated_at = _utc_now()

            for step in task.steps:
                if step.status in {
                    "pending",
                    "ready",
                    "awaiting_approval",
                    "blocked",
                }:
                    step.status = "cancelled"
                    step.error = str(reason)
                    step.completed_at = _utc_now()

            return task.to_dict()

    # ------------------------------------------------------------------
    # Internal lifecycle helpers
    # ------------------------------------------------------------------

    def _normalize_steps(self, source_steps: Sequence[Any]) -> list[TaskStep]:
        normalized: list[TaskStep] = []
        seen_ids: set[str] = set()

        for index, item in enumerate(source_steps, start=1):
            if isinstance(item, Mapping):
                raw_id = item.get("step_id", item.get("id", f"step_{index}"))
                description = item.get(
                    "description",
                    item.get("task", item.get("action", f"Step {index}")),
                )
                action = item.get("action", "general")
                dependencies = item.get("depends_on", [])
                approval = bool(item.get("requires_approval", False))
                approved = bool(item.get("approved", False))
                retries = item.get("max_retries", self.default_retries)
                metadata = item.get("metadata", {})
            else:
                raw_id = getattr(
                    item,
                    "step_id",
                    getattr(item, "id", f"step_{index}"),
                )
                description = getattr(
                    item,
                    "description",
                    getattr(item, "task", getattr(item, "action", f"Step {index}")),
                )
                action = getattr(item, "action", "general")
                dependencies = getattr(item, "depends_on", [])
                approval = bool(getattr(item, "requires_approval", False))
                approved = bool(getattr(item, "approved", False))
                retries = getattr(item, "max_retries", self.default_retries)
                metadata = getattr(item, "metadata", {})

            step_id = str(raw_id).strip() or f"step_{index}"

            if step_id in seen_ids:
                raise ValueError(f"Duplicate step ID: '{step_id}'.")
            seen_ids.add(step_id)

            if isinstance(dependencies, str):
                dependencies = [dependencies]
            elif not isinstance(dependencies, Sequence):
                dependencies = []

            normalized.append(
                TaskStep(
                    step_id=step_id,
                    description=str(description).strip() or f"Step {index}",
                    action=self._normalize_action(action) or "general",
                    depends_on=[str(dep) for dep in dependencies],
                    requires_approval=approval,
                    approved=approved,
                    max_retries=max(0, int(retries)),
                    metadata=dict(metadata) if isinstance(metadata, Mapping) else {},
                )
            )

        return normalized

    def _validate_dependencies(self, steps: Sequence[TaskStep]) -> None:
        ids = {step.step_id for step in steps}

        for step in steps:
            unknown = set(step.depends_on) - ids
            if unknown:
                raise ValueError(
                    f"Step '{step.step_id}' has unknown dependencies: "
                    f"{', '.join(sorted(unknown))}."
                )
            if step.step_id in step.depends_on:
                raise ValueError(
                    f"Step '{step.step_id}' cannot depend on itself."
                )

        graph = {step.step_id: step.depends_on for step in steps}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(step_id: str) -> None:
            if step_id in visiting:
                raise ValueError("Task plan contains a dependency cycle.")
            if step_id in visited:
                return

            visiting.add(step_id)
            for dependency in graph[step_id]:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in graph:
            visit(step_id)

    def _ready_steps(self, task: TaskRecord) -> list[TaskStep]:
        completed = {
            step.step_id for step in task.steps if step.status == "completed"
        }

        ready: list[TaskStep] = []
        for step in task.steps:
            if step.status != "pending":
                continue

            if not all(dependency in completed for dependency in step.depends_on):
                continue

            if step.requires_approval and not step.approved:
                step.status = "awaiting_approval"
                continue

            step.status = "ready"
            ready.append(step)

        return ready

    def _refresh_task_status(self, task: TaskRecord) -> None:
        task.updated_at = _utc_now()

        if task.status == "cancelled":
            return

        statuses = [step.status for step in task.steps]

        if not statuses:
            task.status = "completed"
            task.result = {"message": "Task created with no execution steps."}
            task.completed_at = task.completed_at or _utc_now()
            return

        if all(status == "completed" for status in statuses):
            task.status = "completed"
            task.completed_at = task.completed_at or _utc_now()
            task.result = {
                "completed_steps": len(statuses),
                "message": "All task steps completed.",
            }
            task.error = None
            return

        if any(status == "failed" for status in statuses) and self.stop_on_error:
            task.status = "failed"
            task.error = task.error or "One or more steps failed."
            task.completed_at = task.completed_at or _utc_now()
            return

        if any(status == "awaiting_approval" for status in statuses):
            task.status = "awaiting_approval"
            return

        if any(status == "running" for status in statuses):
            task.status = "running"
            return

        if any(status == "blocked" for status in statuses):
            task.status = "blocked"
            return

        if any(status == "pending" for status in statuses):
            task.status = "pending"
            return

        if all(status in {"completed", "skipped", "cancelled"} for status in statuses):
            task.status = "completed"
            task.completed_at = task.completed_at or _utc_now()
            return

        task.status = "pending"

    def _invoke_handler(
        self,
        handler: TaskHandler,
        task_snapshot: Mapping[str, Any],
        step_snapshot: Mapping[str, Any],
    ) -> Any:
        """
        Invoke a registered handler.

        Handler signature:
            handler(task_snapshot=..., step_snapshot=...)

        Positional fallback supports simple legacy handlers. A TypeError
        raised inside a handler may also trigger this fallback, so handlers
        should preferably accept the keyword signature above.
        """
        try:
            return handler(
                task_snapshot=dict(task_snapshot),
                step_snapshot=dict(step_snapshot),
            )
        except TypeError:
            return handler(dict(step_snapshot))

    def _interpret_handler_result(
        self,
        result: Any,
    ) -> tuple[bool, Any, str | None]:
        if isinstance(result, Mapping):
            status = str(result.get("status", "")).casefold()
            explicit_success = result.get("success")

            if explicit_success is True or status in {
                "success",
                "completed",
                "complete",
                "done",
            }:
                return True, result.get("result", result.get("message", result)), None

            if explicit_success is False or status in {"failed", "error"}:
                return (
                    False,
                    None,
                    str(result.get("error") or result.get("message") or "Handler failed."),
                )

            # A generic mapping is not sufficient proof of success.
            return False, None, "Handler did not return an explicit success status."

        if result is True:
            return True, {"message": "Handler confirmed success."}, None

        if result is False or result is None:
            return False, None, "Handler did not confirm success."

        # Non-empty string results are accepted as explicit handler output.
        if isinstance(result, str) and result.strip():
            return True, {"message": result.strip()}, None

        return False, None, "Unsupported handler result format."

    def _execution_result(
        self,
        task: TaskRecord,
        *,
        message: str,
        executed: int,
        ready_steps: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "status": task.status,
            "message": message,
            "executed_steps": executed,
            "ready_steps": list(ready_steps or []),
            "requires_approval": task.status == "awaiting_approval",
            "error": task.error,
            "task": task.to_dict(),
        }

    def _require_task(self, task_id: str) -> TaskRecord:
        task = self._tasks.get(str(task_id))
        if task is None:
            raise KeyError(f"Task not found: '{task_id}'.")
        return task

    def _require_step(self, task: TaskRecord, step_id: str) -> TaskStep:
        for step in task.steps:
            if step.step_id == str(step_id):
                return step
        raise KeyError(f"Step not found: '{step_id}'.")

    def _get_value(
        self,
        obj: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if isinstance(obj, Mapping):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _normalize_action(self, action: Any) -> str:
        return str(action or "general").strip().casefold().replace(" ", "_")

    def _make_title(self, request: str) -> str:
        return request if len(request) <= 80 else f"{request[:77].rstrip()}..."

    def _status_message(self, status: str) -> str:
        messages = {
            "pending": "Task has pending steps.",
            "ready": "Task is ready for execution.",
            "running": "Task execution is in progress.",
            "awaiting_approval": "Approval is required before continuing.",
            "completed": "Task completed.",
            "failed": "Task failed. Review the error details.",
            "cancelled": "Task was cancelled.",
            "blocked": "Task is blocked and needs attention.",
        }
        return messages.get(status, "Task status updated.")


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _safe_value(value: Any) -> Any:
    """Convert common results to JSON-friendly values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Mapping):
        return {str(key): _safe_value(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]

    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return _safe_value(value.to_dict())
        except Exception:  # noqa: BLE001 - fallback for unconvertible objects
            return repr(value)

    return repr(value)


# Compatibility alias for existing imports.
TaskManager = TaskEngine
