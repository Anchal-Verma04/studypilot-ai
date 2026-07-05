import json
import re
from src.agents.base_agent import BaseAgent

class GraderAgent(BaseAgent):
    """
    Agent responsible for grading quizzes, providing feedback, and recommending topics to review.
    """

    def __init__(self):
        system_prompt = (
            "You are a supportive and analytical academic tutor. Compare the user's answers "
            "against the correct answers for a quiz. Calculate the final score and compile "
            "constructive feedback explaining correct answers and proposing next study steps. "
            "Output your analysis in a valid JSON object. Do not include markdown code block wrappers."
        )
        super().__init__(
            name="Grader Agent",
            role_description="Evaluates user quiz responses and formats detailed tutoring feedback.",
            system_prompt=system_prompt
        )

    def execute(self, quiz: dict, user_answers: dict) -> dict:
        """
        Grades the user answers. Uses Gemini API if configured, otherwise falls back to simulator.
        """
        questions = quiz.get("questions", [])
        
        # Parse answers. user_answers format: {question_id: selected_index}
        score = 0
        total = len(questions)
        graded_questions = []

        for q in questions:
            q_id = q["id"]
            correct_idx = q["answer"]
            user_val = user_answers.get(q_id)
            
            # Map index/value
            try:
                user_idx = int(user_val) if user_val is not None else -1
            except ValueError:
                user_idx = -1

            is_correct = (user_idx == correct_idx)
            if is_correct:
                score += 1
                
            graded_questions.append({
                "id": q_id,
                "question": q["question"],
                "options": q["options"],
                "correct_answer": correct_idx,
                "user_answer": user_idx,
                "is_correct": is_correct,
                "source_sentence": q.get("source_sentence", "")
            })

        if self.use_simulation:
            feedback_data = self._simulate_grading_feedback(graded_questions, score, total)
        else:
            try:
                feedback_data = self._run_api_grading_feedback(graded_questions, score, total)
            except Exception as e:
                print(f"[{self.name}] API grading failed, using simulation fallback.")
                feedback_data = self._simulate_grading_feedback(graded_questions, score, total)

        feedback_data["score"] = score
        feedback_data["total_questions"] = total
        feedback_data["percentage"] = round((score / total * 100) if total > 0 else 0, 2)
        feedback_data["graded_questions"] = graded_questions
        return feedback_data

    def _run_api_grading_feedback(self, graded_questions: list, score: int, total: int) -> dict:
        prompt = (
            f"Review this completed quiz and generate detailed feedback. Score: {score}/{total}.\n"
            f"Question Submissions:\n"
            + "\n".join([
                f"- Q: {g['question']}\n"
                f"  Options: {g['options']}\n"
                f"  Correct Option Index: {g['correct_answer']}\n"
                f"  User Chosen Index: {g['user_answer']}\n"
                f"  Status: {'CORRECT' if g['is_correct'] else 'INCORRECT'}"
                for g in graded_questions
            ]) + "\n\n"
            f"Generate general overall feedback and study suggestions.\n"
            f"Response format (must be JSON only):\n"
            f"{{\n"
            f"  \"overall_feedback\": \"Well done/Constructive critique...\",\n"
            f"  \"recommendations\": [\"Review topic X\", \"Re-read concepts about Y\"],\n"
            f"  \"question_explanations\": {{\n"
            f"     \"q_1\": \"Why the correct answer is correct...\"\n"
            f"  }}\n"
            f"}}"
        )
        raw_output = self.run_llm_generation(prompt)
        
        # Clean potential markdown packaging
        clean_json = re.sub(r"^```json\s*", "", raw_output.strip(), flags=re.IGNORECASE)
        clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.IGNORECASE)
        
        return json.loads(clean_json)

    def _simulate_grading_feedback(self, graded_questions: list, score: int, total: int) -> dict:
        """
        Simulates constructive, TurboLearn-style feedback that always shows the
        real source sentence from the notes so the explanation is grounded in
        actual content, not generic filler text.
        """
        percentage = (score / total * 100) if total > 0 else 0

        question_explanations = {}
        recommendations = []

        for g in graded_questions:
            q_id = g["id"]
            correct_idx = g["correct_answer"]
            correct_text = g["options"][correct_idx] if 0 <= correct_idx < len(g["options"]) else "Unknown Option"
            source = g.get("source_sentence", "").strip()

            if g["is_correct"]:
                explanation = f"Correct! '{correct_text}' is right."
                if source:
                    explanation += f" As your notes state: \"{source}\""
                question_explanations[q_id] = explanation
            else:
                user_idx = g["user_answer"]
                user_text = g["options"][user_idx] if 0 <= user_idx < len(g["options"]) else "None / Unanswered"
                explanation = (
                    f"Incorrect. You chose '{user_text}', but the correct answer is '{correct_text}'."
                )
                if source:
                    explanation += f" Your notes say: \"{source}\""
                question_explanations[q_id] = explanation

                recommendations.append(f"Review this fact again: \"{source if source else correct_text}\"")

        if not recommendations:
            if percentage == 100:
                recommendations.append("Excellent work! Advance to more complex study materials.")
            else:
                recommendations.append("Re-read the provided study guide and try the quiz once more.")
        else:
            recommendations = list(dict.fromkeys(recommendations))

        if percentage == 100:
            overall_feedback = "Perfect score! You have completely mastered these study materials. Excellent retention!"
        elif percentage >= 75:
            overall_feedback = "Great job! You have a solid grasp of most concepts. Just brush up on a few minor points."
        elif percentage >= 50:
            overall_feedback = "Good effort. You understand the core ideas but need additional review on definitions."
        else:
            overall_feedback = "It looks like you're struggling with these terms. We recommend re-reading the study notes carefully and retaking the quiz."

        return {
            "overall_feedback": overall_feedback,
            "recommendations": recommendations,
            "question_explanations": question_explanations
        }
