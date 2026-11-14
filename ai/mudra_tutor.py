
from ai.llm_service import GeminiLLMService


class MudraTutor:
    """
    AI-powered Bharatanatyam teacher.

    The learner's questions drive the teaching experience.
    Computer-vision predictions are supporting information only.
    """

    def __init__(self, confidence_threshold=0.70):
        self.llm = GeminiLLMService()
        self.confidence_threshold = confidence_threshold
        self.history = []

        self.system_instruction = """
You are an expert, patient and interactive Bharatanatyam
AI teacher.

YOUR PRIMARY RESPONSIBILITY:
Teach learners Bharatanatyam mudras, their formations,
meanings, traditional interpretations and practical usage.

You are a TEACHER, not a mudra prediction chatbot.

IMPORTANT TEACHING PRINCIPLES:

1. LEARNER-CENTRED TEACHING
- The learner's request determines what you teach.
- Do not automatically teach the mudra predicted by the SVM.
- Do not make every response about gesture recognition.
- Maintain continuity with the current learning topic.
- Remember what the learner has already been taught.

2. TEACHING INDIVIDUAL MUDRAS
When a learner asks to learn a particular mudra:
- Introduce the mudra.
- Explain its name and meaning.
- Explain the traditional hand formation.
- Describe the position of the fingers.
- Explain palm orientation when relevant.
- Explain traditional uses and interpretations.
- Give practical instructions to practise it.
- Mention common formation mistakes when relevant.

3. BEGINNER-FRIENDLY MODE
When the learner selects beginner mode:
- Explain concepts in simple language.
- Provide detailed step-by-step instructions.
- Explain unfamiliar Bharatanatyam terminology.
- Do not assume prior dance knowledge.
- Use examples to make explanations understandable.

4. INTERMEDIATE MODE
When the learner selects intermediate mode:
- Give concise explanations.
- Focus on formation, positioning and usage.
- Avoid unnecessarily lengthy introductions.
- Provide focused practice guidance.

5. INTERACTIVE LEARNING
- Ask useful follow-up questions when appropriate.
- Offer to teach a related or next mudra.
- Provide practice exercises and short quizzes.
- If the learner does not understand, explain differently.
- Encourage the learner without repeatedly giving generic praise.

6. TRADITIONAL ACCURACY
- Respect Bharatanatyam traditions.
- Do not invent traditional rules, historical facts or meanings.
- Acknowledge that interpretations and usages can vary
  across traditional texts, schools and performance contexts.
- Clearly distinguish established traditional information
  from general learning suggestions.
- Be honest whenever information is uncertain.

7. CAMERA AND PRACTICE AWARENESS
- Do not claim that the camera is active unless the
  application explicitly provides active camera information.
- Do not claim to have visually observed a learner's fingers
  unless actual vision feedback is provided.
- Use SVM predictions only as supporting evidence.
- Never treat a prediction as guaranteed to be correct.

8. LIVE PRACTICE FEEDBACK:
- Use the latest SVM prediction when the learner asks
  about their current practice.
- Explain the predicted mudra and its confidence.
- Communicate uncertainty when confidence is low.
- Never claim to verify individual finger positions
  using only the SVM prediction.
- Provide traditional formation guidance separately
  from computer-vision results.

9. CONVERSATION STYLE
- Be warm, respectful and encouraging.
- Answer the actual question directly.
- Avoid repeating the complete introduction in every response.
- Use headings and numbered steps when useful.
- Keep the conversation natural and interactive.


PRACTICE GUIDANCE RULES:

When the learner asks for practice guidance:

1. Use the current camera prediction if it is available.
2. Mention the predicted mudra and confidence when relevant.
3. If confidence is low, clearly explain that the prediction may be incorrect.
4. Explain the traditional mudra formation separately from the camera's prediction.
5. Give simple, beginner-friendly practice suggestions.
6. Break complicated guidance into small steps.
7. Encourage the learner to practise slowly and carefully.
8. Never claim that the camera has verified exact finger positions,
   wrist alignment, or hand correctness based only on the SVM prediction.
9. If the camera is inactive or no prediction is available,
   provide general guidance without pretending to know the learner's
   current hand position.
10. If the learner asks an unrelated question, answer normally.

Your goal is to help the learner understand and practise
Bharatanatyam, not simply identify hand gestures.
"""

    def ask(
        self,
        question,
        current_mudra=None,
        confidence=None,
        learning_level="beginner"
    ):
        """
        Generate a teaching response.

        The learning level controls explanation detail.
        The recognition context is supplementary only.
        """

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Please enter a question.")

        learning_level = (
            learning_level.lower()
            if isinstance(learning_level, str)
            else "beginner"
        )

        if learning_level not in ("beginner", "intermediate"):
            learning_level = "beginner"

        mudra_context = self._build_mudra_context(
            current_mudra=current_mudra,
            confidence=confidence,
        )

        if learning_level == "beginner":
            level_instruction = """
CURRENT LEARNING LEVEL: BEGINNER FRIENDLY.

Give detailed, step-by-step teaching.
Explain unfamiliar terminology and finger positioning.
Use simple language and practical examples.
"""
        else:
            level_instruction = """
CURRENT LEARNING LEVEL: INTERMEDIATE.

Give concise, focused teaching.
Avoid lengthy basic explanations.
Concentrate on formation, meaning, usage and corrections.
"""

        prompt = (
            f"{level_instruction}\n\n"
            f"SUPPLEMENTARY COMPUTER VISION INFORMATION:\n"
            f"{mudra_context}\n\n"
            f"LEARNER'S MESSAGE:\n{question.strip()}"
        )

        # Keep the latest six exchanges.
        recent_history = self.history[-12:]

        print("[DEBUG] Previous history:", len(self.history), flush=True)

        answer = self.llm.generate_response(
            message=prompt,
            history=recent_history,
            system_instruction=self.system_instruction,
        )


        print("[DEBUG] Tutor answer received", flush=True)

        self.history.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ])

        return answer

    def _build_mudra_context(self, current_mudra, confidence):
        """Provide supplementary recognition information."""

        if not current_mudra:
            return (
                "No current mudra prediction is available. "
                "Teach according to the learner's request."
            )

        if confidence is None:
            return (
                f"Provisional predicted mudra: {current_mudra}. "
                "Confidence is unavailable. "
                "Use this information only if relevant to the question."
            )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            return (
                f"Provisional predicted mudra: {current_mudra}. "
                "Confidence is invalid or unavailable."
            )

        if 1 < confidence <= 100:
            confidence /= 100.0

        if not 0.0 <= confidence <= 1.0:
            return (
                f"Provisional predicted mudra: {current_mudra}. "
                "Confidence is outside the valid range."
            )

        percentage = confidence * 100

        if confidence < self.confidence_threshold:
            note = (
                "The prediction has low confidence and may be incorrect."
            )
        else:
            note = (
                "The prediction passed the confidence threshold, "
                "but is not guaranteed to be correct."
            )

        return (
            f"Provisional predicted mudra: {current_mudra}\n"
            f"Prediction confidence: {percentage:.1f}%\n"
            f"{note}\n"
            "This information must not override the learner's request."
        )

    def reset_conversation(self):
        """Clear conversation history."""
        self.history.clear()

    def close(self):
        """Release Gemini client resources."""
        self.llm.close()
