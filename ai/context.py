
"""
P.A.T Advanced Conversation Context Manager
===========================================

Responsibilities:
- Maintain bounded, timestamped conversation history.
- Track the active topic and recent entities.
- Resolve simple follow-up references from conversation context.
- Store session-scoped preferences and facts.
- Build context snapshots for the AI reasoning and response engines.
- Support import/export of session context.
- Protect shared state with a re-entrant lock.
- Avoid external dependencies and persistent storage by default.

This module manages short-term session context. It does not replace the
separate long-term memory subsystem.
"""

from __future__ import annotations

import json
import re
import threading
import time
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ContextMessage:
    """One normalized message in the conversation."""

    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConversationContext:
    """
    Thread-safe conversation context for a single P.A.T session.

    Typical use:
        context = ConversationContext()
        context.add_message("user", "Help me build an AI assistant")
        context.set_topic("AI assistant development")
        snapshot = context.get_context("What should I do next?")
    """

    DEFAULT_MAX_MESSAGES = 40
    DEFAULT_MAX_MESSAGE_LENGTH = 12_000
    DEFAULT_MAX_FACTS = 200

    FOLLOW_UP_PHRASES = (
        "it",
        "that",
        "this",
        "them",
        "those",
        "the same",
        "continue",
        "what next",
        "next step",
        "do it",
        "explain more",
        "tell me more",
        "அது",
        "இத",
        "அதை",
        "அதுக்கு",
        "தொடரு",
        "அடுத்து",
        "மேலும்",
    )

    def __init__(
        self,
        max_messages: int = DEFAULT_MAX_MESSAGES,
        max_message_length: int = DEFAULT_MAX_MESSAGE_LENGTH,
        max_facts: int = DEFAULT_MAX_FACTS,
        session_id: str | None = None,
    ) -> None:
        self.max_messages = max(2, int(max_messages))
        self.max_message_length = max(100, int(max_message_length))
        self.max_facts = max(1, int(max_facts))
        self.session_id = session_id

        self._messages: deque[ContextMessage] = deque(
            maxlen=self.max_messages
        )
        self._facts: dict[str, Any] = {}
        self._preferences: dict[str, Any] = {}
        self._entities: deque[str] = deque(maxlen=50)
        self._topic: str | None = None
        self._lock = threading.RLock()

    # ---------------------------------------------------------------
    # Conversation history
    # ---------------------------------------------------------------

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a user, assistant, or system message to session history."""
        normalized_role = str(role).strip().casefold()
        normalized_content = self._validate_content(content)

        if normalized_role not in {"user", "assistant", "system", "tool"}:
            raise ValueError(
                "role must be user, assistant, system, or tool"
            )

        message = ContextMessage(
            role=normalized_role,
            content=normalized_content,
            metadata=dict(metadata or {}),
        )

        with self._lock:
            self._messages.append(message)
            self._extract_entities(normalized_content)

        return message.to_dict()

    def add_user_message(
        self,
        content: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.add_message("user", content, metadata)

    def add_assistant_message(
        self,
        content: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.add_message("assistant", content, metadata)

    def get_history(
        self,
        limit: int | None = None,
        role: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return a copy of recent messages, optionally filtered."""
        with self._lock:
            messages = list(self._messages)

        if role is not None:
            normalized_role = str(role).strip().casefold()
            messages = [
                message
                for message in messages
                if message.role == normalized_role
            ]

        if limit is not None:
            messages = messages[-max(0, int(limit)):] if limit > 0 else []

        return [message.to_dict() for message in messages]

    def clear_history(self) -> None:
        """Clear messages without deleting stored facts or preferences."""
        with self._lock:
            self._messages.clear()
            self._entities.clear()
            self._topic = None

    def clear_session(self) -> None:
        """Clear all session-scoped context data."""
        with self._lock:
            self._messages.clear()
            self._facts.clear()
            self._preferences.clear()
            self._entities.clear()
            self._topic = None

    # ---------------------------------------------------------------
    # Topic and entity tracking
    # ---------------------------------------------------------------

    def set_topic(self, topic: str | None) -> None:
        normalized = str(topic).strip() if topic is not None else ""
        with self._lock:
            self._topic = normalized or None

    def get_topic(self) -> str | None:
        with self._lock:
            return self._topic

    def add_entity(self, entity: str) -> None:
        normalized = str(entity).strip()
        if not normalized:
            return

        with self._lock:
            if normalized.casefold() not in {
                item.casefold() for item in self._entities
            }:
                self._entities.append(normalized)

    def get_recent_entities(self, limit: int = 10) -> list[str]:
        with self._lock:
            return list(self._entities)[-max(0, int(limit)):]

    def _extract_entities(self, text: str) -> None:
        """
        Lightweight entity hints, not full named-entity recognition.

        Proper-name detection is deliberately conservative and should not be
        treated as a verified fact.
        """
        candidates = re.findall(
            r"\b[A-Z][a-zA-Z0-9_-]{2,}(?:\s+[A-Z][a-zA-Z0-9_-]{2,}){0,2}\b",
            text,
        )

        existing = {item.casefold() for item in self._entities}
        for candidate in candidates:
            if candidate.casefold() not in existing:
                self._entities.append(candidate)
                existing.add(candidate.casefold())

    # ---------------------------------------------------------------
    # Session facts and preferences
    # ---------------------------------------------------------------

    def set_fact(self, key: str, value: Any) -> None:
        """Store a session fact. Values must be JSON-serializable."""
        normalized_key = str(key).strip()
        if not normalized_key:
            raise ValueError("Fact key cannot be empty")

        # Validate serializability before mutating state.
        json.dumps(value, ensure_ascii=False)

        with self._lock:
            if (
                normalized_key not in self._facts
                and len(self._facts) >= self.max_facts
            ):
                oldest_key = next(iter(self._facts))
                del self._facts[oldest_key]

            self._facts[normalized_key] = value

    def get_fact(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._facts.get(str(key).strip(), default)

    def remove_fact(self, key: str) -> bool:
        with self._lock:
            return self._facts.pop(str(key).strip(), None) is not None

    def set_preference(self, key: str, value: Any) -> None:
        normalized_key = str(key).strip()
        if not normalized_key:
            raise ValueError("Preference key cannot be empty")

        json.dumps(value, ensure_ascii=False)

        with self._lock:
            self._preferences[normalized_key] = value

    def get_preference(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._preferences.get(str(key).strip(), default)

    def get_preferences(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._preferences)

    # ---------------------------------------------------------------
    # Context building and follow-up handling
    # ---------------------------------------------------------------

    def is_follow_up(self, user_input: str) -> bool:
        """Estimate whether the message refers to recent conversation."""
        text = str(user_input).strip().casefold()
        if not text:
            return False

        with self._lock:
            has_history = bool(self._messages)

        if not has_history:
            return False

        if any(phrase in text for phrase in self.FOLLOW_UP_PHRASES):
            return True

        words = text.split()
        return len(words) <= 4 and text.endswith(("?", "…"))

    def resolve_follow_up(self, user_input: str) -> dict[str, Any]:
        """
        Return contextual clues for a possible follow-up.

        This does not rewrite the user's message or claim that a reference
        has been resolved with certainty.
        """
        with self._lock:
            recent_messages = list(self._messages)[-8:]
            topic = self._topic
            entities = list(self._entities)[-10:]

        return {
            "original_input": str(user_input).strip(),
            "is_follow_up": self.is_follow_up(user_input),
            "active_topic": topic,
            "recent_entities": entities,
            "recent_history": [
                message.to_dict() for message in recent_messages
            ],
            "resolution_confidence": (
                0.65 if topic or recent_messages else 0.0
            ),
        }

    def get_context(self, user_input: str | None = None) -> dict[str, Any]:
        """Build a snapshot suitable for the reasoning or response engine."""
        with self._lock:
            messages = [message.to_dict() for message in self._messages]
            topic = self._topic
            facts = dict(self._facts)
            preferences = dict(self._preferences)
            entities = list(self._entities)[-10:]

        result: dict[str, Any] = {
            "session_id": self.session_id,
            "active_topic": topic,
            "history": messages,
            "facts": facts,
            "preferences": preferences,
            "recent_entities": entities,
            "message_count": len(messages),
        }

        if user_input is not None:
            result["follow_up"] = self.resolve_follow_up(user_input)

        return result

    def build_context(
        self,
        user_input: str,
        history: Sequence[Mapping[str, Any]] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Adapter for AIEngine._build_context().

        Supplied history is included as a snapshot; this method does not add
        the same messages again, avoiding duplicate history entries.
        """
        context = self.get_context(user_input)
        if history is not None:
            context["engine_history"] = [dict(item) for item in history]
        if metadata is not None:
            context["request_metadata"] = dict(metadata)
        return context

    # ---------------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------------

    def export_session(self) -> dict[str, Any]:
        """Export session context as a JSON-compatible dictionary."""
        with self._lock:
            return {
                "schema_version": 1,
                "session_id": self.session_id,
                "max_messages": self.max_messages,
                "max_message_length": self.max_message_length,
                "max_facts": self.max_facts,
                "messages": [
                    message.to_dict() for message in self._messages
                ],
                "facts": dict(self._facts),
                "preferences": dict(self._preferences),
                "entities": list(self._entities),
                "topic": self._topic,
            }

    def import_session(self, payload: Mapping[str, Any]) -> None:
        """
        Replace session state from a validated export dictionary.

        Only JSON-compatible data is accepted. The caller is responsible for
        ensuring imported data comes from a trusted source.
        """
        if not isinstance(payload, Mapping):
            raise TypeError("Session payload must be a mapping")

        raw_messages = payload.get("messages", [])
        raw_facts = payload.get("facts", {})
        raw_preferences = payload.get("preferences", {})
        raw_entities = payload.get("entities", [])
        raw_topic = payload.get("topic")

        if not isinstance(raw_messages, list):
            raise TypeError("'messages' must be a list")
        if not isinstance(raw_facts, Mapping):
            raise TypeError("'facts' must be a mapping")
        if not isinstance(raw_preferences, Mapping):
            raise TypeError("'preferences' must be a mapping")
        if not isinstance(raw_entities, list):
            raise TypeError("'entities' must be a list")

        new_messages: list[ContextMessage] = []
        for item in raw_messages[-self.max_messages:]:
            if not isinstance(item, Mapping):
                continue

            role = str(item.get("role", "")).strip().casefold()
            content = item.get("content", "")
            if role not in {"user", "assistant", "system", "tool"}:
                continue
            if not isinstance(content, str):
                continue

            try:
                timestamp = float(item.get("timestamp", time.time()))
            except (TypeError, ValueError):
                timestamp = time.time()

            metadata = item.get("metadata", {})
            if not isinstance(metadata, Mapping):
                metadata = {}

            new_messages.append(
                ContextMessage(
                    role=role,
                    content=self._validate_content(content),
                    timestamp=timestamp,
                    metadata=dict(metadata),
                )
            )

        new_facts = dict(list(raw_facts.items())[-self.max_facts:])
        new_preferences = dict(raw_preferences)
        new_entities = [
            str(item).strip()
            for item in raw_entities
            if str(item).strip()
        ][-50:]

        json.dumps(
            {
                "facts": new_facts,
                "preferences": new_preferences,
                "entities": new_entities,
                "topic": raw_topic,
            },
            ensure_ascii=False,
        )

        with self._lock:
            self._messages.clear()
            self._messages.extend(new_messages)
            self._facts = new_facts
            self._preferences = new_preferences
            self._entities.clear()
            self._entities.extend(new_entities)
            self._topic = (
                str(raw_topic).strip()
                if isinstance(raw_topic, str) and raw_topic.strip()
                else None
            )
            imported_session_id = payload.get("session_id")
            if isinstance(imported_session_id, str):
                self.session_id = imported_session_id

    # ---------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------

    def _validate_content(self, content: str) -> str:
        if not isinstance(content, str):
            raise TypeError("Message content must be a string")
        return content.strip()[: self.max_message_length]

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "session_id": self.session_id,
                "messages": len(self._messages),
                "max_messages": self.max_messages,
                "facts": len(self._facts),
                "preferences": len(self._preferences),
                "entities": len(self._entities),
                "active_topic": self._topic,
            }


# Compatibility aliases for code that expects a shorter class name.
ContextManager = ConversationContext
Context = ConversationContext

__all__ = [
    "Context",
    "ContextManager",
    "ContextMessage",
    "ConversationContext",
]
