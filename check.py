
"""P.A.T project health checker.

Checks Python syntax, expected project files, imports, and Ruff.
Does not modify source files or user memory.
"""

from __future__ import annotations

import ast
import importlib.util
import logging
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "P.A.T-source"

# Support either layout:
# P.A.T/
#   check.py
#   P.A.T-source/
# or a layout where Python files live beside check.py.
PROJECT = SOURCE if SOURCE.is_dir() else ROOT

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("pat.check")


def report(label: str, success: bool, detail: str = "") -> bool:
    status = "PASS" if success else "FAIL"
    message = f"[{status}] {label}"
    if detail:
        message += f" â€” {detail}"

    print(message)
    return success


def python_files() -> list[Path]:
    """Collect project Python files, excluding virtual environments."""
    excluded = {
        ".git",
        ".venv",
        ".venv313",
        "venv",
        "__pycache__",
        "build",
        "dist",
        ".ruff_cache",
        "backups",
        "communication_backup_20261020_085332",
        "PAT-source",
    }

    files: list[Path] = []

    for path in PROJECT.rglob("*.py"):
        try:
            relative = path.relative_to(PROJECT)
        except ValueError:
            continue

        if any(part in excluded for part in relative.parts):
            continue

        files.append(path)

    return sorted(files)


def check_python_syntax(files: list[Path]) -> tuple[int, int]:
    """Compile Python source to AST without executing project code."""
    passed = 0
    failed = 0

    print("\n--- Python syntax ---")

    for path in files:
        try:
            source = path.read_text(encoding="utf-8-sig")
            ast.parse(source, filename=str(path))
            passed += 1
        except (SyntaxError, UnicodeError, OSError) as exc:
            failed += 1
            report(
                f"Syntax: {path.relative_to(PROJECT)}",
                False,
                str(exc),
            )

    report(
        "Python syntax",
        failed == 0,
        f"{passed} passed, {failed} failed",
    )
    return passed, failed


def check_expected_files() -> int:
    """Report missing key files without assuming every optional file exists."""
    expected = [
        PROJECT / "main.py",
        PROJECT / "assistant.py",
        PROJECT / "config.py",
        PROJECT / "memory.py",
        PROJECT / "tools" / "app_tools.py",
        PROJECT / "tools" / "file_tools.py",
        PROJECT / "voice.py",
        PROJECT / "commands.py",
        PROJECT / "ai" / "ai_engine.py",
        PROJECT / "ai" / "context.py",
        PROJECT / "ai" / "intent_engine.py",
        PROJECT / "ai" / "reasoning_engine.py",
        PROJECT / "ai" / "response.py",
        PROJECT / "ai" / "planner.py",
        PROJECT / "ai" / "task_engine.py",
    ]

    print("\n--- Expected project files ---")
    missing = 0

    for path in expected:
        exists = path.is_file()
        if not exists:
            missing += 1

        report(
            str(path.relative_to(PROJECT)),
            exists,
            "" if exists else "File not found",
        )

    return missing


def check_dependencies() -> int:
    """Check whether core third-party dependencies are discoverable."""
    dependencies = {
        "speech_recognition": "speech_recognition",
        "pyttsx3": "pyttsx3",
    }

    print("\n--- Dependency availability ---")
    missing = 0

    for package, module in dependencies.items():
        try:
            available = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            available = False

        if not available:
            missing += 1

        report(
            package,
            available,
            "" if available else "Not found in this Python environment",
        )

    return missing


def check_ruff() -> bool:
    """Run Ruff when installed; do not install or modify anything."""
    print("\n--- Ruff lint ---")

    ruff = shutil.which("ruff")
    if ruff is None:
        try:
            available = importlib.util.find_spec("ruff") is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            available = False

        if not available:
            report("Ruff", False, "Not installed; lint check skipped")
            return False

        command = [sys.executable, "-m", "ruff", "check", str(PROJECT), "--exclude", "backups,backups/**,communication_backup_*,pat_backup_*,voice_before_*,voice_day1_backup.py,*.bak,*.before_*,*.py.bak"]
    else:
        command = [ruff, "check", str(PROJECT), "--exclude", "backups,backups/**,communication_backup_*,pat_backup_*,voice_before_*,voice_day1_backup.py,*.bak,*.before_*,*.py.bak"]

    try:
        result = subprocess.run(
            command,
            cwd=PROJECT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        report("Ruff execution", False, str(exc))
        return False

    if result.stdout.strip():
        print(result.stdout.rstrip())

    if result.stderr.strip():
        print(result.stderr.rstrip())

    report(
        "Ruff",
        result.returncode == 0,
        "No lint errors" if result.returncode == 0 else "Lint issues found",
    )
    return result.returncode == 0


def main() -> int:
    print("=" * 52)
    print("          P.A.T HEALTH CHECK")
    print("=" * 52)
    print(f"Python:  {sys.version.split()[0]}")
    print(f"Project: {PROJECT}")

    if not PROJECT.is_dir():
        report("Project directory", False, str(PROJECT))
        return 1

    files = python_files()
    report("Python files discovered", bool(files), f"{len(files)} found")

    if not files:
        print("No Python files found.")
        return 1

    _, syntax_failures = check_python_syntax(files)
    missing_files = check_expected_files()
    missing_dependencies = check_dependencies()
    ruff_passed = check_ruff()

    print("\n" + "=" * 52)
    print("SUMMARY")
    print(f"Python files: {len(files)}")
    print(f"Syntax errors: {syntax_failures}")
    print(f"Missing expected files: {missing_files}")
    print(f"Missing dependencies: {missing_dependencies}")
    print(f"Ruff passed: {'Yes' if ruff_passed else 'No'}")
    print("=" * 52)

    # Ruff and missing optional dependencies may need separate attention.
    # Syntax errors and missing expected project files fail the health check.
    if syntax_failures or missing_files:
        return 1

    if missing_dependencies or not ruff_passed:
        return 2

    print("Health check completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

