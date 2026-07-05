import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    """
    ADK BaseAgent defining agent characteristics, LLM integration, and execution hooks.
    """

    def __init__(self, name: str, role_description: str, system_prompt: str, skills: list = None):
        self.name = name
        self.role_description = role_description
        self.system_prompt = system_prompt
        self.skills = skills or []
        
        # Load API key and initialize Gemini client if possible
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.use_simulation = True

        if self.api_key and self.api_key.strip():
            try:
                # Official google-genai client initialization
                # By default, it will look up GEMINI_API_KEY from environment
                self.client = genai.Client(api_key=self.api_key)
                self.use_simulation = False
                print(f"[{self.name}] Gemini Client successfully initialized.")
            except Exception as e:
                print(f"[{self.name}] Failed to initialize Gemini client ({e}). Falling back to simulation mode.")
                self.use_simulation = True
        else:
            print(f"[{self.name}] No GEMINI_API_KEY detected. Running in high-fidelity Simulation Mode.")

    def run_llm_generation(self, prompt: str, schema=None, model: str = "gemini-2.5-flash") -> str:
        """
        Executes generation against the Gemini API if configured; otherwise,
        throws an exception or is caught by subclasses to generate high-quality simulations.
        """
        if self.use_simulation or not self.client:
            raise NotImplementedError("Running simulation generation. Must be overridden by subclasses.")
            
        try:
            # Prepare configuration
            config = types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=0.2,
            )
            
            # Setup structural JSON response if a Pydantic schema is passed
            if schema:
                config.response_mime_type = "application/json"
                config.response_schema = schema

            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"[{self.name}] API Generation failed: {e}. Reverting to simulation fallback.")
            raise e
            
    def execute(self, *args, **kwargs):
        """
        Main execution hook that sub-agents implement.
        """
        raise NotImplementedError("Each agent must implement its own execute logic.")
