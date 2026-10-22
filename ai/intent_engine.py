
"""
P.A.T Advanced Intent Engine
============================

Identifies user intent, task category, entities, and clarification needs.

Design:
- Tamil, English, and Tanglish-friendly phrase recognition.
- Rule-based local classification with confidence scores.
- Context-aware follow-up hints.
- Extensible intent registry.
- Structured output compatible with AIEngine.
- No network access, model downloads, or task execution.

This is a local intent classifier, not a substitute for a trained LLM.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class IntentResult:
    """Structured result from intent classification."""

    intent: str
    confidence: float
    category: str = "conversation"
    entities: dict[str, Any] = field(default_factory=dict)
    needs_clarification: bool = False
    clarifying_question: str | None = None
    plan: list[str] = field(default_factory=list)
    source: str = "local_rules"
    alternatives: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IntentEngine:
    """Thread-safe, extensible intent classification for P.A.T."""

    def __init__(
        self,
        *,
        confidence_threshold: float = 0.40,
        custom_intents: Mapping[str, list[str]] | None = None,
    ) -> None:
        self.confidence_threshold = max(
            0.0, min(1.0, float(confidence_threshold))
        )
        self._lock = threading.RLock()

        self._patterns: dict[str, tuple[str, ...]] = {
            "greeting": (
                "hello", "hi", "hey", "good morning", "good evening",
                "vanakkam", "வணக்கம்", "ஹாய்", "ஹலோ",
            ),
            "farewell": (
                "bye", "goodbye", "see you", "take care",
                "poitu varen", "போயிட்டு வரேன்",
            ),
            "help": (
                "help me", "need help", "what can you do",
                "உதவி", "enna panna mudiyum",
            ),
            "question": (
                "what is", "who is", "where is", "when is", "why",
                "explain", "meaning", "enna artham", "enna meaning",
                "என்ன", "யார்", "எங்கே", "ஏன்", "விளக்கு",
            ),
            "planning": (
                "make a plan", "create a plan", "roadmap",
                "step by step", "how do i", "how to",
                "plan pannu", "eppadi", "திட்டம்", "எப்படி",
            ),
            "coding": (
                "write code", "fix this code", "debug",
                "python code", "program", "function", "class ",
                "full replacement code", "code kudu", "code thaa",
                "கோடு எழுது",
            ),
            "file_operation": (
                "open file", "read file", "find file", "copy file",
                "move file", "rename file", "delete file",
                "file open", "folder", "கோப்பு",
            ),
            "browser_search": (
                "search web", "search google", "search online",
                "look up online", "find on internet", "browse web",
                "google la search", "internet la thedu",
            ),
            "download": (
                "download", "save this file", "get this file",
                "download pannu", "download kudu",
            ),
            "app_control": (
                "open app", "launch app", "close app", "start application",
                "open calculator", "open notepad",
                "app open pannu",
            ),
            "system_info": (
                "system information", "computer specs", "cpu usage",
                "memory usage", "disk space", "battery status",
                "system status", "pc status",
            ),
            "time_date": (
                "what time", "current time", "today's date",
                "what date", "neram enna", "mani enna",
                "இப்போது மணி", "இன்றைய தேதி",
            ),
            "calculation": (
                "calculate", "what is the sum", "multiply",
                "divide", "percentage", "calculator",
                "kanakku pannu", "கணக்கிடு",
            ),
            "memory_recall": (
                "remember", "do you remember", "what did i say",
                "recall", "last time", "munnadi sonnen",
                "nyabagam irukka", "நினைவிருக்கிறதா",
            ),
            "memory_store": (
                "remember that", "save this preference",
                "store this", "keep this in memory",
                "idha nyabagam vechuko", "நினைவில் வை",
            ),
            "security_check": (
                "security scan", "check for threats", "suspicious process",
                "network activity", "security report", "threat detection",
                "security check pannu",
            ),
            "automation": (
                "automate", "repeat these steps", "workflow",
                "do this automatically", "teach me once",
                "automatic ah pannu",
            ),
            "task_status": (
                "task status", "progress report", "what is pending",
                "what is completed", "status sollu",
            ),
            "confirmation": (
                "yes", "confirm", "approved", "proceed",
                "aama", "seri pannu", "ஆம்", "சரி",
            ),
            "cancellation": (
                "cancel", "stop", "abort", "don't do that",
                "vendam", "niruthu", "வேண்டாம்", "நிறுத்து",
            ),
            "complaint": (
                "that is wrong", "not working", "you made a mistake",
                "incorrect", "doesn't work", "thappu",
                "work aagala", "தவறு",
            ),
        }

        if custom_intents:
            for name, phrases in custom_intents.items():
                key = str(name).strip().casefold()
                if key and isinstance(phrases, list):
                    normalized = tuple(
                        str(phrase).strip().casefold()
                        for phrase in phrases
                        if str(phrase).strip()
                    )
                    if normalized:
                        self._patterns[key] = normalized

        self._category_map: dict[str, str] = {
            "greeting": "conversation",
            "farewell": "conversation",
            "help": "conversation",
            "question": "information",
            "planning": "planning",
            "coding": "development",
            "file_operation": "computer_control",
            "browser_search": "web",
            "download": "web",
            "app_control": "computer_control",
            "system_info": "system",
            "time_date": "information",
            "calculation": "utility",
            "memory_recall": "memory",
            "memory_store": "memory",
            "security_check": "security",
            "automation": "automation",
            "task_status": "task_management",
            "confirmation": "conversation_control",
            "cancellation": "conversation_control",
            "complaint": "feedback",
        }

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def detect_intent(
        self,
        text: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Classify text and return a dictionary for AIEngine compatibility."""
        result = self.classify(text, context=context)
        return result.to_dict()

    def classify(
        self,
        text: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> IntentResult:
        if not isinstance(text, str):
            raise TypeError("Intent input must be a string")

        original = text.strip()
        if not original:
            return IntentResult(
                intent="unknown",
                confidence=0.0,
                needs_clarification=True,
                clarifying_question="What would you like me to help with?",
            )

        normalized = self._normalize(original)
        context = context or {}

        # Explicit cancellation takes precedence over other detected intents.
        if self._matches(normalized, self._patterns["cancellation"]):
            return IntentResult(
                intent="cancellation",
                confidence=0.98,
                category="conversation_control",
            )

        # Confirmation is meaningful only if the conversation has a pending
        # action or clarification; otherwise, "yes" is ambiguous.
        if self._is_confirmation(normalized):
            pending = self._has_pending_action(context)
            return IntentResult(
                intent="confirmation" if pending else "conversation",
                confidence=0.92 if pending else 0.50,
                category="conversation_control" if pending else "conversation",
                needs_clarification=not pending,
                clarifying_question=(
                    None if pending else
                    "What would you like me to confirm?"
                ),
            )

        scores: list[tuple[str, float, list[str]]] = []

        with self._lock:
            patterns = dict(self._patterns)

        for intent_name, phrases in patterns.items():
            if intent_name in {"confirmation", "cancellation"}:
                continue

            matches = [
                phrase for phrase in phrases
                if self._phrase_matches(normalized, phrase)
            ]
            if matches:
                # Prefer precise and multiword matches.
                best_match = max(
                    matches,
                    key=lambda phrase: (
                        len(phrase.split()),
                        len(phrase),
                    ),
                )
                score = min(
                    0.97,
                    0.58 + min(len(best_match) / 100, 0.20)
                    + (0.08 if len(best_match.split()) > 1 else 0.0),
                )
                scores.append((intent_name, score, matches))

        if not scores:
            follow_up = self._is_follow_up(original, context)
            return IntentResult(
                intent="conversation",
                confidence=0.42 if follow_up else 0.30,
                category="conversation",
                entities=self._extract_entities(original),
                needs_clarification=False,
                source="context_rules" if follow_up else "local_rules",
            )

        scores.sort(key=lambda item: item[1], reverse=True)
        best_intent, confidence, matched_phrases = scores[0]

        # Overlapping rules may indicate a multi-purpose request.
        alternatives = [
            {"intent": name, "confidence": score}
            for name, score, _ in scores[1:4]
        ]

        needs_clarification = self._needs_more_detail(
            best_intent, original, matched_phrases
        )

        question = None
        if needs_clarification:
            question = self._clarification_question(best_intent)

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            category=self._category_map.get(best_intent, "general"),
            entities=self._extract_entities(original),
            needs_clarification=needs_clarification,
            clarifying_question=question,
            source="local_rules",
            alternatives=alternatives,
        )

    def register_intent(
        self,
        name: str,
        phrases: list[str],
        *,
        category: str = "custom",
    ) -> None:
        """Register or replace an intent without restarting P.A.T."""
        normalized_name = str(name).strip().casefold()
        normalized_phrases = tuple(
            str(phrase).strip().casefold()
            for phrase in phrases
            if str(phrase).strip()
        )

        if not normalized_name:
            raise ValueError("Intent name cannot be empty")
        if not normalized_phrases:
            raise ValueError("At least one intent phrase is required")

        with self._lock:
            self._patterns[normalized_name] = normalized_phrases
            self._category_map[normalized_name] = str(category).strip()

    def get_supported_intents(self) -> list[str]:
        with self._lock:
            return sorted(self._patterns)

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "engine": "P.A.T Intent Engine",
                "mode": "local_rules",
                "intent_count": len(self._patterns),
                "confidence_threshold": self.confidence_threshold,
                "intents": sorted(self._patterns),
            }

    # ---------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.casefold().strip()
        text = re.sub(r"\s+", " ", text)
        return text.strip(" \t\r\n.!?,")

    @staticmethod
    def _phrase_matches(text: str, phrase: str) -> bool:
        phrase = phrase.casefold().strip()
        if not phrase:
            return False

        # Multiword and non-Latin phrases use substring matching. For a
        # single Latin word, boundaries avoid matching inside another word.
        if " " in phrase or any(ord(char) > 127 for char in phrase):
            return phrase in text

        return re.search(
            rf"(?<!\w){re.escape(phrase)}(?!\w)",
            text,
            flags=re.UNICODE,
        ) is not None

    @classmethod
    def _matches(cls, text: str, phrases: tuple[str, ...]) -> bool:
        return any(cls._phrase_matches(text, phrase) for phrase in phrases)

    @staticmethod
    def _is_confirmation(text: str) -> bool:
        return text in {
            "yes", "yes please", "confirm", "approved", "proceed",
            "aama", "seri pannu", "ஆம்", "சரி",
        }

    @staticmethod
    def _has_pending_action(context: Mapping[str, Any]) -> bool:
        if context.get("pending_action") or context.get("pending_confirmation"):
            return True

        follow_up = context.get("follow_up")
        if isinstance(follow_up, Mapping):
            return bool(follow_up.get("pending_action"))

        return False

    @classmethod
    def _is_follow_up(
        cls,
        text: str,
        context: Mapping[str, Any],
    ) -> bool:
        normalized = cls._normalize(text)
        history = context.get("history") or context.get("recent_history")
        has_history = isinstance(history, (list, tuple)) and bool(history)

        if not has_history:
            return False

        phrases = (
            "continue", "what next", "do that", "same one",
            "tell me more", "explain more", "அடுத்து", "தொடரு",
            "அதை", "அதுக்கு",
        )
        return any(phrase in normalized for phrase in phrases)

    @staticmethod
    def _extract_entities(text: str) -> dict[str, Any]:
        """Extract lightweight hints; these are not verified entities."""
        paths = re.findall(
            r"""(?:"([^"]+\.[A-Za-z0-9]{1,8})"|'([^']+\.[A-Za-z0-9]{1,8})')""",
            text,
        )
        file_paths = [
            first or second for first, second in paths if first or second
        ]

        urls = re.findall(r"https?://[^\s<>\"']+", text)
        quoted = re.findall(r'"([^"]{1,200})"|\'([^\']{1,200})\'', text)
        quoted_phrases = [
            first or second
            for first, second in quoted
            if first or second
        ]

        return {
            "file_paths": file_paths,
            "urls": urls,
            "quoted_phrases": quoted_phrases,
        }

    @staticmethod
    def _needs_more_detail(
        intent: str,
        text: str,
        matches: list[str],
    ) -> bool:
        if intent in {"file_operation", "download", "app_control"}:
            generic_only = all(
                phrase in {"folder", "download", "open file", "file open"}
                for phrase in matches
            )
            return generic_only and len(text.split()) <= 4

        if intent == "automation" and len(text.split()) <= 3:
            return True

        return intent == "planning" and len(text.split()) <= 2

    @staticmethod
    def _clarification_question(intent: str) -> str:
        questions = {
            "file_operation": "Which file or folder should I work with, and what should I do?",
            "download": "What file or link would you like to download?",
            "app_control": "Which application should I open or control?",
            "automation": "Which workflow would you like me to automate?",
            "planning": "What goal should I create a step-by-step plan for?",
        }
        return questions.get(
            intent,
            "Could you share a little more detail about what you want?",
        )


# Compatibility aliases for integrations that use alternate class names.
IntentClassifier = IntentEngine

__all__ = [
    "IntentClassifier",
    "IntentEngine",
    "IntentResult",
]
