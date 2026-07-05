# StudyPilot AI 🚀

StudyPilot AI is a secure, full-stack multi-agent study dashboard designed to transform raw, untrusted study materials into interactive quizzes, tutor assessments, and progress histories. It is built using an **Agent Development Kit (ADK) Multi-Agent** framework and is fully integrated with a **Model Context Protocol (MCP)** server architecture.

---

## 🌟 Key Architecture & Concept Mapping

The application showcases **four core concepts**:

### 1. ADK Multi-Agent System
StudyPilot AI organizes processing into specialized, cooperative agent instances extending from a standard [BaseAgent](file:///c:/Users/KIIT/Desktop/Capstone/src/agents/base_agent.py):
*   **Notes Extractor Agent** ([notes_extractor_agent.py](file:///c:/Users/KIIT/Desktop/Capstone/src/agents/notes_extractor_agent.py)): Sanitizes user materials and extracts key terminology definitions.
*   **Quiz Generator Agent** ([quiz_generator_agent.py](file:///c:/Users/KIIT/Desktop/Capstone/src/agents/quiz_generator_agent.py)): Dynamically builds distractors and formulates multiple-choice quizzes.
*   **Grader/Feedback Agent** ([grader_agent.py](file:///c:/Users/KIIT/Desktop/Capstone/src/agents/grader_agent.py)): Scores student answers and writes contextual explanations for incorrect choices.
*   **Progress Tracker Agent** ([progress_tracker_agent.py](file:///c:/Users/KIIT/Desktop/Capstone/src/agents/progress_tracker_agent.py)): Manages user score histories, builds progress coordinates, and analyzes learning trends.

### 2. Model Context Protocol (MCP) Server
An independent executable [mcp_server.py](file:///c:/Users/KIIT/Desktop/Capstone/src/mcp_server.py) implements the Model Context Protocol over a JSON-RPC stdio pipe. It registers the multi-agent system actions as tools:
*   `extract_notes`: Executes extraction and logs notes.
*   `generate_quiz`: Constructs quizzes on selected notes.
*   `grade_answers`: Evaluates student submissions.
*   `get_analytics`: Returns dashboard progress trends.

This allows external LLM clients (such as Claude Desktop, Cline, or Antigravity) to call the agents directly.

### 3. Deep Sandbox Security Features
StudyPilot AI treats pasted user text as untrusted. Safe execution is enforced in [safety_filter.py](file:///c:/Users/KIIT/Desktop/Capstone/src/skills/safety_filter.py):
*   **Prompt Injection Blockers**: Heuristic regex checks scan for behavioral overrides (e.g. *"ignore instructions"*).
*   **XSS Protection**: Complete escaping of HTML tags and script elements prevents script-injection hazards.
*   **Size Validation**: Restricts input to `50,000` characters to prevent buffer issues or cost exhaustion.

### 4. Agent Skills
Modular utility libraries represent distinct agent skills:
*   **Safety validation**: [safety_filter.py](file:///c:/Users/KIIT/Desktop/Capstone/src/skills/safety_filter.py)
*   **JSON database store**: [db_store.py](file:///c:/Users/KIIT/Desktop/Capstone/src/skills/db_store.py) (maintains records in a local `db.json` database file).

---

## 📂 Project Structure

```
Capstone/
├── db.json                       # Local JSON database (Auto-generated)
├── requirements.txt              # Backend python dependencies
├── README.md                     # Documentation
├── .env.example                  # Environment configuration template
└── src/
    ├── server.py                 # Core Flask backend server
    ├── mcp_server.py             # Stdio MCP tool server wrapper
    ├── test_agents.py            # Automated integration test script
    ├── agents/
    │   ├── base_agent.py         # ADK abstract agent base
    │   ├── notes_extractor_agent.py
    │   ├── quiz_generator_agent.py
    │   ├── grader_agent.py
    │   └── progress_tracker_agent.py
    ├── skills/
    │   ├── safety_filter.py      # Sanitization skill
    │   └── db_store.py           # Database storage skill
    └── public/                   # Premium UI dashboard assets
        ├── index.html            # Web markup structure
        ├── styles.css            # Custom CSS styling (dark glassmorphism)
        └── app.js                # Core frontend client scripting
```

---

## 🛠️ Installation & Setup

Ensure you have **Python 3.10+** installed on your system.

### 1. Clone & Navigate
Navigate to the project root folder:
```bash
cd c:\Users\KIIT\Desktop\Capstone
```

### 2. Install Dependencies
Install Python requirements:
```bash
pip install -r requirements.txt
```

### 3. Configure Gemini Key (Optional)
By default, the application runs immediately using a high-fidelity mock simulator (ideal for offline testing). To enable live AI integration with Google Gemini:
1.  Copy `.env.example` to `.env`:
    ```bash
    copy .env.example .env
    ```
2.  Open `.env` and add your Google Gemini API key:
    ```env
    GEMINI_API_KEY=AIzaSy...
    ```

---

## 🚀 Running the Application

### Start the Web Application
Launch the Flask server:
```bash
python src/server.py
```
*   The dashboard UI will be hosted at: **[http://localhost:3000](http://localhost:3000)**
*   API endpoints will be exposed at: `http://localhost:3000/api/*`

### Run Automated Tests
Run backend integration and safety test scripts:
```bash
python src/test_agents.py
```

### Running as an MCP Server
The MCP server communicates using JSON-RPC over `stdio`. You can integrate it directly with **Claude Desktop** by editing your `claude_desktop_config.json` configuration file:

```json
{
  "mcpServers": {
    "studypilot-ai": {
      "command": "python",
      "args": ["c:/Users/KIIT/Desktop/Capstone/src/mcp_server.py"]
    }
  }
}
```

---

## 🔄 End-to-End User Journey

1.  **Dashboard Overview**: View statistics for total quizzes taken and your average grade percentage.
2.  **Add Study Notes**: Paste study notes or textbook content in the **Study Lab**.
3.  **Safety Screening**: The **Safety Sandbox Monitor** scans your text. If a script or prompt injection attempt is detected, execution is halted. If safe, topics and terms are extracted.
4.  **Take Quiz**: Click **Generate Quiz** to compile 4 custom multiple-choice questions. Complete the quiz and submit.
5.  **Grading & Tutor Advice**: The **Feedback Hub** presents your graded scorecard, highlights correct vs wrong responses, and displays tutoring recommendations.
6.  **Progress Trend**: Review your updated score history chart on the dashboard!
