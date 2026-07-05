import json
import re
from src.agents.base_agent import BaseAgent
from src.skills.safety_filter import SafetyFilter

class NotesExtractorAgent(BaseAgent):
    """
    Agent responsible for safety checking and structured extraction of study notes.
    """

    def __init__(self):
        system_prompt = (
            "You are a pedagogical extraction assistant. Analyze study notes and extract "
            "main topics, a clean list of key terminology (term and definition), and a "
            "synthesized summary. Format the response as a single valid JSON object. "
            "Do not include markdown wrappers (like ```json) in your raw response."
        )
        super().__init__(
            name="Notes Extractor Agent",
            role_description="Validates safety and extracts key educational structures from notes.",
            system_prompt=system_prompt,
            skills=[SafetyFilter]
        )

    def execute(self, raw_notes: str) -> dict:
        """
        Executes the extraction pipeline: safety check -> sanitization -> AI/Simulated extraction.
        """
        # Step 1: Input size validation
        size_check = SafetyFilter.validate_size(raw_notes)
        if not size_check["is_valid"]:
            return {
                "success": False,
                "error": size_check["reason"],
                "security_flag": True
            }

        # Step 2: Prompt injection scanning
        injection_check = SafetyFilter.analyze_for_prompt_injection(raw_notes)
        if not injection_check["is_safe"]:
            return {
                "success": False,
                "error": injection_check["reason"],
                "security_flag": True
            }

        # Step 3: XSS scrubbing/Sanitization
        sanitized_notes = SafetyFilter.sanitize_text(raw_notes)

        # Step 4: Core extraction
        if self.use_simulation:
            extracted_data = self._simulate_extraction(sanitized_notes)
        else:
            try:
                extracted_data = self._run_api_extraction(sanitized_notes)
            except Exception as e:
                print(f"[{self.name}] API extraction failed, using simulation backup.")
                extracted_data = self._simulate_extraction(sanitized_notes)

        extracted_data["sanitized_content"] = sanitized_notes
        extracted_data["success"] = True
        extracted_data["security_flag"] = False
        return extracted_data

    def _run_api_extraction(self, text: str) -> dict:
        prompt = (
            f"Analyze the following study notes and extract a title, list of main topics, "
            f"key term definitions, and a general summary.\n\n"
            f"Notes:\n{text}\n\n"
            f"Response format (must be JSON only):\n"
            f"{{\n"
            f"  \"title\": \"Title of notes\",\n"
            f"  \"topics\": [\"Topic 1\", \"Topic 2\"],\n"
            f"  \"terms\": [\n"
            f"    {{\"term\": \"Term A\", \"definition\": \"Definition of A\"}}\n"
            f"  ],\n"
            f"  \"summary\": \"Concise paragraph summarizing the content.\"\n"
            f"}}"
        )
        raw_output = self.run_llm_generation(prompt)
        
        # Clean potential markdown packaging
        clean_json = re.sub(r"^```json\s*", "", raw_output.strip(), flags=re.IGNORECASE)
        clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.IGNORECASE)
        
        return json.loads(clean_json)

    def _simulate_extraction(self, text: str) -> dict:
        """
        High-fidelity heuristic simulation of key term extraction from study notes.
        """
        # Split into lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # Deduce title from the first line or a default
        title = lines[0][:60] if lines else "Study Session Notes"
        if len(title) > 50:
            title = title[:47] + "..."

        # Heuristic term extraction: look for "Term: Definition" or capitalization
        terms = []
        topics_found = set()
        
        # Extract terms with ":" or "-" separator
        for line in lines:
            # Match formats like: "Term: definition..." or "Term - definition..."
            match = re.match(r"^([\w\s\-]{3,30})[:\-]\s*(.{10,250})$", line)
            if match:
                term = match.group(1).strip()
                defn = match.group(2).strip()
                terms.append({"term": term, "definition": defn})
                # Add to topics if short
                if len(term.split()) <= 2:
                    topics_found.add(term)
        
        # If no terms found, extract multi-word key phrases with real context as definitions
        if not terms:
            phrase_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b"
            candidates = re.findall(phrase_pattern, text)
            stopword_starts = {"The", "This", "That", "With", "From", "They", "Them", "Then", "Their", "There", "It", "Its"}
            filtered = [c for c in candidates if c.split()[0] not in stopword_starts]

            phrase_counts = {}
            for c in filtered:
                phrase_counts[c] = phrase_counts.get(c, 0) + 1

            sorted_phrases = sorted(phrase_counts.keys(), key=lambda x: (-len(x.split()), -phrase_counts[x]))
            final_terms_list = []
            for phrase in sorted_phrases:
                if not any(phrase != other and phrase in other for other in final_terms_list):
                    final_terms_list.append(phrase)
                if len(final_terms_list) >= 5:
                    break

            sentences = re.split(r"(?<=[.!?])\s+", text)
            for term in final_terms_list:
                context_sentence = next((s.strip() for s in sentences if term in s), None)
                definition = context_sentence if context_sentence else f"A key concept related to {term} discussed in the study materials."
                terms.append({"term": term, "definition": definition})
                topics_found.add(term)

        # Build topics list
        topics = list(topics_found)
        if not topics:
            topics = ["General Study Content", "Key Concepts"]
        
        # Create a brief summary
        words_list = text.split()
        summary_base = " ".join(words_list[:40]) if len(words_list) > 40 else text
        summary = f"Summary of the study materials focusing on key topics including {', '.join(topics[:3])}. {summary_base}..."

        return {
            "title": title,
            "topics": topics,
            "terms": terms,
            "summary": summary
        }
