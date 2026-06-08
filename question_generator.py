# ============================================================
#  question_generator.py — AI-powered interview question generator
# ============================================================

import json
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL


class QuestionGenerator:
    """
    Generates personalised interview questions using the Gemini API
    based on the candidate's resume data, selected category, and
    desired difficulty level.
    """

    def __init__(self):
        """Configure Gemini SDK with the API key from config."""
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    # ── Public API ──────────────────────────────────────────────────────────

    def generate_questions(
        self,
        resume_data: dict,
        category: str,
        difficulty: str,
        num_questions: int = 5,
        job_role: str = "",
    ) -> list[dict]:
        """
        Generate interview questions for a candidate.

        Args:
            resume_data (dict): Structured resume data from ResumeParser.
            category (str): One of Technical / HR / Project-Based / Behavioral.
            difficulty (str): Beginner / Intermediate / Advanced.
            num_questions (int): Number of questions to generate (1–10).
            job_role (str): Target job role (optional, for role-specific Qs).

        Returns:
            list[dict]: Each dict has keys: question, category, difficulty, hint.
        """
        prompt = self._build_prompt(
            resume_data, category, difficulty, num_questions, job_role
        )
        try:
            response = self.model.generate_content(prompt)
            return self._parse_questions(response.text, category, difficulty)
        except Exception as e:
            print(f"[QuestionGenerator] Error: {e}")
            return self._fallback_questions(category, difficulty, num_questions)

    def generate_all_categories(
        self,
        resume_data: dict,
        difficulty: str,
        num_per_category: int = 3,
        job_role: str = "",
    ) -> dict:
        """
        Generate questions for all four standard categories in one call.

        Returns:
            dict: { category_name: [question_dicts] }
        """
        categories = ["Technical", "HR / Behavioral", "Project-Based", "Behavioral"]
        all_questions = {}
        for cat in categories:
            questions = self.generate_questions(
                resume_data, cat, difficulty, num_per_category, job_role
            )
            all_questions[cat] = questions
        return all_questions

    def generate_profile_summary(self, resume_data: dict) -> str:
        """
        Ask Gemini to write a professional summary for the candidate
        based on the extracted resume information.
        """
        skills = ", ".join(resume_data.get("skills", [])[:20])
        experience_snippet = resume_data.get("experience", "")[:800]
        education_snippet = resume_data.get("education", "")[:400]

        prompt = f"""
You are a professional career coach. Write a concise, compelling 3–5 sentence professional 
profile summary for a candidate based on the following resume information.

Skills detected: {skills}
Experience section: {experience_snippet}
Education: {education_snippet}

Write in third person. Focus on strengths, key technologies, and career direction.
Do NOT make up specific company names or dates not mentioned above.
Return ONLY the summary paragraph.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Profile summary unavailable. Error: {e}"

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _build_prompt(
        self,
        resume_data: dict,
        category: str,
        difficulty: str,
        num_questions: int,
        job_role: str,
    ) -> str:
        """Build the Gemini prompt for question generation."""
        skills = ", ".join(resume_data.get("skills", [])[:25])
        projects_snippet = resume_data.get("projects", "")[:600]
        experience_snippet = resume_data.get("experience", "")[:600]
        role_line = f"Target Job Role: {job_role}" if job_role else ""

        return f"""
You are an expert technical interviewer. Generate exactly {num_questions} interview questions.

Category: {category}
Difficulty: {difficulty}
{role_line}

Candidate Profile:
- Skills & Technologies: {skills}
- Experience Summary: {experience_snippet[:300]}
- Projects: {projects_snippet[:300]}

Requirements:
1. Questions must be tailored to the candidate's actual skills.
2. Match difficulty level precisely:
   - Beginner: conceptual, definitions, basic usage
   - Intermediate: design decisions, trade-offs, moderate coding
   - Advanced: system design, optimisation, architecture, edge cases
3. For "Project-Based": reference the candidate's projects.
4. For "HR / Behavioral": use STAR-format prompts.
5. Return ONLY a valid JSON array — no markdown fences, no extra text.

JSON format:
[
  {{
    "question": "Full question text here",
    "hint": "Brief hint or what a great answer covers (1 sentence)",
    "expected_duration": "30-60 seconds"
  }}
]
"""

    def _parse_questions(
        self, raw_text: str, category: str, difficulty: str
    ) -> list[dict]:
        """
        Parse Gemini's JSON response into a list of question dicts.
        Falls back to regex extraction if JSON parsing fails.
        """
        # Strip potential markdown code fences
        cleaned = re.sub(r"```(?:json)?", "", raw_text).strip()

        try:
            items = json.loads(cleaned)
            return [
                {
                    "question": item.get("question", ""),
                    "hint": item.get("hint", ""),
                    "expected_duration": item.get("expected_duration", "60 seconds"),
                    "category": category,
                    "difficulty": difficulty,
                }
                for item in items
                if item.get("question")
            ]
        except json.JSONDecodeError:
            # Fallback: extract numbered questions with regex
            questions = re.findall(r"\d+[\.\)]\s+(.+?)(?=\d+[\.\)]|$)", cleaned, re.DOTALL)
            return [
                {
                    "question": q.strip(),
                    "hint": "",
                    "expected_duration": "60 seconds",
                    "category": category,
                    "difficulty": difficulty,
                }
                for q in questions
                if len(q.strip()) > 10
            ]

    @staticmethod
    def _fallback_questions(category: str, difficulty: str, n: int) -> list[dict]:
        """Return generic placeholder questions if the API call fails."""
        generic = {
            "Technical": [
                "Explain the difference between a list and a tuple in Python.",
                "What is REST API and how does it differ from GraphQL?",
                "How does garbage collection work in Java?",
                "Explain the concept of Big-O notation with an example.",
                "What are design patterns? Name three common ones.",
            ],
            "HR / Behavioral": [
                "Tell me about yourself and your background.",
                "What is your greatest professional achievement?",
                "Describe a challenge you faced and how you overcame it.",
                "Where do you see yourself in 5 years?",
                "Why do you want to work here?",
            ],
            "Project-Based": [
                "Describe your most technically challenging project.",
                "What tech stack did you use in your latest project and why?",
                "How did you handle version control in your team projects?",
                "Describe a bug you spent the most time fixing.",
                "How did you approach testing in your projects?",
            ],
            "Behavioral": [
                "Tell me about a time you worked in a team under pressure.",
                "How do you prioritise tasks when deadlines conflict?",
                "Describe a situation where you showed leadership.",
                "How do you handle constructive criticism?",
                "Tell me about a time you learned something new quickly.",
            ],
        }
        questions = generic.get(category, generic["Technical"])
        return [
            {
                "question": q,
                "hint": "",
                "expected_duration": "60 seconds",
                "category": category,
                "difficulty": difficulty,
            }
            for q in questions[:n]
        ]
