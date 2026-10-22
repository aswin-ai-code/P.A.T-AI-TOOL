
"""
P.A.T Advanced Reasoning Engine
--------------------------------
Local-first reasoning, task decomposition, confidence assessment,
risk analysis, plan review, and clarification support.

This module does not execute system actions. Execution belongs to the
task/tool layer, which must enforce permissions and approval requirements.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


@dataclass(slots=True)
class ReasoningResult:
    """Structured result returned by the reasoning engine."""

    summary: str
    reasoning: list[str] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    confidence: float = 0.5
    risk_level: str = "low"
    requires_clarification: bool = False
    clarification_question: str | None = None
    requires_approval: bool = False
    intent: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return asdict(self)


class ReasoningEngine:
    """
    P.A.T's local reasoning coordinator.

    This is a deterministic reasoning foundation, not a standalone
    large language model. An optional reasoning provider can be injected
    later without changing the public interface.
    """

    ACTION_INTENTS: ClassVar[set[str]] = {
        "file_operation",
        "browser_search",
        "download",
        "app_control",
        "automation",
        "security_check",
        "system_info",
    }

    DESTRUCTIVE_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\bdelete\b",
        r"\bremove\b",
        r"\bformat\b",
        r"\bwipe\b",
        r"\bdestroy\b",
        r"\boverwrite\b",
        r"\breset\b",
        r"\bநீக்கு\b",
        r"\bஅழி\b",
        r"\bformat பண்ணு\b",
        r"\bdelete பண்ணு\b",
    )

    EXTERNAL_ACTION_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\bsend\b",
        r"\bpost\b",
        r"\bpurchase\b",
        r"\bbuy\b",
        r"\bpay\b",
        r"\bpublish\b",
        r"\bshare\b",
        r"\bsubmit\b",
        r"\binstall\b",
        r"\bexecute\b",
        r"\brun command\b",
        r"\bஅனுப்பு\b",
        r"\bpost பண்ணு\b",
        r"\bbuy பண்ணு\b",
        r"\binstall பண்ணு\b",
    )

    CLARIFICATION_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"^\s*(do it|do that|fix it|open it|delete it|அதை செய்|அத பண்ணு)\s*[.!?]*\s*$",
        r"^\s*(help me|இத பண்ணு|சரி பண்ணு)\s*[.!?]*\s*$",
    )

    STEP_HINTS: ClassVar[tuple[tuple[str, tuple[str, ...]], ...]] = (
        (
            "understand",
            ("build", "create", "develop", "make", "website", "app", "project"),
        ),
        (
            "inspect",
            ("check", "analyze", "diagnose", "review", "find", "கண்டுபிடி"),
        ),
        (
            "plan",
            ("plan", "steps", "roadmap", "strategy", "திட்டம்"),
        ),
        (
            "implement",
            ("implement", "write code", "develop", "create", "build"),
        ),
        (
            "verify",
            ("verify", "validate", "test", "check", "confirm", "சரிபார்"),
        ),
    )

    def __init__(
        self,
        provider: Any | None = None,
        *,
        confidence_threshold: float = 0.55,
        max_steps: int = 12,
    ) -> None:
        self.provider = provider
        self.confidence_threshold = self._clamp(confidence_threshold)
        self.max_steps = max(1, int(max_steps))
        self._last_result: ReasoningResult | None = None

    def reason(
        self,
        user_input: str,
        *,
        intent: str = "general",
        context: Any = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a request and return a structured reasoning result.

        This method intentionally does not perform real-world actions.
        """
        text = self._normalize_text(user_input)
        intent_name = self._normalize_intent(intent)
        meta = dict(metadata or {})

        if not text:
            result = ReasoningResult(
                summary="The request is empty.",
                reasoning=["No actionable user request was supplied."],
                missing_information=["What would you like P.A.T to do?"],
                confidence=0.0,
                requires_clarification=True,
                clarification_question="Sollu bro, enna help venum?",
                intent=intent_name,
                metadata=meta,
            )
            return self._save(result)

        context_text = self._context_to_text(context)
        risks, risk_level, approval = self._assess_risk(text, intent_name)
        missing = self._identify_missing_information(text, intent_name)
        clarification = self._needs_clarification(text, missing)

        steps = self._decompose_task(text, intent_name)
        confidence = self._estimate_confidence(
            text=text,
            intent=intent_name,
            steps=steps,
            missing=missing,
            risks=risks,
        )

        assumptions = self._identify_assumptions(text, intent_name, context_text)
        reasoning = [
            f"Detected task category: {intent_name}.",
            f"Estimated complexity: {self._estimate_complexity(text, steps)}.",
            f"Risk assessment: {risk_level}.",
            (
                "The request needs clarification before a reliable plan can be made."
                if clarification
                else "The request has enough detail for an initial plan."
            ),
        ]

        question = self._clarification_question(missing, intent_name) if clarification else None

        result = ReasoningResult(
            summary=self._make_summary(text, intent_name, steps),
            reasoning=reasoning,
            steps=steps,
            assumptions=assumptions,
            missing_information=missing,
            risks=risks,
            confidence=confidence,
            risk_level=risk_level,
            requires_clarification=clarification,
            clarification_question=question,
            requires_approval=approval,
            intent=intent_name,
            metadata={
                **meta,
                "step_count": len(steps),
                "context_available": bool(context_text),
                "provider_available": self.provider is not None,
                "engine": "local-rule-based",
            },
        )

        provider_result = self._try_provider(
            text=text,
            intent=intent_name,
            context=context,
            local_result=result,
        )
        if provider_result is not None:
            result = provider_result

        return self._save(result)

    def analyze(
        self,
        user_input: str,
        intent: str = "general",
        context: Any = None,
    ) -> dict[str, Any]:
        """Compatibility alias used by orchestration components."""
        return self.reason(user_input, intent=intent, context=context)

    def evaluate_plan(
        self,
        plan: Any,
        *,
        user_input: str = "",
    ) -> dict[str, Any]:
        """Review a proposed plan for missing steps and risky actions."""
        plan_steps = self._extract_plan_steps(plan)
        risks: list[str] = []
        recommendations: list[str] = []

        if not plan_steps:
            recommendations.append("Create at least one concrete task step.")

        for index, step in enumerate(plan_steps, start=1):
            description = self._step_description(step)
            lowered = description.casefold()

            if self._matches_any(lowered, self.DESTRUCTIVE_PATTERNS):
                risks.append(f"Step {index} may delete or overwrite data.")
                recommendations.append(
                    f"Step {index}: confirm the exact target and create a backup if appropriate."
                )

            if self._matches_any(lowered, self.EXTERNAL_ACTION_PATTERNS):
                risks.append(f"Step {index} may affect an external system or account.")
                recommendations.append(
                    f"Step {index}: request explicit approval before carrying out the action."
                )

        if user_input and not user_input.strip():
            recommendations.append("Clarify the user's goal before proceeding.")

        risk_level = self._risk_level_from_count(risks)
        return {
            "valid": bool(plan_steps),
            "step_count": len(plan_steps),
            "risk_level": risk_level,
            "risks": self._unique(risks),
            "recommendations": self._unique(recommendations),
            "requires_approval": bool(risks),
        }

    def assess_risk(
        self,
        user_input: str,
        intent: str = "general",
    ) -> dict[str, Any]:
        """Public risk-assessment interface."""
        risks, level, approval = self._assess_risk(
            self._normalize_text(user_input),
            self._normalize_intent(intent),
        )
        return {
            "risk_level": level,
            "risks": risks,
            "requires_approval": approval,
        }

    def get_last_result(self) -> dict[str, Any] | None:
        """Return the latest result, if one exists."""
        return self._last_result.to_dict() if self._last_result else None

    def get_status(self) -> dict[str, Any]:
        """Return engine capability information."""
        return {
            "engine": self.__class__.__name__,
            "mode": "provider-assisted" if self.provider is not None else "local-rule-based",
            "provider_available": self.provider is not None,
            "confidence_threshold": self.confidence_threshold,
            "max_steps": self.max_steps,
            "has_previous_result": self._last_result is not None,
        }

    def _try_provider(
        self,
        *,
        text: str,
        intent: str,
        context: Any,
        local_result: ReasoningResult,
    ) -> ReasoningResult | None:
        """Call an optional provider through a small, defensive interface."""
        if self.provider is None:
            return None

        method = getattr(self.provider, "reason", None)
        if not callable(method):
            method = getattr(self.provider, "analyze", None)
        if not callable(method):
            return None

        try:
            output = method(
                text,
                intent=intent,
                context=context,
                local_result=local_result.to_dict(),
            )
        except TypeError:
            try:
                output = method(text)
            except (TypeError, ValueError, RuntimeError):
                return None
        except (ValueError, RuntimeError):
            return None

        if isinstance(output, ReasoningResult):
            return output
        if not isinstance(output, Mapping):
            return None

        merged = local_result.to_dict()
        allowed_fields = {
            "summary",
            "reasoning",
            "steps",
            "assumptions",
            "missing_information",
            "risks",
            "confidence",
            "risk_level",
            "requires_clarification",
            "clarification_question",
            "requires_approval",
            "intent",
        }
        for key in allowed_fields:
            if key in output:
                merged[key] = output[key]

        try:
            merged["confidence"] = self._clamp(float(merged["confidence"]))
            merged["reasoning"] = self._string_list(merged["reasoning"])
            merged["steps"] = self._mapping_list(merged["steps"])
            merged["assumptions"] = self._string_list(merged["assumptions"])
            merged["missing_information"] = self._string_list(
                merged["missing_information"]
            )
            merged["risks"] = self._string_list(merged["risks"])
            merged["risk_level"] = self._normalize_risk(merged["risk_level"])
            merged["requires_clarification"] = bool(merged["requires_clarification"])
            merged["requires_approval"] = bool(merged["requires_approval"])
            merged["metadata"] = {
                **local_result.metadata,
                "engine": "provider-assisted",
            }
            return ReasoningResult(**merged)
        except (TypeError, ValueError):
            return None

    def _assess_risk(
        self,
        text: str,
        intent: str,
    ) -> tuple[list[str], str, bool]:
        risks: list[str] = []
        lowered = text.casefold()

        if self._matches_any(lowered, self.DESTRUCTIVE_PATTERNS):
            risks.append("Potentially destructive action detected.")

        if self._matches_any(lowered, self.EXTERNAL_ACTION_PATTERNS):
            risks.append("Action may affect an external system, account, or recipient.")

        if intent in {"file_operation", "app_control", "automation"}:
            risks.append("Local resources or applications may be changed.")

        if intent == "security_check":
            risks.append(
                "Security actions must remain authorized and within the defined scope."
            )

        level = self._risk_level_from_count(risks)
        approval = any(
            marker in lowered
            for marker in (
                "delete",
                "remove",
                "format",
                "wipe",
                "send",
                "post",
                "purchase",
                "buy",
                "pay",
                "publish",
                "share",
                "submit",
                "install",
                "execute",
                "அழி",
                "நீக்கு",
                "அனுப்பு",
            )
        )
        return self._unique(risks), level, approval

    def _identify_missing_information(
        self,
        text: str,
        intent: str,
    ) -> list[str]:
        missing: list[str] = []
        lowered = text.casefold()

        if self._matches_any(lowered, self.CLARIFICATION_PATTERNS):
            missing.append("The target or intended outcome is unclear.")

        if intent == "file_operation":
            has_target = any(
                token in lowered
                for token in ("file", "folder", "document", "desktop", "download", "file ", "கோப்பு")
            )
            if not has_target:
                missing.append("Specify which file or folder is involved.")

        if intent == "download" and not re.search(r"https?://|www\.", lowered):
            missing.append("Provide the download link or exact item name.")

        if intent == "app_control" and not any(
            token in lowered
            for token in ("open", "close", "launch", "start", "quit", "திற", "மூடு")
        ):
            missing.append("Specify the application and the action to perform.")

        if intent == "automation" and not any(
            token in lowered
            for token in ("when", "every", "daily", "weekly", "if", "whenever", "போது")
        ):
            missing.append("Specify the trigger or schedule for the automation.")

        return self._unique(missing)

    def _needs_clarification(self, text: str, missing: Sequence[str]) -> bool:
        if missing:
            return True
        words = text.split()
        return bool(len(words) <= 2 and text.casefold() in {"do it", "fix it", "open it", "delete it", "அதை செய்", "அத பண்ணு"})

    def _clarification_question(
        self,
        missing: Sequence[str],
        intent: str,
    ) -> str:
        if missing:
            first = missing[0]
            if "file or folder" in first:
                return "Endha file illa folder, bro? Exact name or path sollu."
            if "download link" in first:
                return "Endha item download pannanum, bro? Link illa exact name kudu."
            if "application and the action" in first:
                return "Endha app-ah open/close pannanum, bro?"
            if "trigger or schedule" in first:
                return "Automation eppo trigger aaganum, bro? Time or condition sollu."
            return "Konjam detail sollu bro, correct-ah help panren."
        if intent == "general":
            return "Enna result venum bro? Konjam specific-ah sollu."
        return "Indha task-ku oru detail missing, bro. Konjam clarify pannalama?"

    def _decompose_task(self, text: str, intent: str) -> list[dict[str, Any]]:
        """Build a practical initial plan without executing it."""
        if self._is_simple_question(text, intent):
            return [
                {
                    "id": "step_1",
                    "action": "understand",
                    "description": "Understand the question and identify the key information needed.",
                    "depends_on": [],
                    "requires_approval": False,
                },
                {
                    "id": "step_2",
                    "action": "respond",
                    "description": "Prepare a clear answer and mention uncertainty when relevant.",
                    "depends_on": ["step_1"],
                    "requires_approval": False,
                },
            ]

        actions = self._actions_for_intent(intent, text)
        steps: list[dict[str, Any]] = []
        previous_id: str | None = None

        for index, (action, description, requires_approval) in enumerate(
            actions[: self.max_steps],
            start=1,
        ):
            step_id = f"step_{index}"
            steps.append(
                {
                    "id": step_id,
                    "action": action,
                    "description": description,
                    "depends_on": [previous_id] if previous_id else [],
                    "requires_approval": requires_approval,
                }
            )
            previous_id = step_id

        return steps

    def _actions_for_intent(
        self,
        intent: str,
        text: str,
    ) -> list[tuple[str, str, bool]]:
        if intent == "file_operation":
            return [
                ("inspect", "Identify the exact target file or folder.", False),
                ("validate", "Check the requested operation and its consequences.", False),
                ("confirm", "Ask for confirmation if the operation changes or deletes data.", True),
                ("execute", "Perform the approved file operation through the tool layer.", True),
                ("verify", "Verify the result and report any errors.", False),
            ]

        if intent in {"browser_search", "question"}:
            return [
                ("understand", "Extract the user's question and relevant search terms.", False),
                ("search", "Search an appropriate source if online lookup is required.", False),
                ("evaluate", "Compare relevant information and source reliability.", False),
                ("respond", "Present the answer with uncertainty and sources when available.", False),
            ]

        if intent == "download":
            return [
                ("identify", "Identify the exact requested file and its source.", False),
                ("validate", "Check the source, file type, and destination.", False),
                ("confirm", "Request approval before risky or consequential changes.", True),
                ("download", "Download only through an authorized download tool.", True),
                ("verify", "Check the downloaded file and report its saved location.", False),
            ]

        if intent == "app_control":
            return [
                ("identify", "Identify the application and requested operation.", False),
                ("validate", "Check whether the operation is supported and safe.", False),
                ("confirm", "Request confirmation for consequential actions.", True),
                ("execute", "Use the approved application-control tool.", True),
                ("verify", "Check whether the requested application action succeeded.", False),
            ]

        if intent == "automation":
            return [
                ("clarify", "Identify the trigger, schedule, action, and scope.", False),
                ("design", "Create a workflow with clear conditions and failure handling.", False),
                ("review", "Review permissions and possible side effects.", False),
                ("confirm", "Get approval before enabling the automation.", True),
                ("verify", "Verify the automation configuration and report its status.", False),
            ]

        if intent == "coding":
            return [
                ("understand", "Identify requirements, constraints, and expected behavior.", False),
                ("design", "Choose a compatible implementation and interfaces.", False),
                ("implement", "Write the requested code and preserve existing contracts.", False),
                ("review", "Review edge cases, errors, and security considerations.", False),
                ("verify", "Validate the implementation during the designated testing phase.", False),
            ]

        if intent == "planning":
            return [
                ("clarify", "Identify the goal, constraints, budget, and timeline.", False),
                ("research", "Gather relevant facts when research is needed.", False),
                ("plan", "Break the goal into ordered, achievable milestones.", False),
                ("review", "Check dependencies, risks, and alternatives.", False),
                ("respond", "Present the recommended plan and next actions.", False),
            ]

        if intent == "security_check":
            return [
                ("scope", "Confirm ownership, authorization, and the allowed target scope.", False),
                ("inspect", "Collect only the information needed for the defensive assessment.", False),
                ("analyze", "Evaluate indicators, likely causes, and confidence.", False),
                ("recommend", "Suggest proportionate defensive remediation.", False),
                ("report", "Summarize evidence, limitations, and recommended actions.", False),
            ]

        if intent == "calculation":
            return [
                ("parse", "Identify the expression, units, and required precision.", False),
                ("calculate", "Compute the result using a suitable calculation method.", False),
                ("check", "Check the result and unit consistency.", False),
                ("respond", "Return the result with a concise explanation.", False),
            ]

        if intent == "memory_store":
            return [
                ("identify", "Identify the information the user wants retained.", False),
                ("review", "Check whether it is suitable to retain and how it should be scoped.", False),
                ("confirm", "Confirm ambiguous or sensitive retention requests when necessary.", False),
                ("store", "Save only through the approved memory interface.", True),
                ("respond", "Explain what was saved or what still needs confirmation.", False),
            ]

        if intent == "memory_recall":
            return [
                ("retrieve", "Retrieve relevant available conversation context.", False),
                ("verify", "Check whether the retrieved information actually supports the answer.", False),
                ("respond", "Answer and state clearly if the information is unavailable.", False),
            ]

        if intent in self.ACTION_INTENTS:
            return [
                ("understand", "Identify the requested action and its target.", False),
                ("validate", "Check capability, permissions, and potential side effects.", False),
                ("execute", "Carry out the action only through the authorized tool layer.", True),
                ("verify", "Check the outcome and report any limitations.", False),
            ]

        return [
            ("understand", "Interpret the user's goal and relevant context.", False),
            ("organize", "Identify the key information or subtasks needed.", False),
            ("respond", "Provide the most useful response supported by available information.", False),
        ]

    def _estimate_confidence(
        self,
        *,
        text: str,
        intent: str,
        steps: Sequence[Mapping[str, Any]],
        missing: Sequence[str],
        risks: Sequence[str],
    ) -> float:
        confidence = 0.52

        if len(text.split()) >= 4:
            confidence += 0.12
        if intent != "general":
            confidence += 0.12
        if steps:
            confidence += 0.08
        if missing:
            confidence -= 0.22
        if len(risks) >= 2:
            confidence -= 0.08
        if len(text) < 5:
            confidence -= 0.2

        return round(self._clamp(confidence), 2)

    def _identify_assumptions(
        self,
        text: str,
        intent: str,
        context_text: str,
    ) -> list[str]:
        assumptions: list[str] = []

        if intent in self.ACTION_INTENTS:
            assumptions.append(
                "Any real action must be performed through an authorized tool with appropriate permissions."
            )

        if not context_text:
            assumptions.append(
                "No additional conversation context was supplied to this reasoning call."
            )

        if re.search(r"\b(it|that|there|அதை|அங்க)\b", text.casefold()):
            assumptions.append(
                "A referenced item may depend on earlier conversation context."
            )

        return assumptions

    def _make_summary(
        self,
        text: str,
        intent: str,
        steps: Sequence[Mapping[str, Any]],
    ) -> str:
        preview = text if len(text) <= 140 else f"{text[:137].rstrip()}..."
        return (
            f"Prepared an initial {intent.replace('_', ' ')} analysis "
            f"with {len(steps)} planned step(s): {preview}"
        )

    def _estimate_complexity(
        self,
        text: str,
        steps: Sequence[Mapping[str, Any]],
    ) -> str:
        if len(steps) >= 5 or len(text.split()) >= 30:
            return "high"
        if len(steps) >= 3 or len(text.split()) >= 12:
            return "medium"
        return "low"

    def _is_simple_question(self, text: str, intent: str) -> bool:
        if intent in {"greeting", "farewell", "help", "time_date", "calculation"}:
            return True
        return intent == "question" and len(text.split()) < 18

    def _extract_plan_steps(self, plan: Any) -> list[Any]:
        if isinstance(plan, Mapping):
            steps = plan.get("steps", [])
        else:
            steps = getattr(plan, "steps", [])

        if isinstance(steps, Sequence) and not isinstance(steps, (str, bytes)):
            return list(steps)
        return []

    def _step_description(self, step: Any) -> str:
        if isinstance(step, Mapping):
            value = step.get("description", step.get("task", step.get("action", "")))
        else:
            value = getattr(
                step,
                "description",
                getattr(step, "task", getattr(step, "action", "")),
            )
        return str(value)

    def _context_to_text(self, context: Any) -> str:
        if context is None:
            return ""

        if isinstance(context, str):
            return context.strip()

        if isinstance(context, Mapping):
            return " ".join(
                str(value)
                for value in context.values()
                if isinstance(value, (str, int, float))
            )

        for attribute in ("summary", "context", "recent_messages", "messages"):
            value = getattr(context, attribute, None)
            if value:
                if isinstance(value, str):
                    return value
                if isinstance(value, Sequence):
                    return " ".join(str(item) for item in value)

        return ""

    def _matches_any(self, text: str, patterns: Sequence[str]) -> bool:
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    def _normalize_intent(self, intent: Any) -> str:
        normalized = str(intent or "general").strip().casefold().replace(" ", "_")
        return normalized or "general"

    def _normalize_risk(self, risk: Any) -> str:
        value = str(risk or "low").strip().casefold()
        return value if value in {"low", "medium", "high", "critical"} else "medium"

    def _risk_level_from_count(self, risks: Sequence[str]) -> str:
        count = len(self._unique(risks))
        if count >= 3:
            return "high"
        if count == 2:
            return "medium"
        if count == 1:
            return "medium"
        return "low"

    def _string_list(self, value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [str(item) for item in value]
        return []

    def _mapping_list(self, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return []
        return [dict(item) for item in value if isinstance(item, Mapping)]

    def _unique(self, values: Sequence[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            item = str(value).strip()
            key = item.casefold()
            if item and key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _save(self, result: ReasoningResult) -> dict[str, Any]:
        self._last_result = result
        return result.to_dict()


# Backwards-compatible alias for older imports.
Reasoner = ReasoningEngine
