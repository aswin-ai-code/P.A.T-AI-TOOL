
"""
P.A.T Advanced AI Core Package
==============================

Provides a stable public interface for the P.A.T AI subsystem.

Design goals:
- Backward-compatible package initialization.
- Safe imports without requiring optional modules.
- Lazy access to AI components.
- No automatic model loading or heavy initialization.
- Clear package metadata for diagnostics and testing.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__version__ = "2.0.0"
__package_name__ = "P.A.T AI Core"

# Keep package import lightweight. Components are loaded only when requested.
# These names are resolved lazily so importing `ai` does not require every
# optional component to be available.

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "AIEngine": (".ai_engine", "AIEngine"),
    "AIContext": (".context", "AIContext"),
    "IntentEngine": (".intent_engine", "IntentEngine"),
    "ReasoningEngine": (".reasoning_engine", "ReasoningEngine"),
    "ResponseEngine": (".response_engine", "ResponseEngine"),
    "TaskEngine": (".task_engine", "TaskEngine"),
    "Planner": (".planner", "Planner"),
}

__all__ = [
    "AIContext",
    "AIEngine",
    "IntentEngine",
    "Planner",
    "ReasoningEngine",
    "ResponseEngine",
    "TaskEngine",
    "__package_name__",
    "__version__",
    "get_ai_capabilities",
]


def get_ai_capabilities() -> dict[str, Any]:
    """
    Return package metadata and the AI components available on disk.

    This function checks module specifications without importing the modules
    or loading AI models. It is useful for diagnostics and health checks.
    """
    from importlib.util import find_spec

    available: dict[str, bool] = {}

    for public_name, (relative_module, _) in _LAZY_EXPORTS.items():
        module_name = f"{__name__}{relative_module}"
        try:
            available[public_name] = find_spec(module_name) is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            available[public_name] = False

    return {
        "package": __package_name__,
        "version": __version__,
        "components": available,
        "available_components": [
            name for name, is_available in available.items() if is_available
        ],
        "missing_components": [
            name for name, is_available in available.items() if not is_available
        ],
    }


def __getattr__(name: str) -> Any:
    """
    Resolve supported public component names on demand.

    Python calls this function when an attribute is not already defined.
    Unknown names raise AttributeError as expected.
    """
    export = _LAZY_EXPORTS.get(name)
    if export is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )

    relative_module, attribute_name = export
    module = import_module(relative_module, package=__name__)

    try:
        value = getattr(module, attribute_name)
    except AttributeError as exc:
        raise ImportError(
            f"{attribute_name!r} is not defined in "
            f"{relative_module!r}. Check the component implementation."
        ) from exc

    # Cache the resolved component for subsequent attribute access.
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose lazy exports to IDEs, autocomplete, and interactive tools."""
    return sorted(set(globals()) | set(__all__))
