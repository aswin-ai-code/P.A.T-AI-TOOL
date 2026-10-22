
"""Persistent JSON memory manager for P.A.T."""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from config import DATA_DIR, MAX_MEMORY_ITEMS
except ImportError:
    DATA_DIR = Path(__file__).resolve().parent / "data"
    MAX_MEMORY_ITEMS = 500

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_FILE = Path(DATA_DIR) / "memory.json"


class Memory:
    """Store and retrieve small pieces of persistent assistant memory.

    Memory is stored as JSON with this structure:
        {
            "key": {
                "value": "...",
                "updated_at": "...",
                "created_at": "..."
            }
        }

    This class does not collect information automatically. The caller decides
    what to save and should obtain consent when storing sensitive information.
    """

    def __init__(
        self,
        file_path: str | Path | None = None,
        *,
        max_items: int | None = None,
    ) -> None:
        self.file_path = Path(file_path or DEFAULT_MEMORY_FILE).expanduser()
        self.max_items = max(
            1,
            int(max_items if max_items is not None else MAX_MEMORY_ITEMS),
        )
        self._lock = threading.RLock()
        self._data: dict[str, dict[str, Any]] = {}
        self._load_error: str | None = None
        self.load()

    @staticmethod
    def _timestamp() -> str:
        """Return a timezone-aware UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_key(key: str) -> str:
        if not isinstance(key, str):
            raise TypeError("Memory keys must be strings.")

        normalized = " ".join(key.strip().split())
        if not normalized:
            raise ValueError("Memory key cannot be empty.")

        if len(normalized) > 200:
            raise ValueError("Memory key cannot exceed 200 characters.")

        return normalized.casefold()

    @staticmethod
    def _validate_value(value: Any) -> Any:
        """Ensure a value can be safely represented as JSON."""
        try:
            encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
            return json.loads(encoded)
        except (TypeError, ValueError) as exc:
            raise ValueError("Memory value must be JSON-serializable.") from exc

    def load(self) -> dict[str, dict[str, Any]]:
        """Load saved memory without overwriting a damaged file."""
        with self._lock:
            if not self.file_path.exists():
                self._data = {}
                self._load_error = None
                return self._data.copy()

            try:
                with self.file_path.open("r", encoding="utf-8") as file:
                    loaded = json.load(file)

                if not isinstance(loaded, dict):
                    raise TypeError("Memory JSON root must be an object.")

                clean: dict[str, dict[str, Any]] = {}
                for key, item in loaded.items():
                    if not isinstance(key, str) or not isinstance(item, dict):
                        continue
                    if "value" not in item:
                        continue
                    clean[key] = {
                        "value": self._validate_value(item["value"]),
                        "created_at": str(item.get("created_at", "")),
                        "updated_at": str(item.get("updated_at", "")),
                    }

                self._data = clean
                self._load_error = None
                return self._data.copy()

            except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
                self._load_error = str(exc)
                logger.error(
                    "Could not load memory file %s: %s",
                    self.file_path,
                    exc,
                )
                # Keep the file intact. Do not silently overwrite corrupted data.
                self._data = {}
                return {}

    def _save_locked(self) -> bool:
        """Atomically save memory. Caller must hold the lock."""
        temporary_path = self.file_path.with_name(
            f".{self.file_path.name}.{os.getpid()}.tmp"
        )

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(
                self._data,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )

            with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
                file.write(payload)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_path, self.file_path)
            self._load_error = None
            return True

        except (OSError, TypeError, ValueError):
            logger.exception("Could not save P.A.T memory.")
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.debug("Could not remove temporary memory file.")
            return False

    def save(self) -> bool:
        """Persist current memory to disk."""
        with self._lock:
            if self._load_error:
                logger.error(
                    "Memory save blocked because the existing file failed to load."
                )
                return False
            return self._save_locked()

    def remember(self, key: str, value: Any) -> bool:
        """Create or update a memory entry."""
        normalized_key = self._normalize_key(key)
        safe_value = self._validate_value(value)

        with self._lock:
            if self._load_error:
                logger.error(
                    "Memory update blocked: resolve the existing memory file first."
                )
                return False

            is_new = normalized_key not in self._data
            if is_new and len(self._data) >= self.max_items:
                logger.warning("Memory capacity reached; no new item was saved.")
                return False

            old_entry = self._data.get(normalized_key)
            now = self._timestamp()

            self._data[normalized_key] = {
                "value": safe_value,
                "created_at": (
                    old_entry.get("created_at", now) if old_entry else now
                ),
                "updated_at": now,
            }

            if self._save_locked():
                return True

            if old_entry is None:
                self._data.pop(normalized_key, None)
            else:
                self._data[normalized_key] = old_entry
            return False

    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve a saved value, or return default when missing."""
        normalized_key = self._normalize_key(key)

        with self._lock:
            entry = self._data.get(normalized_key)
            if entry is None:
                return default
            return entry.get("value", default)

    def forget(self, key: str) -> bool:
        """Delete one memory entry and persist the change."""
        normalized_key = self._normalize_key(key)

        with self._lock:
            if self._load_error or normalized_key not in self._data:
                return False

            old_entry = self._data.pop(normalized_key)
            if self._save_locked():
                return True

            self._data[normalized_key] = old_entry
            return False

    def clear(self) -> bool:
        """Clear all entries, restoring them if saving fails."""
        with self._lock:
            if self._load_error:
                return False

            old_data = self._data.copy()
            self._data = {}

            if self._save_locked():
                return True

            self._data = old_data
            return False

    def all(self) -> dict[str, Any]:
        """Return a copy of all key/value entries."""
        with self._lock:
            return {
                key: entry["value"]
                for key, entry in self._data.items()
                if "value" in entry
            }

    def get_all(self) -> dict[str, Any]:
        """Compatibility alias for all()."""
        return self.all()

    def get(self, key: str, default: Any = None) -> Any:
        """Compatibility alias for recall()."""
        return self.recall(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Compatibility alias for remember()."""
        return self.remember(key, value)

    def delete(self, key: str) -> bool:
        """Compatibility alias for forget()."""
        return self.forget(key)

    def reload(self) -> dict[str, dict[str, Any]]:
        """Reload memory from disk."""
        return self.load()

    def status(self) -> dict[str, Any]:
        """Return a safe summary without exposing saved values."""
        with self._lock:
            return {
                "file_path": str(self.file_path),
                "items": len(self._data),
                "max_items": self.max_items,
                "loaded": self._load_error is None,
                "error": self._load_error,
            }


# Backward-compatible class names for existing modules.
MemoryManager = Memory
PATMemory = Memory
PersistentMemory = Memory
