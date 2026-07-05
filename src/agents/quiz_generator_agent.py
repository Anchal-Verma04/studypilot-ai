import json
import re
import random
from src.agents.base_agent import BaseAgent

class QuizGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating structured quizzes from extracted study notes.
    """

    def __init__(self):
        system_prompt = (
            "You are a test design professor. Create a multiple-choice quiz of 3-5 questions "
            "based on the topics and terms extracted from the study notes. Output the quiz as a "
            "valid JSON array of question objects. Do not include markdown code block wrappers."
        )
        super().__init__(
            name="Quiz Generator Agent",
            role_description="Designs multiple choice quizzes based on key study terms and concepts.",
            system_prompt=system_prompt
        )

    def execute(self, extracted_notes: dict) -> list:
        """
        Generates a quiz. Uses Gemini API if configured, otherwise falls back to simulator.
        """
        terms = extracted_notes.get("terms", [])

        if not terms:
            return self._generate_default_quiz()

        if self.use_simulation:
            return self._simulate_quiz_generation(extracted_notes)
        else:
            try:
                return self._run_api_quiz_generation(extracted_notes)
            except Exception as e:
                print(f"[{self.name}] API quiz generation failed, using simulator fallback.")
                return self._simulate_quiz_generation(extracted_notes)

    def _run_api_quiz_generation(self, extracted_notes: dict) -> list:
        # Deduce target question count
        terms_len = len(extracted_notes.get("terms", []))
        target_count = 4
        if terms_len >= 5:
            target_count = 5
        elif terms_len <= 2:
            target_count = 3

        prompt = (
            f"Generate a quiz containing exactly {target_count} multiple-choice questions based on these notes:\n"
            f"Title: {extracted_notes.get('title')}\n"
            f"Topics: {', '.join(extracted_notes.get('topics', []))}\n"
            f"Key Terms:\n"
            + "\n".join([f"- {t['term']}: {t['definition']}" for t in extracted_notes.get("terms", [])]) + "\n\n"
            f"Each question must have exactly 4 options. One option must be correct.\n"
            f"Response format (must be JSON array only):\n"
            f"[\n"
            f"  {{\n"
            f"    \"id\": \"q1\",\n"
            f"    \"question\": \"Question text?\",\n"
            f"    \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"],\n"
            f"    \"answer\": 0\n"
            f"  }}\n"
            f"]"
        )
        raw_output = self.run_llm_generation(prompt)
        
        # Clean potential markdown packaging
        clean_json = re.sub(r"^```json\s*", "", raw_output.strip(), flags=re.IGNORECASE)
        clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.IGNORECASE)
        
        quiz = json.loads(clean_json)
        # Ensure ids and structures are standard
        for idx, q in enumerate(quiz):
            q["id"] = f"q_{idx + 1}"
        return quiz

    def _simulate_quiz_generation(self, extracted_notes: dict) -> list:
        """
        Comprehension-style simulation: pulls real sentences straight from the
        notes and turns them into fill-in-the-blank fact questions.
        """
        text = extracted_notes.get("sanitized_content", "")
        terms = extracted_notes.get("terms", [])

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 25]

        phrase_pool = set()
        for m in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b", text):
            phrase_pool.add(m.group(0))
        for m in re.finditer(r"\b\d[\d,.]*\s?(?:%|percent|days|years|miles|km|degrees)?\b", text):
            if len(m.group(0)) > 1:
                phrase_pool.add(m.group(0))

        target_count = 4
        if len(terms) >= 5:
            target_count = 5
        elif len(terms) <= 2:
            target_count = 3

        candidate_sentences = [s for s in sentences if any(p in s for p in phrase_pool)]
        random.shuffle(candidate_sentences)

        questions = []
        used_sentences = set()

        for sentence in candidate_sentences:
            if len(questions) >= target_count:
                break
            if sentence in used_sentences:
                continue

            matches_in_sentence = [p for p in phrase_pool if p in sentence]
            if not matches_in_sentence:
                continue
            answer_phrase = max(matches_in_sentence, key=len)

            blanked = sentence.replace(answer_phrase, "______", 1)
            question_text = f"Complete this fact from your notes: \"{blanked}\""

            distractor_pool = [p for p in phrase_pool if p != answer_phrase and p not in blanked]
            distractors = random.sample(distractor_pool, min(3, len(distractor_pool)))
            while len(distractors) < 3:
                distractors.append("Not mentioned in the notes")

            options = distractors + [answer_phrase]
            random.shuffle(options)
            correct_index = options.index(answer_phrase)

            questions.append({
                "id": f"q_{len(questions)+1}",
                "question": question_text,
                "options": options,
                "answer": correct_index,
                "source_sentence": sentence
            })
            used_sentences.add(sentence)

        if len(questions) < target_count:
            questions.extend(self._term_based_fallback(terms, target_count - len(questions)))

        return questions

    def _term_based_fallback(self, terms: list, count: int) -> list:
        """Fallback for very short notes where sentence-blanking isn't possible."""
        questions = []
        seen_defs = set()
        unique_terms = []
        for t in terms:
            if t["definition"] not in seen_defs:
                unique_terms.append(t)
                seen_defs.add(t["definition"])

        all_definitions = [t["definition"] for t in unique_terms]
        generic_fillers = [
            "Not mentioned anywhere in these notes.",
            "This is not covered in the study materials.",
            "An unrelated concept not found in the notes."
        ]

        for i, target in enumerate(unique_terms[:count]):
            distractors = [d for d in all_definitions if d != target["definition"]]
            random.shuffle(distractors)
            selected = distractors[:3]
            filler_idx = 0
            while len(selected) < 3 and filler_idx < len(generic_fillers):
                selected.append(generic_fillers[filler_idx])
                filler_idx += 1

            options = selected + [target["definition"]]
            random.shuffle(options)
            questions.append({
                "id": f"q_fallback_{i+1}",
                "question": f"Based on your notes, which best describes '{target['term']}'?",
                "options": options,
                "answer": options.index(target["definition"]),
                "source_sentence": target["definition"]
            })
        return questions
        
    def _generate_default_quiz(self) -> list:
        return [
            {
                "id": "q_1",
                "question": "What is the primary key to effective studying?",
                "options": [
                    "Passive reading of paragraphs repeatedly",
                    "Active recall and testing yourself on concepts",
                    "Highlighting the entire textbook page",
                    "Cramming the night before the examination"
                ],
                "answer": 1
            },
            {
                "id": "q_2",
                "question": "How does spaced repetition benefit long-term memory?",
                "options": [
                    "It causes rapid forgetting of useless details",
                    "It reviews information at increasing intervals to combat the forgetting curve",
                    "It guarantees 100% exam scores without effort",
                    "It helps in reading double the speed"
                ],
                "answer": 1
            }
        ]
