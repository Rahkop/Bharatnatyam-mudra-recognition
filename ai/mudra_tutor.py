
from ai.llm_service import GeminiLLMService


class MudraTutor:
    """
    Unified Bharatanatyam tutor.

    Supports:
    - Explanations of the currently predicted mudra.
    - General Bharatanatyam learning questions.
    - Follow-up questions using conversation history.
    """

    def __init__(self, confidence_threshold=0.70):
        self.llm = GeminiLLMService()
        self.confidence_threshold = confidence_threshold
        self.history = []

        self.system_instruction = """
You are an interactive Bharatanatyam learning tutor.

Your purpose is to help learners understand Bharatanatyam mudras,
their traditional interpretations, dance terminology, practice
techniques, and related concepts.

You have two capabilities within the SAME conversation:

1. Mudra-aware tutoring:
   Use the currently predicted mudra and its confidence information
   when the learner asks about the gesture they are performing.

2. General Bharatanatyam tutoring:
   Answer general questions, explain terminology, provide learning
   guidance, and create practice exercises or quizzes even when
   no mudra is currently detected.

Guidelines:
- Give clear, beginner-friendly explanations.
- Answer the learner's actual question instead of repeating a
  generic introduction every time.
- Use conversation history to understand follow-up questions.
- Never claim that the computer-vision prediction is certainly correct.
- If the prediction is uncertain, explicitly mention that limitation.
- A model's confidence score is not a guarantee of correctness.
- Traditional interpretations and usage can vary by text, lineage,
  school, and performance context. Mention variations when relevant.
- Do not invent traditional rules, historical facts, or citations.
  If uncertain, say so honestly.
- Distinguish traditional knowledge from your own learning suggestions.
- When explaining a mudra, discuss its name, hand formation,
  common interpretations, and relevant usage when known.
- Give safe, practical practice guidance.
- Be respectful of Bharatanatyam's cultural traditions.
- Keep answers focused, using examples or short lists when useful.
"""

    def ask(self, question, current_mudra=None, confidence=None):
        """
        Ask the tutor a question.

        Args:
            question: The learner's question.
            current_mudra: Current SVM-predicted class name, if available.
            confidence: Prediction probability from 0 to 1, or 0 to 100.

        Returns:
            Gemini's response as a string.
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Please enter a question.")

        mudra_context = self._build_mudra_context(
            current_mudra=current_mudra,
            confidence=confidence,
        )

        prompt = (
            f"Current recognition context:\n{mudra_context}\n\n"
            f"Learner's question:\n{question.strip()}"
        )

        # Keep the most recent six exchanges to limit conversation size.
        recent_history = self.history[-12:]

        answer = self.llm.generate_response(
            message=prompt,
            history=recent_history,
            system_instruction=self.system_instruction,
        )

        # Save the exchange only after Gemini responds successfully.
        self.history.extend(
            [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ]
        )

        return answer

    def _build_mudra_context(self, current_mudra, confidence):
        """Describe the latest prediction without overstating certainty."""

        if not current_mudra:
            return (
                "No current mudra prediction was provided. "
                "Answer general Bharatanatyam questions normally. "
                "If the learner asks about their current hand gesture, "
                "explain that no prediction is available."
            )

        if confidence is None:
            return (
                f"Predicted mudra: {current_mudra}\n"
                "Prediction confidence: unavailable\n"
                "Treat the prediction as provisional."
            )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            return (
                f"Predicted mudra: {current_mudra}\n"
                "Prediction confidence: invalid or unavailable\n"
                "Treat the prediction as provisional."
            )

        # Accept either a probability (0.0-1.0) or a percentage (0-100).
        if 1 < confidence <= 100:
            confidence /= 100.0

        if not 0.0 <= confidence <= 1.0:
            return (
                f"Predicted mudra: {current_mudra}\n"
                "Prediction confidence: outside the valid range\n"
                "Treat the prediction as provisional."
            )

        percentage = confidence * 100

        if confidence < self.confidence_threshold:
            certainty_note = (
                "The prediction is below the configured confidence "
                "threshold. Tell the learner it may be incorrect and "
                "suggest repositioning the hand and trying again."
            )
        else:
            certainty_note = (
                "The prediction passed the configured confidence "
                "threshold, but it is not guaranteed to be correct."
            )

        return (
            f"Predicted mudra: {current_mudra}\n"
            f"Prediction confidence: {percentage:.1f}%\n"
            f"{certainty_note}"
        )

    def reset_conversation(self):
        """Clear conversation history without recreating the client."""
        self.history.clear()

    def close(self):
        """Release the Gemini client resources."""
        self.llm.close()
