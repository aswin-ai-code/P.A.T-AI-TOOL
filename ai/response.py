
"""
P.A.T Advanced Response Engine
------------------------------
Generates natural, context-aware assistant responses.

Local-first by default. An optional provider can be injected for
model-generated responses. This module does not execute tools or
claim that an action succeeded without a verified result.
"""

from __future__ import annotations

import random
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


@dataclass(slots=True)
class ResponseResult:
    """Structured response returned by ResponseEngine."""

    text: str
    intent: str = "general"
    language: str = "en"
    tone: str = "friendly"
    needs_follow_up: bool = False
    follow_up_question: str | None = None
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResponseEngine:
    """
    P.A.T conversational response generator.

    Public methods:
        generate(...)
        create_response(...)
        respond(...)
        format_response(...)
        get_status()

    This engine uses local templates when no provider is configured.
    """

    LANGUAGE_MARKERS: ClassVar[dict[str, tuple[str, ...]]] = {
        "ta": (
            "வணக்கம்", "என்ன", "வேண்டும்", "சொல்லு", "செய்",
            "நன்றி", "இல்லை", "எப்படி", "நேரம்", "உதவி",
        ),
        "tanglish": (
            "bro", "enna", "epdi", "sollu", "pannu", "venum",
            "illa", "seri", "iruku", "irukku", "panrom",
            "mudiyum", "theriyum", "paaru",
        ),
    }

    GREETINGS: ClassVar[tuple[str, ...]] = (
        "Hey bro! 😎 Sollu, enna plan?",
        "Hey! P.A.T online. Enna help venum?",
        "Vanakkam bro! Ready—enna pannalaam?",
        "Hey bro! Namma next mission enna?",
    )

    FAREWELLS: ClassVar[tuple[str, ...]] = (
        "Seri bro, appuram pesalaam! 👋",
        "Bye bro! Take care. Next mission-ku ready-ah irukken.",
        "See you bro! Un work smooth-ah pogattum. 😎",
    )

    HUMOR: ClassVar[tuple[str, ...]] = (
        "Plan ready bro. Ippo namma chaos-ah konjam organize pannuvom. 😎",
        "Mission possible, bro. Aana first details clear pannidalaam.",
        "Brainstorming mode on. Coffee optional; bugs mandatory-nu illa. 😄",
        "Namma smart-ah handle pannuvom—guess panni system-ah disturb panna vendaam.",
    )

    INTENT_TEMPLATES: ClassVar[dict[str, tuple[str, ...]]] = {
        "help": (
            "Sollu bro, enna help venum? Goal-ah sonna step-by-step guide panren.",
            "I'm here to help. Tell me the goal, and we'll work through it together.",
        ),
        "coding": (
            "Seri bro, coding task-ah requirements, existing structure, compatibility-nu break panni handle pannalaam.",
            "Let's handle the coding task carefully, preserving the existing interfaces and behavior.",
        ),
        "planning": (
            "Namma goal, budget, timeline, dependencies ellathayum consider panni practical plan podalaam.",
            "Let's turn the goal into practical milestones, with dependencies and risks made clear.",
        ),
        "question": (
            "Good question bro. Available information base panni clear-ah explain panren.",
            "Let's break that question down and separate confirmed facts from uncertainty.",
        ),
        "calculation": (
            "Calculation-ah clear steps-oda paakkalaam bro.",
            "I'll work through the calculation and make the assumptions clear.",
        ),
        "memory_recall": (
            "Available conversation context-la relevant details irukka-nu paathu answer panren bro.",
            "I'll use the relevant context available to me and be clear if a detail isn't available.",
        ),
        "security_check": (
            "Seri bro, authorized scope-kulla defensive-ah inspect panni findings and limitations explain pannalaam.",
            "Let's keep the assessment authorized, evidence-based, and focused on defensive outcomes.",
        ),
        "file_operation": (
            "File operation-na exact target and effect verify pannitu proceed panna vendum bro.",
            "Let's identify the exact file target and verify the consequences before changing anything.",
        ),
        "browser_search": (
            "Seri bro, relevant sources-la search panni useful details compare pannalaam.",
            "I'll look for relevant sources and distinguish reliable information from uncertain claims.",
        ),
        "automation": (
            "Automation-ku trigger, action, permissions, failure handling ellam define pannalaam bro.",
            "Let's define the trigger, action, permissions, and recovery behavior before enabling automation.",
        ),
    }

    def __init__(
        self,
        provider: Any | None = None,
        *,
        default_language: str = "tanglish",
        default_tone: str = "friendly",
        humor_enabled: bool = True,
        max_response_chars: int = 6000,
    ) -> None:
        self.provider = provider
        self.default_language = self._normalize_language(default_language)
        self.default_tone = self._normalize_tone(default_tone)
        self.humor_enabled = bool(humor_enabled)
        self.max_response_chars = max(200, int(max_response_chars))
        self._last_result: ResponseResult | None = None

    def generate(
        self,
        user_input: str,
        *,
        intent: str = "general",
        context: Any = None,
        reasoning: Any = None,
        task_result: Any = None,
        language: str | None = None,
        tone: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        """
        Generate a natural-language response.

        Returns a string for compatibility with orchestration engines.
        Use generate_result() when structured metadata is required.
        """
        result = self.generate_result(
            user_input,
            intent=intent,
            context=context,
            reasoning=reasoning,
            task_result=task_result,
            language=language,
            tone=tone,
            metadata=metadata,
        )
        return result.text

    def generate_result(
        self,
        user_input: str,
        *,
        intent: str = "general",
        context: Any = None,
        reasoning: Any = None,
        task_result: Any = None,
        language: str | None = None,
        tone: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ResponseResult:
        """Generate a response and return structured response metadata."""
        text = self._normalize_text(user_input)
        intent_name = self._normalize_intent(intent)
        selected_language = self._normalize_language(language) if language else (
            self._detect_language(text) or self.default_language
        )
        selected_tone = self._normalize_tone(tone) if tone else self.default_tone
        meta = dict(metadata or {})

        response = self._try_provider(
            user_input=text,
            intent=intent_name,
            context=context,
            reasoning=reasoning,
            task_result=task_result,
            language=selected_language,
            tone=selected_tone,
        )

        if not response:
            response = self._generate_local(
                text=text,
                intent=intent_name,
                context=context,
                reasoning=reasoning,
                task_result=task_result,
                language=selected_language,
                tone=selected_tone,
            )

        response = self._sanitize_response(response)
        follow_up = self._get_follow_up(
            text=text,
            intent=intent_name,
            reasoning=reasoning,
            task_result=task_result,
        )

        result = ResponseResult(
            text=response,
            intent=intent_name,
            language=selected_language,
            tone=selected_tone,
            needs_follow_up=follow_up is not None,
            follow_up_question=follow_up,
            confidence=self._response_confidence(
                text=text,
                intent=intent_name,
                reasoning=reasoning,
                task_result=task_result,
            ),
            metadata={
                **meta,
                "provider_available": self.provider is not None,
                "response_mode": (
                    "provider-assisted"
                    if self.provider is not None
                    else "local-template"
                ),
            },
        )
        self._last_result = result
        return result

    def create_response(self, *args: Any, **kwargs: Any) -> str:
        """Compatibility alias for existing integrations."""
        return self.generate(*args, **kwargs)

    def respond(self, *args: Any, **kwargs: Any) -> str:
        """Compatibility alias for existing integrations."""
        return self.generate(*args, **kwargs)

    def format_response(
        self,
        text: str,
        *,
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> str:
        """Normalize spacing and optionally add a prefix or suffix."""
        content = self._sanitize_response(text)
        if prefix:
            content = f"{prefix.strip()} {content}".strip()
        if suffix:
            content = f"{content} {suffix.strip()}".strip()
        return content[: self.max_response_chars]

    def get_last_result(self) -> dict[str, Any] | None:
        return self._last_result.to_dict() if self._last_result else None

    def get_status(self) -> dict[str, Any]:
        return {
            "engine": self.__class__.__name__,
            "mode": "provider-assisted" if self.provider is not None else "local-template",
            "provider_available": self.provider is not None,
            "default_language": self.default_language,
            "default_tone": self.default_tone,
            "humor_enabled": self.humor_enabled,
            "has_previous_response": self._last_result is not None,
        }

    def _generate_local(
        self,
        *,
        text: str,
        intent: str,
        context: Any,
        reasoning: Any,
        task_result: Any,
        language: str,
        tone: str,
    ) -> str:
        status_response = self._respond_to_task_result(
            task_result=task_result,
            language=language,
        )
        if status_response:
            return status_response

        if self._requires_clarification(reasoning):
            question = self._value(reasoning, "clarification_question")
            if question:
                return str(question)
            return self._clarification_fallback(language)

        if intent == "greeting" or self._is_greeting(text):
            return self._pick(self.GREETINGS, language)

        if intent == "farewell" or self._is_farewell(text):
            return self._pick(self.FAREWELLS, language)

        if intent == "confirmation":
            return self._confirmation_response(text, language)

        if intent == "cancellation":
            return self._cancellation_response(language)

        if intent == "complaint":
            return self._complaint_response(language)

        if intent == "task_status":
            return self._task_status_response(task_result, language)

        if intent == "time_date":
            return (
                "Time/date information-ah system context-la irundhu verify pannanum bro."
                if language == "tanglish"
                else "The current time and date should come from the system's timezone-aware clock."
            )

        if intent == "general" and not text:
            return self._clarification_fallback(language)

        template = self._choose_intent_template(intent, language)
        if template:
            return self._append_reasoning_summary(template, reasoning, language)

        if language == "ta":
            return (
                "உங்கள் கோரிக்கையைப் புரிந்துகொள்ள முயற்சிக்கிறேன். "
                "நீங்கள் எதிர்பார்க்கும் முடிவைச் சற்றுத் தெளிவாகச் சொல்ல முடியுமா?"
            )

        if language == "tanglish":
            return (
                "Purinjiduchu bro—initial-ah analyse pannalaam. "
                "Exact result enna venum-nu konjam detail sonna, "
                "next step precise-ah decide pannalaam."
            )

        return (
            "I can help with that. I'll work from the information available, "
            "make uncertainty clear, and ask for clarification when needed."
        )

    def _try_provider(
        self,
        *,
        user_input: str,
        intent: str,
        context: Any,
        reasoning: Any,
        task_result: Any,
        language: str,
        tone: str,
    ) -> str | None:
        if self.provider is None:
            return None

        method = getattr(self.provider, "generate_response", None)
        if not callable(method):
            method = getattr(self.provider, "generate", None)
        if not callable(method):
            method = getattr(self.provider, "respond", None)
        if not callable(method):
            return None

        try:
            output = method(
                user_input,
                intent=intent,
                context=context,
                reasoning=reasoning,
                task_result=task_result,
                language=language,
                tone=tone,
            )
        except TypeError:
            try:
                output = method(user_input)
            except Exception:  # noqa: BLE001 - provider fallback boundary
                return None
        except Exception:  # noqa: BLE001 - optional provider failure
            return None

        if isinstance(output, str) and output.strip():
            return output.strip()

        if isinstance(output, Mapping):
            value = output.get("text", output.get("response", output.get("message")))
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    def _respond_to_task_result(
        self,
        *,
        task_result: Any,
        language: str,
    ) -> str | None:
        if task_result is None:
            return None

        status = str(self._value(task_result, "status", "")).casefold()
        message = self._value(task_result, "message")
        error = self._value(task_result, "error")

        if status in {"success", "completed", "complete", "done"}:
            if message:
                return str(message)
            return (
                "Action complete-nu task layer confirm pannirukku bro."
                if language == "tanglish"
                else "The task layer reports that the action completed."
            )

        if status in {"failed", "error"}:
            detail = str(error or message or "No additional error details are available.")
            return (
                f"Task fail aayirukku bro: {detail}"
                if language == "tanglish"
                else f"The task failed: {detail}"
            )

        if status in {"pending", "awaiting_approval", "needs_approval"}:
            return (
                "Indha action-ku approval pending bro. Confirm pannama execute panna maatten."
                if language == "tanglish"
                else "This action is awaiting approval; it has not been executed yet."
            )

        if status in {"running", "in_progress"}:
            return (
                "Task in progress bro; complete aana apram result confirm pannalaam."
                if language == "tanglish"
                else "The task is in progress; the result is not confirmed yet."
            )

        return None

    def _choose_intent_template(self, intent: str, language: str) -> str | None:
        templates = self.INTENT_TEMPLATES.get(intent)
        if not templates:
            return None

        if language == "ta":
            tamil_templates = (
                "சரி, இதைத் தெளிவான படிகளாகப் பிரித்து அணுகலாம்.",
                "முதலில் தேவையைப் புரிந்துகொண்டு, பிறகு பாதுகாப்பான நடைமுறையைத் தேர்வு செய்வோம்.",
            )
            return random.choice(tamil_templates)

        if language == "tanglish":
            tanglish_templates = [
                template for template in templates
                if any(word in template.casefold() for word in ("bro", "pannalaam", "panren", "paakkalaam"))
            ]
            return random.choice(tanglish_templates or templates)

        return random.choice(templates)

    def _append_reasoning_summary(
        self,
        response: str,
        reasoning: Any,
        language: str,
    ) -> str:
        summary = self._value(reasoning, "summary")
        if not summary:
            return response

        summary_text = str(summary).strip()
        if not summary_text or summary_text.casefold() in response.casefold():
            return response

        if language == "tanglish":
            return f"{response}\n\nInitial analysis: {summary_text}"
        if language == "ta":
            return f"{response}\n\nஆரம்பப் பகுப்பாய்வு: {summary_text}"
        return f"{response}\n\nInitial analysis: {summary_text}"

    def _get_follow_up(
        self,
        *,
        text: str,
        intent: str,
        reasoning: Any,
        task_result: Any,
    ) -> str | None:
        explicit_question = self._value(reasoning, "clarification_question")
        if self._requires_clarification(reasoning) and explicit_question:
            return str(explicit_question)

        status = str(self._value(task_result, "status", "")).casefold()
        if status in {"pending", "awaiting_approval", "needs_approval"}:
            return "Would you like to approve this action?"

        if intent == "planning" and not self._value(reasoning, "steps"):
            return "What budget and deadline should I plan around?"

        if intent == "general" and len(text.split()) <= 2 and text:
            return "Konjam context sollu bro—enna outcome venum?"

        return None

    def _requires_clarification(self, reasoning: Any) -> bool:
        return bool(self._value(reasoning, "requires_clarification", False))

    def _clarification_fallback(self, language: str) -> str:
        if language == "ta":
            return "என்ன செய்ய வேண்டும் என்று இன்னும் கொஞ்சம் விவரமாகச் சொல்லுங்கள்."
        if language == "tanglish":
            return "Konjam detail sollu bro—enna help venum?"
        return "Could you share a little more detail about what you'd like me to do?"

    def _confirmation_response(self, text: str, language: str) -> str:
        if language == "ta":
            return "சரி. அடுத்த படியைச் செய்வதற்கு முன், எந்தச் செயலுக்கு நீங்கள் ஒப்புதல் அளிக்கிறீர்கள் என்பதை உறுதிப்படுத்துவோம்."
        if language == "tanglish":
            return "Seri bro. Endha action-ku confirmation-nu verify pannitu next step edukkalaam."
        return "Understood. I'll verify which action you're confirming before proceeding."

    def _cancellation_response(self, language: str) -> str:
        if language == "ta":
            return "சரி, அந்தச் செயலைத் தொடரமாட்டேன்."
        if language == "tanglish":
            return "Seri bro, andha action-ah continue panna maatten."
        return "Okay. I won't proceed with that action."

    def _complaint_response(self, language: str) -> str:
        if language == "ta":
            return "மன்னிக்கவும், bro. எது தவறாக நடந்தது என்று சொல்லுங்கள்; அதைச் சரிசெய்ய முயற்சிக்கிறேன்."
        if language == "tanglish":
            return "Sorry bro, enna thappu nadandhuchu-nu sollu. Correct panni improve pannalaam."
        return "Sorry about that. Tell me what went wrong, and I'll try to correct it."

    def _task_status_response(self, task_result: Any, language: str) -> str:
        if task_result is None:
            return (
                "Current task status enakku available illa bro."
                if language == "tanglish"
                else "I don't have a current task status available."
            )

        status = self._value(task_result, "status", "unknown")
        message = self._value(task_result, "message", "")
        return f"Task status: {status}. {message}".strip()

    def _response_confidence(
        self,
        *,
        text: str,
        intent: str,
        reasoning: Any,
        task_result: Any,
    ) -> float:
        value = self._value(reasoning, "confidence")
        if value is not None:
            try:
                confidence = float(value)
                return round(max(0.0, min(1.0, confidence)), 2)
            except (TypeError, ValueError):
                pass

        if task_result is not None:
            status = str(self._value(task_result, "status", "")).casefold()
            if status in {"success", "completed", "complete", "done"}:
                return 0.9
            if status in {"failed", "error"}:
                return 0.9

        if intent != "general":
            return 0.7
        if len(text.split()) >= 4:
            return 0.6
        return 0.4

    def _detect_language(self, text: str) -> str | None:
        if not text:
            return None

        if re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"

        lowered = text.casefold()
        tanglish_matches = sum(
            1
            for marker in self.LANGUAGE_MARKERS["tanglish"]
            if re.search(rf"\b{re.escape(marker)}\b", lowered)
        )
        if tanglish_matches:
            return "tanglish"

        return None

    def _normalize_language(self, language: str | None) -> str:
        value = str(language or "en").strip().casefold()
        aliases = {
            "tamil": "ta",
            "தமிழ்": "ta",
            "english": "en",
            "tanglish": "tanglish",
            "ta": "ta",
            "en": "en",
        }
        return aliases.get(value, "en")

    def _normalize_tone(self, tone: str | None) -> str:
        value = str(tone or "friendly").strip().casefold()
        allowed = {"friendly", "professional", "concise", "playful", "empathetic"}
        return value if value in allowed else "friendly"

    def _normalize_intent(self, intent: Any) -> str:
        return str(intent or "general").strip().casefold().replace(" ", "_") or "general"

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    def _sanitize_response(self, response: Any) -> str:
        text = self._normalize_text(response)
        if not text:
            return self._clarification_fallback(self.default_language)
        return text[: self.max_response_chars]

    def _is_greeting(self, text: str) -> bool:
        normalized = text.casefold().strip(" .,!?")
        return normalized in {
            "hi", "hello", "hey", "hey bro", "vanakkam",
            "வணக்கம்", "ஹாய்", "ஹலோ",
        }

    def _is_farewell(self, text: str) -> bool:
        normalized = text.casefold().strip(" .,!?")
        return normalized in {
            "bye", "goodbye", "see you", "bye bro",
            "போயிட்டு வரேன்", "பை",
        }

    def _pick(self, values: Sequence[str], language: str) -> str:
        if language == "ta":
            if values is self.GREETINGS:
                return "வணக்கம்! என்ன உதவி வேண்டும்?"
            if values is self.FAREWELLS:
                return "சரி, பிறகு பேசலாம்! கவனமாக இருங்கள்."
        if language == "en":
            if values is self.GREETINGS:
                return random.choice(("Hey! How can I help?", "Hello! What would you like to work on?"))
            if values is self.FAREWELLS:
                return random.choice(("See you later! Take care.", "Goodbye! Talk to you soon."))
        if self.humor_enabled and self.default_tone == "playful" and random.random() < 0.2:
            return random.choice(self.HUMOR)
        return random.choice(values)

    def _value(self, obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, Mapping):
            return obj.get(key, default)
        return getattr(obj, key, default)


# Compatibility alias for older imports.
ResponseGenerator = ResponseEngine
