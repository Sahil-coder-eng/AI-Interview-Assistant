# ============================================================
#  answer_evaluator.py — AI-powered answer evaluation via Gemini
# ============================================================

import json
import re
from ai_client import AIClient
from config import OPENROUTER_MODEL_INTERVIEW, EVALUATION_CRITERIA


class AnswerEvaluator:
    """
    Evaluates a candidate's interview answer using the Gemini API.

    Scoring is done across five criteria (each 0–10):
      - Technical Accuracy
      - Problem Solving
      - Communication Skills
      - Completeness
      - Confidence

    Overall score = weighted average scaled to 100.
    """

    # Weights for each criterion (must sum to 1.0)
    CRITERION_WEIGHTS = {
        "Technical Accuracy": 0.30,
        "Problem Solving": 0.25,
        "Communication Skills": 0.20,
        "Completeness": 0.15,
        "Confidence": 0.10,
    }

    def __init__(self):
        """Configure the unified AI client."""
        self.client = AIClient()

    # ── Public API ──────────────────────────────────────────────────────────

    def evaluate(self, question: str, answer: str, context: dict = None) -> dict:
        """
        Evaluate a single question-answer pair.

        Args:
            question (str): The interview question asked.
            answer (str): The candidate's response.
            context (dict): Optional resume context for relevance scoring.

        Returns:
            dict: {
                scores: {criterion: score},
                overall_score: float (0–100),
                feedback: str,
                strengths: list,
                improvements: list,
                model_answer_hint: str
            }
        """
        if not answer or not answer.strip():
            return self._empty_answer_result()

        prompt = self._build_evaluation_prompt(question, answer, context)
        try:
            response_text = self.client.generate_content(prompt, model_name=OPENROUTER_MODEL_INTERVIEW)
            return self._parse_evaluation(response_text)
        except Exception as e:
            print(f"[AnswerEvaluator] Error: {e}")
            return self._fallback_evaluation()

    def evaluate_session(self, qa_pairs: list[dict]) -> dict:
        """
        Evaluate all Q&A pairs from an interview session.

        Args:
            qa_pairs: List of {question, answer, category, difficulty} dicts.

        Returns:
            dict: Aggregated session results with per-question and overall scores.
        """
        results = []
        for qa in qa_pairs:
            eval_result = self.evaluate(
                qa.get("question", ""),
                qa.get("answer", ""),
            )
            eval_result["question"] = qa.get("question", "")
            eval_result["answer"] = qa.get("answer", "")
            eval_result["category"] = qa.get("category", "General")
            eval_result["difficulty"] = qa.get("difficulty", "Intermediate")
            results.append(eval_result)

        # Aggregate
        if not results:
            return {"results": [], "aggregate": {}}

        all_scores = [r["overall_score"] for r in results]
        category_scores = self._aggregate_by_category(results)
        criterion_scores = self._aggregate_by_criterion(results)

        return {
            "results": results,
            "aggregate": {
                "overall_score": round(sum(all_scores) / len(all_scores), 1),
                "max_score": max(all_scores),
                "min_score": min(all_scores),
                "category_scores": category_scores,
                "criterion_scores": criterion_scores,
                "total_questions": len(results),
            },
        }

    # ── Prompt Builder ──────────────────────────────────────────────────────

    def _build_evaluation_prompt(
        self, question: str, answer: str, context: dict
    ) -> str:
        """Construct the Gemini evaluation prompt."""
        context_str = ""
        if context:
            skills = ", ".join(context.get("skills", [])[:15])
            context_str = f"\nCandidate's known skills: {skills}"

        return f"""
You are an expert technical interviewer evaluating a candidate's response.{context_str}

Interview Question:
"{question}"

Candidate's Answer:
"{answer}"

Evaluate the answer on EXACTLY these five criteria, each scored 1–10 (integers only):
1. Technical Accuracy — Is the information factually correct?
2. Problem Solving — Does the candidate show a structured approach?
3. Communication Skills — Is the answer clear, coherent, and well-structured?
4. Completeness — Does the answer cover all key aspects?
5. Confidence — Does the answer read with conviction and directness?

Return ONLY valid JSON. No markdown, no extra text. Format:
{{
  "scores": {{
    "Technical Accuracy": <int>,
    "Problem Solving": <int>,
    "Communication Skills": <int>,
    "Completeness": <int>,
    "Confidence": <int>
  }},
  "feedback": "<2–3 sentence overall feedback>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<area 1>", "<area 2>"],
  "model_answer_hint": "<one sentence on what an ideal answer would include>"
}}
"""

    # ── Response Parser ─────────────────────────────────────────────────────

    def _parse_evaluation(self, raw_text: str) -> dict:
        """Parse the Gemini JSON response into a clean evaluation dict."""
        cleaned = re.sub(r"```(?:json)?", "", raw_text).strip()

        try:
            data = json.loads(cleaned)
            raw_scores = data.get("scores", {})

            # Clamp scores to 1–10
            scores = {
                criterion: max(1, min(10, int(raw_scores.get(criterion, 5))))
                for criterion in EVALUATION_CRITERIA
            }

            # Weighted overall score (0–100)
            overall = sum(
                scores[c] * self.CRITERION_WEIGHTS.get(c, 0.2)
                for c in scores
            ) * 10

            return {
                "scores": scores,
                "overall_score": round(overall, 1),
                "feedback": data.get("feedback", "No feedback provided."),
                "strengths": data.get("strengths", []),
                "improvements": data.get("improvements", []),
                "model_answer_hint": data.get("model_answer_hint", ""),
            }
        except (json.JSONDecodeError, ValueError):
            return self._fallback_evaluation()

    # ── Aggregation Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _aggregate_by_category(results: list) -> dict:
        """Compute average overall score per question category."""
        from collections import defaultdict
        cat_totals = defaultdict(list)
        for r in results:
            cat_totals[r["category"]].append(r["overall_score"])
        return {
            cat: round(sum(scores) / len(scores), 1)
            for cat, scores in cat_totals.items()
        }

    @staticmethod
    def _aggregate_by_criterion(results: list) -> dict:
        """Compute average score per evaluation criterion across all questions."""
        from collections import defaultdict
        criterion_totals = defaultdict(list)
        for r in results:
            for criterion, score in r.get("scores", {}).items():
                criterion_totals[criterion].append(score)
        return {
            c: round(sum(vals) / len(vals), 1)
            for c, vals in criterion_totals.items()
        }

    # ── Fallbacks ───────────────────────────────────────────────────────────

    @staticmethod
    def _empty_answer_result() -> dict:
        """Return zeroed result for skipped/empty answers."""
        return {
            "scores": {c: 0 for c in EVALUATION_CRITERIA},
            "overall_score": 0.0,
            "feedback": "No answer was provided for this question.",
            "strengths": [],
            "improvements": ["Attempt every question — even a partial answer is scored."],
            "model_answer_hint": "",
        }

    @staticmethod
    def _fallback_evaluation() -> dict:
        """Return a neutral mid-score if the API call fails."""
        return {
            "scores": {c: 5 for c in EVALUATION_CRITERIA},
            "overall_score": 50.0,
            "feedback": "Evaluation unavailable due to a service error. Score defaulted to 50.",
            "strengths": [],
            "improvements": [],
            "model_answer_hint": "",
        }
