import re
import html

class SafetyFilter:
    """
    Skill for sanitizing inputs, preventing XSS, and detecting prompt injection attempts
    in untrusted study notes.
    """

    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        r"(ignore|override|bypass)\s+(the\s+)?(previous|above|system)?\s*(instruction|prompt|rule|direction)",
        r"you\s+are\s+now\s+a\s+",
        r"new\s+role\s*:",
        r"system\s*override",
        r"ignore\s+all\s+constraints",
        r"do\s+not\s+grade",
        r"give\s+me\s+(a\s+)?perfect\s+score",
        r"ignore\s+grading\s+criteria",
        r"delete\s+all\s+files",
        r"format\s+your\s+output\s+as\s+follows\s*:\s*ignore"
    ]

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Cleanses HTML to remove harmful script tags and event handlers,
        while preserving mathematical symbols and chemical equations (like ->) for LLM parsing.
        """
        if not text:
            return ""
        # Scrub harmful script structures first
        cleaned = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r"on\w+\s*=\s*['\"].*?['\"]", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"on\w+\s*=\s*[^>\s]+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"javascript:\s*[^>\s]+", "", cleaned, flags=re.IGNORECASE)
        return cleaned

    @classmethod
    def analyze_for_prompt_injection(cls, text: str) -> dict:
        """
        Analyzes the text for known prompt injection heuristic indicators.
        Returns a dict indicating if injection was detected and the reasons.
        """
        if not text:
            return {"is_safe": True, "reason": "Empty input"}

        detected_triggers = []
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                detected_triggers.append(pattern)

        if detected_triggers:
            return {
                "is_safe": False,
                "reason": f"Potential prompt injection detected. Matching rules: {', '.join(detected_triggers)}"
            }

        return {"is_safe": True, "reason": "Passed prompt injection heuristics"}

    @staticmethod
    def validate_size(text: str, max_chars: int = 50000) -> dict:
        """
        Ensures input text does not exceed size limits to avoid resource exhaustion.
        """
        if not text:
            return {"is_valid": True, "size": 0}
        
        size = len(text)
        if size > max_chars:
            return {
                "is_valid": False,
                "size": size,
                "reason": f"Input size ({size} characters) exceeds the safe limit of {max_chars} characters."
            }
        
        return {"is_valid": True, "size": size}
