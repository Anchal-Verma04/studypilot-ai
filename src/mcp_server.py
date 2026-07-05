import sys
import json
import os
import traceback

# Ensure Capstone directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.skills.db_store import DBStore
from src.agents.notes_extractor_agent import NotesExtractorAgent
from src.agents.quiz_generator_agent import QuizGeneratorAgent
from src.agents.grader_agent import GraderAgent
from src.agents.progress_tracker_agent import ProgressTrackerAgent

# Setup DB store & Agents
db_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "db.json")
db = DBStore(db_path=db_path)

extractor = NotesExtractorAgent()
quiz_gen = QuizGeneratorAgent()
grader = GraderAgent()
tracker = ProgressTrackerAgent(db)

def respond(response_id, result=None, error=None):
    """Writes a standard JSON-RPC response to stdout."""
    res = {"jsonrpc": "2.0", "id": response_id}
    if error:
        res["error"] = error
    else:
        res["result"] = result
    
    sys.stdout.write(json.dumps(res) + "\n")
    sys.stdout.flush()

def log_stderr(message):
    """Logs messages to stderr so they don't corrupt stdout JSON-RPC pipe."""
    sys.stderr.write(f"[MCP Logs] {message}\n")
    sys.stderr.flush()

def handle_tools_list(request_id):
    tools = [
        {
            "name": "extract_notes",
            "description": "Validates, sanitizes, and extracts key terms, topics, and summary from raw study notes.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The raw study notes text to process."},
                    "title": {"type": "string", "description": "Optional title for the study notes."}
                },
                "required": ["content"]
            }
        },
        {
            "name": "generate_quiz",
            "description": "Generates multiple choice questions based on a previously extracted note ID.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "note_id": {"type": "string", "description": "The target study note ID."}
                },
                "required": ["note_id"]
            }
        },
        {
            "name": "grade_answers",
            "description": "Evaluates submitted answers, updates history, and returns feedback details.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "quiz_id": {"type": "string", "description": "The target quiz ID."},
                    "answers": {
                        "type": "object",
                        "description": "Key-value map matching question ID to chosen option index, e.g. {'q_1': 1, 'q_2': 0}."
                    }
                },
                "required": ["quiz_id", "answers"]
            }
        },
        {
            "name": "get_analytics",
            "description": "Retrieves the student progress charts metrics and score history logs.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
    ]
    respond(request_id, {"tools": tools})

def handle_tools_call(request_id, params):
    name = params.get("name")
    arguments = params.get("arguments", {})

    log_stderr(f"Invoking tool call: {name}")

    try:
        if name == "extract_notes":
            content = arguments.get("content", "").strip()
            title = arguments.get("title", "").strip()
            if not content:
                respond(request_id, error={"code": -32602, "message": "Content cannot be empty."})
                return

            result = extractor.execute(content)
            if result.get("success") and not result.get("security_flag"):
                note_record = db.save_notes(title=title or result.get("title"), raw_content=result.get("sanitized_content"), topics=result.get("topics", []))
                result["note_id"] = note_record["id"]
            
            respond(request_id, {
                "content": [{"type": "text", "text": json.dumps(result)}]
            })

        elif name == "generate_quiz":
            note_id = arguments.get("note_id")
            notes_list = db._load().get("notes", [])
            selected_note = next((n for n in notes_list if n["id"] == note_id), None)
            
            if not selected_note:
                respond(request_id, error={"code": -32602, "message": f"Note with ID '{note_id}' not found."})
                return

            payload = {
                "title": selected_note["title"],
                "topics": selected_note["topics"],
                "terms": selected_note.get("terms", [])
            }
            if not payload["terms"]:
                temp_extraction = extractor.execute(selected_note["raw_content"])
                payload["terms"] = temp_extraction.get("terms", [])
                payload["topics"] = temp_extraction.get("topics", [])

            questions = quiz_gen.execute(payload)
            quiz_record = db.save_quiz(note_id, questions)
            
            respond(request_id, {
                "content": [{"type": "text", "text": json.dumps({
                    "success": True,
                    "quiz_id": quiz_record["id"],
                    "questions": questions
                })}]
            })

        elif name == "grade_answers":
            quiz_id = arguments.get("quiz_id")
            user_answers = arguments.get("answers", {})

            quiz = db.get_quiz(quiz_id)
            if not quiz:
                respond(request_id, error={"code": -32602, "message": f"Quiz with ID '{quiz_id}' not found."})
                return

            grading = grader.execute(quiz, user_answers)
            tracker.execute(
                action="log_attempt",
                quiz_id=quiz_id,
                score=grading["score"],
                total_questions=grading["total_questions"],
                answers=user_answers,
                feedback=grading["overall_feedback"]
            )

            respond(request_id, {
                "content": [{"type": "text", "text": json.dumps({"success": True, "grading": grading})}]
            })

        elif name == "get_analytics":
            analytics = tracker.execute(action="get_dashboard_analytics")
            history = tracker.execute(action="get_history")
            respond(request_id, {
                "content": [{"type": "text", "text": json.dumps({
                    "success": True,
                    "analytics": analytics,
                    "history": history.get("history", [])
                })}]
            })
        else:
            respond(request_id, error={"code": -32601, "message": f"Unknown tool: {name}"})
    
    except Exception as e:
        log_stderr(f"Error handling tool call: {str(e)}\n{traceback.format_exc()}")
        respond(request_id, error={"code": -32603, "message": f"Error running agent tool: {str(e)}"})

def main():
    log_stderr("StudyPilot AI MCP Server started in stdio mode.")
    
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                respond(req_id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "StudyPilot-AI-Server",
                        "version": "1.0.0"
                    }
                })
            elif method == "tools/list":
                handle_tools_list(req_id)
            elif method == "tools/call":
                handle_tools_call(req_id, params)
            elif method.startswith("$/"):
                # Ignore notifications
                continue
            else:
                respond(req_id, error={"code": -32601, "message": f"Method not found: {method}"})
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}})+"\n")
            sys.stdout.flush()
        except Exception as e:
            log_stderr(f"Global server loop error: {str(e)}")

if __name__ == "__main__":
    main()
