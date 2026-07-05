import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure the root Capstone directory is in Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.skills.db_store import DBStore
from src.agents.notes_extractor_agent import NotesExtractorAgent
from src.agents.quiz_generator_agent import QuizGeneratorAgent
from src.agents.grader_agent import GraderAgent
from src.agents.progress_tracker_agent import ProgressTrackerAgent

load_dotenv()

# Initialize Flask. Serve static assets from 'src/public' at root URL path
app = Flask(__name__, static_folder="public", static_url_path="")
CORS(app)

# Initialize single DB store instance and Agents
db_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "db.json")
db = DBStore(db_path=db_path)

extractor_agent = NotesExtractorAgent()
quiz_agent = QuizGeneratorAgent()
grader_agent = GraderAgent()
tracker_agent = ProgressTrackerAgent(db)

@app.route("/")
def serve_index():
    """Serves the dashboard home page."""
    return app.send_static_file("index.html")

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint containing mode indicator."""
    return jsonify({
        "status": "healthy",
        "llm_mode": "API (Live Gemini)" if not extractor_agent.use_simulation else "High-Fidelity Simulation",
        "api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
        "database_path": db.db_path
    })

@app.route("/api/notes/extract", methods=["POST"])
def extract_notes():
    """Sanitizes and extracts study notes."""
    try:
        data = request.json or {}
        content = data.get("content", "").strip()
        title = data.get("title", "").strip()

        if not content:
            return jsonify({"success": False, "error": "Study notes content cannot be empty."}), 400

        # Execute Extractor Agent
        result = extractor_agent.execute(content)
        
        # If extraction was successful and it wasn't flagged for safety, persist notes reference
        if result.get("success") and not result.get("security_flag"):
            note_record = db.save_notes(
                title=title or result.get("title"),
                raw_content=result.get("sanitized_content"),
                topics=result.get("topics", [])
            )
            result["note_id"] = note_record["id"]
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": f"An error occurred during note extraction: {str(e)}"}), 500

@app.route("/api/quiz/generate", methods=["POST"])
def generate_quiz():
    """Generates multiple choice questions from notes metadata."""
    try:
        data = request.json or {}
        note_id = data.get("note_id")
        
        # Look up notes content
        notes_list = db._load().get("notes", [])
        selected_note = next((n for n in notes_list if n["id"] == note_id), None)
        
        if not selected_note:
            return jsonify({"success": False, "error": "Study notes record not found."}), 404

        # Prepare payload for Quiz Agent
        payload = {
            "title": selected_note["title"],
            "topics": selected_note["topics"],
            "terms": selected_note.get("terms", []),
            "sanitized_content": selected_note.get("raw_content", "")
        }
        
        # If no terms existed in db notes, try to extract them dynamically
        if not payload["terms"]:
            temp_extraction = extractor_agent.execute(selected_note["raw_content"])
            payload["terms"] = temp_extraction.get("terms", [])
            payload["topics"] = temp_extraction.get("topics", [])
            
        # Execute Quiz Generator Agent
        questions = quiz_agent.execute(payload)
        
        # Save generated quiz
        quiz_record = db.save_quiz(note_id, questions)
        
        return jsonify({
            "success": True,
            "quiz_id": quiz_record["id"],
            "questions": questions
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"An error occurred during quiz generation: {str(e)}"}), 500

@app.route("/api/quiz/grade", methods=["POST"])
def grade_quiz():
    """Grades submitted answers, logs scores, and produces tutor advice."""
    try:
        data = request.json or {}
        quiz_id = data.get("quiz_id")
        user_answers = data.get("answers", {})  # map: q_id -> chosen index
        
        # Look up quiz
        quiz = db.get_quiz(quiz_id)
        if not quiz:
            return jsonify({"success": False, "error": "Quiz not found."}), 404

        # Execute Grader Agent
        grading = grader_agent.execute(quiz, user_answers)

        # Execute Tracker Agent to persist progress attempt
        tracker_agent.execute(
            action="log_attempt",
            quiz_id=quiz_id,
            score=grading["score"],
            total_questions=grading["total_questions"],
            answers=user_answers,
            feedback=grading["overall_feedback"],
            detailed_grading=grading
        )

        return jsonify({
            "success": True,
            "grading": grading
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"An error occurred during grading: {str(e)}"}), 500

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Fetches progress trackers details."""
    try:
        analytics = tracker_agent.execute(action="get_dashboard_analytics")
        history = tracker_agent.execute(action="get_history")
        
        return jsonify({
            "success": True,
            "analytics": analytics,
            "history": history.get("history", [])
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"An error occurred fetching metrics: {str(e)}"}), 500

if __name__ == "__main__":
    print("--------------------------------------------------")
    print("StudyPilot AI Server Initializing...")
    print("Serving Port: 3000")
    print("Local URL:    http://localhost:3000")
    print("--------------------------------------------------")
    app.run(host="0.0.0.0", port=3000, debug=True)
