
from ai.mudra_tutor import MudraTutor


def main():
    tutor = None

    try:
        tutor = MudraTutor()

        # Test 1: General Bharatanatyam question.
        print("\nTEST 1: General learning question")
        answer = tutor.ask(
            "What are mudras in Bharatanatyam?"
        )
        print(answer)

        # Test 2: Question about the currently predicted mudra.
        print("\nTEST 2: Mudra-aware question")
        answer = tutor.ask(
            "Explain this mudra and how it is commonly used.",
            current_mudra="Alapadma",
            confidence=0.95,
        )
        print(answer)

        # Test 3: Follow-up question in the same conversation.
        print("\nTEST 3: Follow-up question")
        answer = tutor.ask(
            "Give me one simple practice exercise for it.",
            current_mudra="Alapadma",
            confidence=0.95,
        )
        print(answer)

    except Exception as exc:
        print(f"\nTutor test failed: {type(exc).__name__}: {exc}")

    finally:
        if tutor is not None:
            tutor.close()


if __name__ == "__main__":
    main()
