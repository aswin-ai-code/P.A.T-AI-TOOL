
"""P.A.T file and directory tools.

Provides guarded file operations inside a configured workspace.
Destructive operations require explicit confirmation.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


class FileTools:
    """Manage files and directories inside an approved workspace."""

    def __init__(
        self,
        root_dir: str | Path | None = None,
        max_read_bytes: int = 2_000_000,
    ) -> None:
        self.root_dir = Path(
            root_dir or Path.home() / "PAT_Workspace"
        ).expanduser().resolve()
        self.max_read_bytes = max(1, int(max_read_bytes))
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str | Path) -> Path:
        """Resolve a workspace path and reject paths outside the root."""
        candidate = Path(path).expanduser()

        if not candidate.is_absolute():
            candidate = self.root_dir / candidate

        resolved = candidate.resolve(strict=False)

        try:
            resolved.relative_to(self.root_dir)
        except ValueError as exc:
            raise PermissionError(
                "Path is outside the approved P.A.T workspace."
            ) from exc

        # Reject symlinks within the workspace that point outside it.
        current = self.root_dir
        try:
            relative = resolved.relative_to(self.root_dir)
        except ValueError as exc:
            raise PermissionError("Invalid workspace path.") from exc

        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                actual = current.resolve(strict=True)
                try:
                    actual.relative_to(self.root_dir)
                except ValueError as exc:
                    raise PermissionError(
                        "Path traverses a symlink outside the workspace."
                    ) from exc

        return resolved

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

    def list_directory(
        self,
        path: str = ".",
        recursive: bool = False,
        limit: int = 500,
    ) -> dict[str, Any]:
        """List directory entries without opening or modifying them."""
        try:
            directory = self._resolve(path)

            if not directory.is_dir():
                return self._result(
                    False, "not_directory", "Path is not a directory."
                )

            limit = max(1, min(int(limit), 5000))
            iterator = directory.rglob("*") if recursive else directory.iterdir()
            items = []

            for entry in iterator:
                if len(items) >= limit:
                    break

                try:
                    info = entry.lstat()
                    items.append(
                        {
                            "name": entry.name,
                            "path": str(entry.relative_to(self.root_dir)),
                            "type": (
                                "symlink"
                                if entry.is_symlink()
                                else "directory"
                                if entry.is_dir()
                                else "file"
                            ),
                            "size_bytes": (
                                info.st_size if entry.is_file() else None
                            ),
                        }
                    )
                except OSError:
                    continue

            return self._result(
                True,
                "listed",
                f"Found {len(items)} item(s).",
                path=str(directory),
                items=items,
                limit=limit,
            )
        except (OSError, ValueError, PermissionError) as exc:
            return self._result(False, "error", str(exc))

    def search_files(
        self,
        query: str,
        path: str = ".",
        limit: int = 200,
    ) -> dict[str, Any]:
        """Find files and folders whose names contain the query."""
        term = str(query or "").strip().casefold()

        if not term:
            return self._result(
                False, "invalid", "Search query cannot be empty."
            )

        try:
            directory = self._resolve(path)
            if not directory.is_dir():
                return self._result(
                    False, "not_directory", "Path is not a directory."
                )

            matches = []
            limit = max(1, min(int(limit), 2000))

            for entry in directory.rglob("*"):
                if term in entry.name.casefold():
                    matches.append(
                        str(entry.relative_to(self.root_dir))
                    )
                    if len(matches) >= limit:
                        break

            return self._result(
                True,
                "searched",
                f"Found {len(matches)} matching item(s).",
                matches=matches,
            )
        except (OSError, ValueError, PermissionError) as exc:
            return self._result(False, "error", str(exc))

    def read_file(self, path: str) -> dict[str, Any]:
        """Read a bounded-size UTF-8 text file."""
        try:
            target = self._resolve(path)

            if not target.is_file():
                return self._result(
                    False, "not_file", "Path is not a regular file."
                )

            if target.is_symlink():
                return self._result(
                    False, "not_allowed", "Symbolic links cannot be read."
                )

            size = target.stat().st_size
            if size > self.max_read_bytes:
                return self._result(
                    False,
                    "too_large",
                    f"File exceeds the {self.max_read_bytes}-byte read limit.",
                    size_bytes=size,
                )

            content = target.read_text(encoding="utf-8")
            return self._result(
                True,
                "read",
                "File read successfully.",
                path=str(target),
                content=content,
                size_bytes=size,
            )
        except UnicodeDecodeError:
            return self._result(
                False,
                "encoding_error",
                "File is not valid UTF-8 text.",
            )
        except (OSError, ValueError, PermissionError) as exc:
            return self._result(False, "error", str(exc))

    def create_directory(self, path: str) -> dict[str, Any]:
        """Create a directory inside the workspace."""
        try:
            target = self._resolve(path)

            if target.exists():
                return self._result(
                    False, "already_exists", "Path already exists."
                )

            target.mkdir(parents=True, exist_ok=False)
            return self._result(
                True, "created", "Directory created.", path=str(target)
            )
        except (OSError, ValueError, PermissionError) as exc:
            return self._result(False, "error", str(exc))

    def create_file(
        self,
        path: str,
        content: str = "",
        overwrite: bool = False,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Create a UTF-8 text file; overwriting requires confirmation."""
        try:
            target = self._resolve(path)

            if target.exists() and not overwrite:
                return self._result(
                    False,
                    "already_exists",
                    "File already exists. Set overwrite=True to replace it.",
                )

            if target.exists() and overwrite and not confirm:
                return self._result(
                    False,
                    "confirmation_required",
                    "Confirm the overwrite before replacing the existing file.",
                )

            if target.is_dir():
                return self._result(
                    False, "is_directory", "Cannot write text to a directory."
                )

            target.parent.mkdir(parents=True, exist_ok=True)

            # Exclusive creation avoids accidental overwrite by default.
            if not target.exists():
                with target.open("x", encoding="utf-8", newline="") as file:
                    file.write(str(content))
            else:
                target.write_text(str(content), encoding="utf-8")

            return self._result(
                True, "created", "File saved.", path=str(target)
            )
        except FileExistsError:
            return self._result(
                False, "already_exists", "File already exists."
            )
        except (OSError, ValueError, PermissionError) as exc:
            return self._result(False, "error", str(exc))

    def copy_file(
        self,
        source: str,
        destination: str,
        overwrite: bool = False,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Copy a file within the workspace."""
        try:
            src = self._resolve(source)
            dst = self._resolve(destination)

            if src.is_symlink() or dst.is_symlink():
                return self._result(
                    False,
                    "not_allowed",
                    "Symbolic-link paths are not supported.",
                )

            if not src.is_file():
                return self._result(
                    False, "not_file", "Source is not a regular file."
                )

            if src == dst:
                return self._result(
                    False, "invalid", "Source and destination are identical."
                )

            if dst.exists() and not overwrite:
                return self._result(
                    False,
                    "already_exists",
                    "Destination exists. Set overwrite=True to replace it.",
                )

            if dst.exists() and overwrite and not confirm:
                return self._result(
                    False,
                    "confirmation_required",
                    "Confirm before overwriting the destination.",
                )

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

            return self._result(
                True,
                "copied",
                "File copied.",
                source=str(src),
                destination=str(dst),
            )
        except (OSError, ValueError, PermissionError) as exc:
            return self._result(False, "error", str(exc))

    def rename_file(
        self,
        source: str,
        destination: str,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Rename or move a file within the workspace."""
        try:
            src = self._resolve(source)
            dst = self._resolve(destination)

            if not src.is_file() or src.is_symlink():
                return self._result(
                    False,
                    "not_file",
                    "Source must be a regular file, not a symlink.",
                )

            if src == dst:
                return self._result(
                    False, "invalid", "Source and destination are identical."
                )

            if dst.exists():
                return self._result(
                    False,
                    "already_exists",
                    "Destination exists; rename will not overwrite it.",
                )

            if not confirm:
                return self._result(
                    False,
                    "confirmation_required",
                    "Confirm the file rename or move before proceeding.",
                )

            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)

            return self._result(
                True,
                "renamed",
                "File renamed or moved.",
                source=str(src),
                destination=str(dst),
            )
        except (OSError, ValueError, PermissionError) as exc:
            return self._result(False, "error", str(exc))

    def delete_file(
        self,
        path: str,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Delete a regular file only after explicit confirmation."""
        try:
            target = self._resolve(path)

            if not target.exists() and not target.is_symlink():
                return self._result(
                    False, "not_found", "File was not found."
                )

            if target.is_symlink():
                return self._result(
                    False,
                    "not_allowed",
                    "Symbolic links cannot be deleted through this method.",
                )

            if not target.is_file():
                return self._result(
                    False,
                    "not_file",
                    "This method deletes files only, not directories.",
                )

            if not confirm:
                return self._result(
                    False,
                    "confirmation_required",
                    "Explicit confirmation is required to delete this file.",
                    path=str(target),
                )

            target.unlink()
            return self._result(
                True, "deleted", "File deleted.", path=str(target)
            )
        except (OSError, ValueError, PermissionError) as exc:
            return self._result(False, "error", str(exc))

    def get_status(self) -> dict[str, Any]:
        return {
            "component": "FileTools",
            "available": True,
            "workspace": str(self.root_dir),
            "max_read_bytes": self.max_read_bytes,
        }


# Compatibility aliases and convenience functions.
FileTool = FileTools
FileManager = FileTools


def list_directory(path: str = ".", recursive: bool = False) -> dict[str, Any]:
    return FileTools().list_directory(path, recursive=recursive)


def search_files(query: str, path: str = ".") -> dict[str, Any]:
    return FileTools().search_files(query, path=path)


def read_file(path: str) -> dict[str, Any]:
    return FileTools().read_file(path)


def create_file(
    path: str,
    content: str = "",
    overwrite: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    return FileTools().create_file(
        path, content, overwrite=overwrite, confirm=confirm
    )


def delete_file(path: str, confirm: bool = False) -> dict[str, Any]:
    return FileTools().delete_file(path, confirm=confirm)
