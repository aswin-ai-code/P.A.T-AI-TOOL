import subprocess
import sys


def run_check(command, name):
    print(f"\n{'=' * 50}")
    print(f"CHECK: {name}")
    print("=" * 50)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True,
        check=False,
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def main():
    print("=" * 50)
    print("        P.A.T PROJECT HEALTH CHECK")
    print("=" * 50)

    checks = [
        (
            f'"{sys.executable}" -m compileall -q .',
            "Python Syntax",
        ),
        (
            "ruff check . --fix",
            "Ruff Code Check",
        ),
    ]

    failed = []

    for command, name in checks:
        if not run_check(command, name):
            failed.append(name)

    print("\n" + "=" * 50)

    if failed:
        print("❌ P.A.T CHECK FAILED")
        print("\nProblems found:")

        for item in failed:
            print(f"- {item}")

        print("\nFix the reported errors and run:")
        print("python check.py")

    else:
        print("✅ P.A.T HEALTH CHECK PASSED")
        print("No syntax or Ruff errors found.")

    print("=" * 50)


if __name__ == "__main__":
    main()