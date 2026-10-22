
"""Central configuration for P.A.T."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "P.A.T"
FULL_NAME = "Personal Assistant Tool"
VERSION = "1.0.0"

DEVELOPER_MODE = (
    os.getenv("PAT_DEVELOPER_MODE", "true").strip().casefold()
    in {"1", "true", "yes", "on"}
)

TIMEZONE = os.getenv("PAT_TIMEZONE", "Asia/Kolkata").strip()

DEFAULT_GREETING = (
    "Hey bro! 😎 I'm P.A.T, your Personal Assistant Tool. "
    "Enna help venum?"
)

UNKNOWN_COMMAND_MESSAGE = (
    "I don't understand that request yet, bro. "
    "Tell me a little more, or ask for help."
)

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"

WORKSPACE_DIR = Path(
    os.getenv(
        "PAT_WORKSPACE_DIR",
        str(Path.home() / "PAT_Workspace"),
    )
).expanduser()

MAX_CONVERSATION_MESSAGES = 100
MAX_MEMORY_ITEMS = 500
MAX_INPUT_LENGTH = 10_000

DEFAULT_LANGUAGE = "auto"
DEFAULT_TONE = "friendly"
ENABLE_HUMOR = True
ENABLE_CONTEXT = True

REQUIRE_CONFIRMATION_FOR_DESTRUCTIVE_ACTIONS = True
ALLOW_AUTOMATIC_TASK_EXECUTION = False

ONLINE_AI_ENABLED = (
    os.getenv("PAT_ONLINE_AI_ENABLED", "false").strip().casefold()
    in {"1", "true", "yes", "on"}
)

AI_PROVIDER = os.getenv("PAT_AI_PROVIDER", "local").strip().casefold()


def get_config_status() -> dict[str, object]:
    """Return safe configuration details without exposing secrets."""
    return {
        "app_name": APP_NAME,
        "full_name": FULL_NAME,
        "version": VERSION,
        "developer_mode": DEVELOPER_MODE,
        "timezone": TIMEZONE,
        "project_root": str(PROJECT_ROOT),
        "workspace_dir": str(WORKSPACE_DIR),
        "online_ai_enabled": ONLINE_AI_ENABLED,
        "ai_provider": AI_PROVIDER,
        "automatic_task_execution": ALLOW_AUTOMATIC_TASK_EXECUTION,
    }
