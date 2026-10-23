from assistant import PAT

pat = PAT()

tests = [
    "Hello",
    "How are you?",
    "I love you",
    "Thank you, bye",
]

for phrase in tests:
    try:
        result = pat.process_command(phrase)
        print(f"INPUT: {phrase}")
        print(f"RESULT TYPE: {type(result).__name__}")
        print(f"RESULT: {result!r}")
        print("-" * 30)
    except Exception as exc:  # noqa: BLE001
        print(f"INPUT: {phrase}")
        print(f"ERROR: {type(exc).__name__}: {exc}")
        print("-" * 30)

