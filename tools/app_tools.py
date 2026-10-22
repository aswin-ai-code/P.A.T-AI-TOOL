
"""P.A.T application tools.

Provides guarded helpers for opening approved applications and websites.
Designed for Windows, with graceful handling on other platforms.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse


class AppTools:
    """Guarded application and browser utilities."""

    def __init__(
        self,
        allowed_apps: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.timeout = max(1.0, float(timeout))
        self.allowed_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "file explorer": "explorer.exe",
        }
        if allowed_apps:
            self.allowed_apps.update(
                {
                    str(name).strip().lower(): str(target).strip()
                    for name, target in allowed_apps.items()
                    if str(name).strip() and str(target).strip()
                }
            )

    def open_app(self, app_name: str) -> dict[str, Any]:
        """Open a supported application by its registered alias."""
        name = str(app_name or "").strip().lower()

        if not name:
            return self._result(False, "invalid", "App name is required.")

        target = self.allowed_apps.get(name)
        if target is None:
            return self._result(
                False,
                "not_allowed",
                f"'{name}' is not in the approved application list.",
            )

        try:
            if platform.system() == "Windows":
                # Shell execution is deliberately disabled.
                subprocess.Popen(
                    [target],
                    shell=False,
                    close_fds=True,
                )
            else:
                executable = shutil.which(target)
                if executable is None:
                    return self._result(
                        False,
                        "unsupported",
                        f"'{name}' is not available on this system.",
                    )
                subprocess.Popen(
                    [executable],
                    shell=False,
                    close_fds=True,
                )

            return self._result(
                True,
                "opened",
                f"Opened {name}.",
                app=name,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return self._result(
                False,
                "error",
                f"Could not open {name}: {exc}",
            )

    def open_website(self, url: str) -> dict[str, Any]:
        """Open an HTTP(S) URL in the default browser."""
        address = str(url or "").strip()

        if not address:
            return self._result(
                False, "invalid", "Website URL is required."
            )

        if "://" not in address:
            address = "https://" + address

        parsed = urlparse(address)

        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            return self._result(
                False,
                "invalid",
                "Only valid HTTP and HTTPS website URLs are allowed.",
            )

        try:
            opened = webbrowser.open(address, new=2)
            if not opened:
                return self._result(
                    False,
                    "error",
                    "The default browser did not confirm opening the URL.",
                    url=address,
                )

            return self._result(
                True,
                "opened",
                "Website opened in the default browser.",
                url=address,
            )
        except Exception as exc:  # noqa: BLE001 - external app launch boundary
            return self._result(
                False,
                "error",
                f"Could not open website: {exc}",
            )

    def search_web(self, query: str) -> dict[str, Any]:
        """Search the web using the default browser."""
        search_text = str(query or "").strip()

        if not search_text:
            return self._result(
                False, "invalid", "Search query is required."
            )

        url = "https://www.google.com/search?q=" + quote(search_text)
        return self.open_website(url)

    def search_youtube(self, query: str) -> dict[str, Any]:
        """Search YouTube using the default browser."""
        search_text = str(query or "").strip()

        if not search_text:
            return self._result(
                False, "invalid", "YouTube search query is required."
            )

        url = "https://www.youtube.com/results?search_query=" + quote(
            search_text
        )
        return self.open_website(url)

    def open_path(self, path: str) -> dict[str, Any]:
        """Open an existing file or directory using the OS default handler."""
        raw_path = str(path or "").strip()

        if not raw_path:
            return self._result(
                False, "invalid", "A file or folder path is required."
            )

        try:
            target = Path(raw_path).expanduser().resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            return self._result(
                False,
                "not_found",
                f"Path could not be resolved: {exc}",
            )

        try:
            if platform.system() == "Windows":
                os.startfile(str(target))  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(
                    ["open", str(target)],
                    shell=False,
                    close_fds=True,
                )
            else:
                opener = shutil.which("xdg-open")
                if opener is None:
                    return self._result(
                        False,
                        "unsupported",
                        "The xdg-open utility is not installed.",
                    )
                subprocess.Popen(
                    [opener, str(target)],
                    shell=False,
                    close_fds=True,
                )

            return self._result(
                True,
                "opened",
                "Opened the requested path.",
                path=str(target),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return self._result(
                False,
                "error",
                f"Could not open the path: {exc}",
            )

    def get_status(self) -> dict[str, Any]:
        """Return tool availability and configured aliases."""
        return {
            "component": "AppTools",
            "platform": platform.system(),
            "available": True,
            "registered_apps": sorted(self.allowed_apps),
            "timeout": self.timeout,
        }

    @staticmethod
    def _result(
        success: bool,
        status: str,
        message: str,
        **details: Any,
    ) -> dict[str, Any]:
        return {
            "success": success,
            "status": status,
            "message": message,
            **details,
        }


# Compatibility aliases for existing imports.
ApplicationTools = AppTools
AppTool = AppTools


def open_app(app_name: str) -> dict[str, Any]:
    """Convenience wrapper."""
    return AppTools().open_app(app_name)


def open_website(url: str) -> dict[str, Any]:
    """Convenience wrapper."""
    return AppTools().open_website(url)


def search_web(query: str) -> dict[str, Any]:
    """Convenience wrapper."""
    return AppTools().search_web(query)


def search_youtube(query: str) -> dict[str, Any]:
    """Convenience wrapper."""
    return AppTools().search_youtube(query)


def open_path(path: str) -> dict[str, Any]:
    """Convenience wrapper."""
    return AppTools().open_path(path)
