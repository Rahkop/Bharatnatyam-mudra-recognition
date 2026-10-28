
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load API configuration from the project's .env file.
load_dotenv()


class GeminiLLMService:
    """Handles communication between the application and Gemini."""

    def __init__(self, model=None):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key or api_key == "your_actual_gemini_api_key":
            raise ValueError(
                "GEMINI_API_KEY is missing. "
                "Add your Gemini API key to the .env file."
            )

        self.model = model or os.getenv(
            "GEMINI_MODEL", "gemini-flash-latest"
        )

        self.client = genai.Client(api_key=api_key)

    def generate_response(
        self,
        message,
        history=None,
        system_instruction=None,
    ):
        """
        Generate a Gemini response.

        Args:
            message: The user's latest message.
            history: Previous messages, each containing 'role' and 'content'.
            system_instruction: Instructions defining the tutor's behavior.

        Returns:
            The generated response as a string.
        """
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Message cannot be empty.")

        formatted_history = []

        for entry in history or []:
            role = entry.get("role")
            content = entry.get("content", "")

            # Gemini uses "model" for assistant responses.
            if role == "assistant":
                role = "model"

            if role not in ("user", "model"):
                raise ValueError(
                    "History roles must be 'user', 'model', or 'assistant'."
                )

            if not isinstance(content, str) or not content.strip():
                continue

            formatted_history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content)],
                )
            )

        config = None

        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        models_to_try = [self.model]

        fallback_model = os.getenv(
            "GEMINI_FALLBACK_MODEL", ""
        ).strip()

        if fallback_model and fallback_model != self.model:
            models_to_try.append(fallback_model)

        last_error = None

        for model_name in models_to_try:
            try:
                chat = self.client.chats.create(
                    model=model_name,
                    history=formatted_history,
                    config=config,
                )

                response = chat.send_message(message=message)
                answer = response.text

                if not answer or not answer.strip():
                    raise RuntimeError(
                        "Gemini returned an empty response. Please try again."
                    )

                return answer.strip()

            except Exception as exc:
                last_error = exc

                # Use the fallback only for temporary server overloads.
                if "503" not in str(exc):
                    break

        raise RuntimeError(
            f"Gemini request failed after trying the configured model(s): "
            f"{last_error}"
        ) from last_error



    def close(self):
        """Release the underlying client resources."""
        self.client.close()
