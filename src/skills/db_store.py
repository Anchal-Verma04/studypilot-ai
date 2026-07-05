import os
import json
import time
from datetime import datetime

class DBStore:
    """
    Skill for persisting study logs, quiz attempts, and student progress to a local JSON file.
    """

    def __init__(self, db_path: str = "db.json"):
        # Put the database in the root workspace folder
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        if not os.path.exists(self.db_path):
            initial_data = {
                "notes": [],
                "quizzes": [],
                "attempts": []
            }
            self._save(initial_data)

    def _load(self) -> dict:
        try:
            if not os.path.exists(self.db_path):
                self._initialize_db()
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Return fresh dictionary if reading fails (fallback)
            return {"notes": [], "quizzes": [], "attempts": []}

    def _save(self, data: dict):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving database: {e}")

    def save_notes(self, title: str, raw_content: str, topics: list) -> dict:
        data = self._load()
        note_id = f"note_{int(time.time())}"
        note_record = {
            "id": note_id,
            "title": title or f"Study Note {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "raw_content": raw_content,
            "topics": topics,
            "created_at": datetime.now().isoformat()
        }
        data["notes"].append(note_record)
        self._save(data)
        return note_record

    def save_quiz(self, note_id: str, questions: list) -> dict:
        data = self._load()
        quiz_id = f"quiz_{int(time.time())}"
        quiz_record = {
            "id": quiz_id,
            "note_id": note_id,
            "questions": questions,  # list of {id, question, options: [], answer}
            "created_at": datetime.now().isoformat()
        }
        data["quizzes"].append(quiz_record)
        self._save(data)
        return quiz_record

    def get_quiz(self, quiz_id: str) -> dict:
        data = self._load()
        for quiz in data.get("quizzes", []):
            if quiz["id"] == quiz_id:
                return quiz
        return None

    def save_attempt(self, quiz_id: str, score: float, total_questions: int, answers: dict, feedback: str, detailed_grading: dict = None) -> dict:
        data = self._load()
        attempt_id = f"attempt_{int(time.time())}"
        
        # Calculate percentage
        percentage = (score / total_questions * 100) if total_questions > 0 else 0
        
        attempt_record = {
            "id": attempt_id,
            "quiz_id": quiz_id,
            "score": score,
            "total_questions": total_questions,
            "percentage": round(percentage, 2),
            "answers": answers,  # user submitted answers map: question_id -> user_answer
            "feedback": feedback,
            "detailed_grading": detailed_grading or {},
            "created_at": datetime.now().isoformat()
        }
        data["attempts"].append(attempt_record)
        self._save(data)
        return attempt_record

    def get_attempts_history(self) -> list:
        data = self._load()
        # Enrich attempts with quiz/note details if available
        attempts = data.get("attempts", [])
        quizzes = {q["id"]: q for q in data.get("quizzes", [])}
        notes = {n["id"]: n for n in data.get("notes", [])}

        history = []
        for attempt in attempts:
            quiz = quizzes.get(attempt["quiz_id"], {})
            note = notes.get(quiz.get("note_id"), {})
            history.append({
                "id": attempt["id"],
                "quiz_id": attempt["quiz_id"],
                "score": attempt["score"],
                "total_questions": attempt["total_questions"],
                "percentage": attempt["percentage"],
                "feedback": attempt["feedback"],
                "created_at": attempt["created_at"],
                "note_title": note.get("title", "Unknown Source Notes"),
                "note_content": note.get("raw_content", "No notes content available."),
                "topics": note.get("topics", []),
                "questions": quiz.get("questions", []),
                "answers": attempt.get("answers", {}),
                "detailed_grading": attempt.get("detailed_grading", {})
            })
        
        # Sort chronologically
        history.sort(key=lambda x: x["created_at"])
        return history
