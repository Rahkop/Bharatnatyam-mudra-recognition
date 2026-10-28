
print("1. Test script started", flush=True)

try:
    print("2. Importing GeminiLLMService...", flush=True)
    from ai.llm_service import GeminiLLMService

    print("3. Import successful", flush=True)

    print("4. Creating Gemini client...", flush=True)
    tutor = GeminiLLMService()

    print("5. Sending request to Gemini...", flush=True)
    answer = tutor.generate_response(
        message="Explain Bharatanatyam in two simple sentences."
    )

    print("\n6. Gemini response:", flush=True)
    print(answer, flush=True)

    tutor.close()

except Exception as exc:
    print(f"\nERROR: {type(exc).__name__}: {exc}", flush=True)

print("\nTest script finished.", flush=True)
