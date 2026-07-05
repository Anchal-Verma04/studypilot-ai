from src.agents.base_agent import BaseAgent
from src.skills.db_store import DBStore

class ProgressTrackerAgent(BaseAgent):
    """
    Agent responsible for tracking student progress, updating databases, and analyzing performance trends.
    """

    def __init__(self, db_store: DBStore):
        super().__init__(
            name="Progress Tracker Agent",
            role_description="Logs scores, analyzes historical trends, and delivers progress metrics.",
            system_prompt="You are a data-driven student success coach. Analyze score history and output a progress report.",
            skills=[db_store]
        )
        self.db = db_store

    def execute(self, action: str, **kwargs) -> dict:
        """
        Processes commands: 'log_attempt', 'get_dashboard_analytics', or 'get_history'.
        """
        if action == "log_attempt":
            return self._log_attempt(
                quiz_id=kwargs.get("quiz_id"),
                score=kwargs.get("score"),
                total_questions=kwargs.get("total_questions"),
                answers=kwargs.get("answers"),
                feedback=kwargs.get("feedback"),
                detailed_grading=kwargs.get("detailed_grading")
            )
        elif action == "get_dashboard_analytics":
            return self._get_dashboard_analytics()
        elif action == "get_history":
            return {"history": self.db.get_attempts_history()}
        else:
            return {"error": f"Unknown action: {action}"}

    def _log_attempt(self, quiz_id: str, score: float, total_questions: int, answers: dict, feedback: str, detailed_grading: dict = None) -> dict:
        attempt = self.db.save_attempt(quiz_id, score, total_questions, answers, feedback, detailed_grading)
        return {
            "success": True,
            "attempt": attempt
        }

    def _get_dashboard_analytics(self) -> dict:
        history = self.db.get_attempts_history()
        
        if not history:
            return {
                "total_attempts": 0,
                "average_score": 0,
                "learning_trend": "No attempts recorded yet. Paste some notes and take a quiz to get started!",
                "strengths": [],
                "focus_areas": [],
                "chart_data": []
            }

        total_attempts = len(history)
        total_percentage = sum(item["percentage"] for item in history)
        avg_percentage = round(total_percentage / total_attempts, 2)

        # Build chart coordinates: x = date, y = percentage
        chart_data = []
        for idx, item in enumerate(history):
            chart_data.append({
                "attempt_num": idx + 1,
                "percentage": item["percentage"],
                "note_title": item["note_title"],
                "date": item["created_at"][:10]  # Just YYYY-MM-DD
            })

        # Heuristic strengths & focus areas based on topics
        strengths = set()
        focus_areas = set()

        for item in history:
            topics = item.get("topics", [])
            is_perfect = (item["percentage"] == 100)
            
            for t in topics:
                if is_perfect:
                    strengths.add(t)
                else:
                    focus_areas.add(t)

        # Clean focus areas (remove from focus areas if user got 100% on it later)
        # But for this simple analytics, let's keep it simple:
        focus_areas = focus_areas - strengths

        # Deduce learning trend
        if total_attempts == 1:
            learning_trend = "Starting strong! Keep taking quizzes to track your learning velocity."
        else:
            last_percentage = history[-1]["percentage"]
            prev_percentage = history[-2]["percentage"]
            diff = last_percentage - prev_percentage
            
            if diff > 0:
                learning_trend = f"Upward trend! Your score increased by {round(diff, 1)}% in your last quiz."
            elif diff < 0:
                learning_trend = f"Slight dip by {round(abs(diff), 1)}% on your last attempt. Review the focus areas below."
            else:
                learning_trend = "Steady progress. Consistency is key to long-term memory retention!"

        return {
            "total_attempts": total_attempts,
            "average_score": avg_percentage,
            "learning_trend": learning_trend,
            "strengths": list(strengths)[:4],
            "focus_areas": list(focus_areas)[:4],
            "chart_data": chart_data
        }
