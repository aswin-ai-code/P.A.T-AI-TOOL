
"""
P.A.T Advanced AI Engine
========================

Central orchestration layer for P.A.T's conversational AI.

Responsibilities:
- Maintain bounded conversation context.
- Understand user intent using optional existing modules.
- Produce reasoning and task plans when supported.
- Coordinate responses without assuming every module exists.
- Support optional online/offline language-model providers.
- Handle errors without crashing the entire assistant.
- Expose structured results for integration with the existing P.A.T app.

This module does not execute arbitrary shell commands or access the network
by itself. External actions must be handled by explicitly authorized tools.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AIMessage:
    """A normalized conversation message."""

    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return asdict(self)


@dataclass(slots=True)
class AIResult:
    """Standard result returned by the AI orchestration engine."""

    success: bool
    response: str
    intent: str = "conversation"
    confidence: float = 0.0
    plan: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    needs_clarification: bool = False
    source: str = "local"
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return asdict(self)


class AIEngine:
    """
    Central coordinator for P.A.T AI components.

    The constructor accepts optional component instances, allowing the existing
    project to inject its own intent, context, reasoning, planner, task, and
    response implementations without forcing imports from missing modules.

    Existing integrations can use:
        engine = AIEngine()
        result = engine.process("Hello")
        print(result.response)

    Or inject existing modules:
        engine = AIEngine(intent_engine=my_intent_engine)
    """

    DEFAULT_MAX_HISTORY = 30
    DEFAULT_MAX_MESSAGE_LENGTH = 12_000

    def __init__(
        self,
        *,
        intent_engine: Any | None = None,
        context_engine: Any | None = None,
        reasoning_engine: Any | None = None,
        planner: Any | None = None,
        task_engine: Any | None = None,
        response_engine: Any | None = None,
        online_provider: Any | None = None,
        offline_provider: Any | None = None,
        max_history: int = DEFAULT_MAX_HISTORY,
        max_message_length: int = DEFAULT_MAX_MESSAGE_LENGTH,
        system_prompt: str | None = None,
    ) -> None:
        self.intent_engine = intent_engine
        self.context_engine = context_engine
        self.reasoning_engine = reasoning_engine
        self.planner = planner
        self.task_engine = task_engine
        self.response_engine = response_engine
        self.online_provider = online_provider
        self.offline_provider = offline_provider

        self.max_history = max(2, int(max_history))
        self.max_message_length = max(100, int(max_message_length))
        self.system_prompt = system_prompt or (
            "You are P.A.T, a helpful personal AI assistant. "
            "Be clear, conversational, context-aware, and honest about "
            "uncertainty. Support Tamil and English according to the user's "
            "language. Ask a concise clarifying question when essential "
            "information is missing. Never claim an action succeeded unless "
            "a trusted tool confirms it."
        )

        self._history: deque[AIMessage] = deque(maxlen=self.max_history)
        self._lock = threading.RLock()
        self._request_count = 0
        self._error_count = 0
        self._last_request_at: float | None = None
        self._last_error: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        user_input: str,
        *,
        metadata: Mapping[str, Any] | None = None,
        execute_tasks: bool = False,
    ) -> AIResult:
        """
        Process a user message and return a structured result.

        Task execution is opt-in. When execute_tasks=False, the engine may
        prepare a plan but will not invoke task execution methods.
        """
        text = self._normalize_input(user_input)
        if not text:
            return AIResult(
                success=False,
                response="I didn't receive a message. What would you like help with?",
                error="empty_input",
            )

        request_metadata = dict(metadata or {})
        started_at = time.perf_counter()

        with self._lock:
            self._request_count += 1
            self._last_request_at = time.time()
            self._history.append(AIMessage(role="user", content=text))

            try:
                context = self._build_context(text, request_metadata)
                intent, confidence, intent_data = self._detect_intent(
                    text, context
                )

                if self._needs_clarification(intent_data):
                    response = self._clarification_response(intent_data)
                    result = AIResult(
                        success=True,
                        response=response,
                        intent=intent,
                        confidence=confidence,
                        needs_clarification=True,
                        source="local",
                        metadata={"intent_data": intent_data},
                    )
                else:
                    plan = self._create_plan(text, intent, context, intent_data)
                    task_results: list[dict[str, Any]] = []

                    if execute_tasks and plan:
                        task_results = self._execute_plan(
                            plan, text, intent, context
                        )

                    response, source = self._generate_response(
                        text=text,
                        intent=intent,
                        context=context,
                        plan=plan,
                        task_results=task_results,
                        intent_data=intent_data,
                    )

                    result = AIResult(
                        success=True,
                        response=response,
                        intent=intent,
                        confidence=confidence,
                        plan=plan,
                        actions=task_results,
                        source=source,
                        metadata={
                            "intent_data": intent_data,
                            "elapsed_seconds": round(
                                time.perf_counter() - started_at, 4
                            ),
                        },
                    )

                self._history.append(
                    AIMessage(
                        role="assistant",
                        content=result.response,
                        metadata={
                            "intent": result.intent,
                            "source": result.source,
                        },
                    )
                )
                return result

            except Exception as exc:
                self._error_count += 1
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("P.A.T AI request failed")

                fallback = self._fallback_response(text)
                self._history.append(
                    AIMessage(role="assistant", content=fallback)
                )

                return AIResult(
                    success=False,
                    response=fallback,
                    error=type(exc).__name__,
                    metadata={
                        "elapsed_seconds": round(
                            time.perf_counter() - started_at, 4
                        )
                    },
                )

    def chat(self, user_input: str) -> str:
        """
        Simple string-in/string-out interface for older integrations.

        Use process() when callers need intent, plans, confidence, or metadata.
        """
        return self.process(user_input).response

    def ask(self, user_input: str) -> str:
        """Compatibility-friendly alias for chat()."""
        return self.chat(user_input)

    def get_history(self) -> list[dict[str, Any]]:
        """Return a snapshot of recent conversation history."""
        with self._lock:
            return [message.to_dict() for message in self._history]

    def clear_history(self) -> None:
        """Clear the in-memory conversation history."""
        with self._lock:
            self._history.clear()

    def get_status(self) -> dict[str, Any]:
        """Return engine diagnostics without exposing message contents."""
        with self._lock:
            return {
                "engine": "P.A.T AI Engine",
                "version": "2.0.0",
                "history_messages": len(self._history),
                "max_history": self.max_history,
                "requests_processed": self._request_count,
                "errors": self._error_count,
                "last_request_at": self._last_request_at,
                "last_error": self._last_error,
                "components": {
                    "intent": self.intent_engine is not None,
                    "context": self.context_engine is not None,
                    "reasoning": self.reasoning_engine is not None,
                    "planner": self.planner is not None,
                    "tasks": self.task_engine is not None,
                    "response": self.response_engine is not None,
                    "online_provider": self.online_provider is not None,
                    "offline_provider": self.offline_provider is not None,
                },
            }

    # ------------------------------------------------------------------
    # Input and context
    # ------------------------------------------------------------------

    def _normalize_input(self, user_input: str) -> str:
        if not isinstance(user_input, str):
            raise TypeError("user_input must be a string")

        text = user_input.strip()
        if len(text) > self.max_message_length:
            text = text[: self.max_message_length]
        return text

    def _build_context(
        self, user_input: str, metadata: Mapping[str, Any]
    ) -> dict[str, Any]:
        with self._lock:
            history = [message.to_dict() for message in self._history]

        context: dict[str, Any] = {
            "system_prompt": self.system_prompt,
            "history": history,
            "user_input": user_input,
            "metadata": dict(metadata),
            "language_hint": self._detect_language_hint(user_input),
        }

        if self.context_engine is not None:
            value = self._call_component(
                self.context_engine,
                ("build_context", "get_context", "create_context", "process"),
                user_input,
                history=history,
                metadata=dict(metadata),
            )
            if isinstance(value, Mapping):
                context["external_context"] = dict(value)
            elif value is not None:
                context["external_context"] = value

        return context

    @staticmethod
    def _detect_language_hint(text: str) -> str:
        """Lightweight script hint, not a full language detector."""
        if any("\u0b80" <= char <= "\u0bff" for char in text):
            return "ta"
        return "en"

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def _detect_intent(
        self, text: str, context: Mapping[str, Any]
    ) -> tuple[str, float, dict[str, Any]]:
        if self.intent_engine is not None:
            value = self._call_component(
                self.intent_engine,
                ("detect_intent", "classify", "understand", "process"),
                text,
                context=context,
            )
            parsed = self._parse_intent(value)
            if parsed is not None:
                return parsed

        normalized = text.casefold()
        if any(
            phrase in normalized
            for phrase in ("hello", "hi", "hey", "வணக்கம்", "ஹாய்")
        ):
            return "greeting", 0.72, {"source": "fallback"}

        if any(
            phrase in normalized
            for phrase in (
                "help",
                "what can you do",
                "உதவி",
                "என்ன செய்ய",
            )
        ):
            return "help", 0.70, {"source": "fallback"}

        if any(
            phrase in normalized
            for phrase in (
                "plan",
                "steps",
                "how do i",
                "எப்படி",
                "திட்டம்",
            )
        ):
            return "planning", 0.58, {"source": "fallback"}

        return "conversation", 0.40, {"source": "fallback"}

    @staticmethod
    def _parse_intent(
        value: Any,
    ) -> tuple[str, float, dict[str, Any]] | None:
        if isinstance(value, str) and value.strip():
            return value.strip(), 0.7, {"raw": value}

        if isinstance(value, Mapping):
            intent = value.get("intent") or value.get("name") or value.get(
                "label"
            )
            if not isinstance(intent, str) or not intent.strip():
                return None

            raw_confidence = value.get("confidence", 0.7)
            try:
                confidence = float(raw_confidence)
            except (TypeError, ValueError):
                confidence = 0.7

            confidence = max(0.0, min(1.0, confidence))
            return intent.strip(), confidence, dict(value)

        return None

    @staticmethod
    def _needs_clarification(intent_data: Mapping[str, Any]) -> bool:
        return bool(
            intent_data.get("needs_clarification")
            or intent_data.get("clarification_required")
        )

    @staticmethod
    def _clarification_response(intent_data: Mapping[str, Any]) -> str:
        question = intent_data.get("clarifying_question") or intent_data.get(
            "question"
        )
        if isinstance(question, str) and question.strip():
            return question.strip()
        return "Could you clarify what you want me to do?"

    # ------------------------------------------------------------------
    # Planning and task execution
    # ------------------------------------------------------------------

    def _create_plan(
        self,
        text: str,
        intent: str,
        context: Mapping[str, Any],
        intent_data: Mapping[str, Any],
    ) -> list[str]:
        suggested = intent_data.get("plan") or intent_data.get("steps")
        if isinstance(suggested, Sequence) and not isinstance(
            suggested, (str, bytes)
        ):
            steps = [
                str(step).strip()
                for step in suggested
                if str(step).strip()
            ]
            if steps:
                return steps

        if self.planner is not None:
            value = self._call_component(
                self.planner,
                ("create_plan", "plan", "build_plan", "process"),
                text,
                intent=intent,
                context=context,
            )
            steps = self._extract_steps(value)
            if steps:
                return steps

        if self.reasoning_engine is not None:
            value = self._call_component(
                self.reasoning_engine,
                ("reason", "analyze", "process"),
                text,
                intent=intent,
                context=context,
            )
            steps = self._extract_steps(value)
            if steps:
                return steps

        if intent == "planning":
            return [
                "Clarify the desired outcome and constraints.",
                "Break the goal into manageable steps.",
                "Review dependencies and risks.",
                "Carry out the approved steps and verify the results.",
            ]

        return []

    @staticmethod
    def _extract_steps(value: Any) -> list[str]:
        if isinstance(value, Mapping):
            value = value.get("steps") or value.get("plan") or value.get(
                "actions"
            )

        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes)
        ):
            result: list[str] = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    result.append(item.strip())
                elif isinstance(item, Mapping):
                    description = (
                        item.get("description")
                        or item.get("task")
                        or item.get("action")
                    )
                    if isinstance(description, str) and description.strip():
                        result.append(description.strip())
            return result

        return []

    def _execute_plan(
        self,
        plan: list[str],
        user_input: str,
        intent: str,
        context: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Delegate execution to an explicitly injected task engine.

        No shell command or arbitrary function is executed by this method.
        """
        if self.task_engine is None:
            return [
                {
                    "status": "not_executed",
                    "reason": "No task engine is configured.",
                }
            ]

        value = self._call_component(
            self.task_engine,
            ("execute_plan", "run_plan", "execute", "process"),
            plan,
            user_input=user_input,
            intent=intent,
            context=context,
        )

        if isinstance(value, Mapping):
            return [dict(value)]
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes)
        ):
            return [
                dict(item) if isinstance(item, Mapping) else {"result": item}
                for item in value
            ]
        if value is None:
            return []
        return [{"result": value}]

    # ------------------------------------------------------------------
    # Response generation
    # ------------------------------------------------------------------

    def _generate_response(
        self,
        *,
        text: str,
        intent: str,
        context: Mapping[str, Any],
        plan: list[str],
        task_results: list[dict[str, Any]],
        intent_data: Mapping[str, Any],
    ) -> tuple[str, str]:
        if self.response_engine is not None:
            value = self._call_component(
                self.response_engine,
                ("generate_response", "respond", "generate", "process"),
                text,
                intent=intent,
                context=context,
                plan=plan,
                task_results=task_results,
                intent_data=intent_data,
            )
            response = self._extract_response(value)
            if response:
                return response, "response_engine"

        provider_response = self._try_providers(
            text=text,
            intent=intent,
            context=context,
            plan=plan,
            task_results=task_results,
        )
        if provider_response is not None:
            return provider_response, "provider"

        return (
            self._local_response(
                text=text,
                intent=intent,
                plan=plan,
                task_results=task_results,
            ),
            "local",
        )

    def _try_providers(
        self,
        *,
        text: str,
        intent: str,
        context: Mapping[str, Any],
        plan: list[str],
        task_results: list[dict[str, Any]],
    ) -> str | None:
        """
        Try configured providers in privacy-conscious order.

        Online use requires an injected provider and explicit opt-in via
        PAT_ALLOW_ONLINE_AI=true. Provider implementations must handle their
        own credentials, network timeouts, and data disclosure.
        """
        providers: list[Any] = []

        offline_enabled = os.getenv("PAT_ENABLE_OFFLINE_AI", "true").casefold()
        if self.offline_provider is not None and offline_enabled not in {
            "0",
            "false",
            "no",
        }:
            providers.append(self.offline_provider)

        online_enabled = os.getenv("PAT_ALLOW_ONLINE_AI", "false").casefold()
        if self.online_provider is not None and online_enabled in {
            "1",
            "true",
            "yes",
        }:
            providers.append(self.online_provider)

        for provider in providers:
            try:
                value = self._call_component(
                    provider,
                    ("generate", "generate_response", "chat", "complete"),
                    text,
                    system_prompt=self.system_prompt,
                    context=context,
                    intent=intent,
                    plan=plan,
                    task_results=task_results,
                )
                response = self._extract_response(value)
                if response:
                    return response
            except Exception:
                logger.warning(
                    "Configured AI provider failed; trying fallback.",
                    exc_info=True,
                )

        return None

    @staticmethod
    def _extract_response(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()

        if isinstance(value, Mapping):
            for key in ("response", "text", "content", "answer", "message"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()

        return None

    @staticmethod
    def _local_response(
        *,
        text: str,
        intent: str,
        plan: list[str],
        task_results: list[dict[str, Any]],
    ) -> str:
        if intent == "greeting":
            return "Hey bro! I'm P.A.T. What are we working on today?"

        if intent == "help":
            return (
                "I'm P.A.T. I can help with conversation, planning, coding, "
                "and tasks supported by the tools connected to me. Tell me "
                "your goal, and we'll work through it step by step."
            )

        if task_results:
            completed = any(
                str(item.get("status", "")).casefold()
                in {"completed", "success", "succeeded"}
                for item in task_results
            )
            if completed:
                return (
                    "The task engine reported a completed action. "
                    "Let's review its result to confirm what changed."
                )
            return (
                "I've received the task engine's result, but I can't confirm "
                "that the requested action succeeded. Let's inspect the details."
            )

        if plan:
            formatted_plan = "\n".join(
                f"{index}. {step}"
                for index, step in enumerate(plan, start=1)
            )
            return (
                "Here's a practical plan:\n"
                f"{formatted_plan}\n"
                "We can refine the steps based on your requirements."
            )

        return (
            "I understand your message. I can help work through it, but my "
            "advanced language-model provider isn't configured right now. "
            "Tell me a little more about the outcome you want."
        )

    @staticmethod
    def _fallback_response(text: str) -> str:
        del text
        return (
            "I hit an internal AI error while processing that message. "
            "Your request wasn't confirmed as completed. Please try again "
            "or check the application logs."
        )

    # ------------------------------------------------------------------
    # Component compatibility helper
    # ------------------------------------------------------------------

    @staticmethod
    def _call_component(
        component: Any,
        method_names: tuple[str, ...],
        primary_argument: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Invoke the first supported method on an injected component.

        The helper first passes context keywords. If the component's method
        signature does not accept those keywords, it retries with only the
        primary positional argument.
        """
        method: Callable[..., Any] | None = None

        for method_name in method_names:
            candidate = getattr(component, method_name, None)
            if callable(candidate):
                method = candidate
                break

        if method is None and callable(component):
            method = component

        if method is None:
            return None

        try:
            return method(primary_argument, **kwargs)
        except TypeError:
            # Supports older component APIs that accept only one argument.
            # If the method raises TypeError internally, this fallback may
            # call it again; component adapters should use stable signatures.
            return method(primary_argument)
