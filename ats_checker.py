# ============================================================
#  ats_checker.py — ATS Score Calculation & Suggestions
# ============================================================

import re
from config import ATS_KEYWORDS, ATS_SCORING_WEIGHTS


class ATSChecker:
    """
    Calculates an ATS (Applicant Tracking System) compatibility score
    for a resume based on keyword presence, structure, and formatting.

    Score breakdown (out of 100):
      - Keyword match by category  : 70 points
      - Document structure          : 20 points
      - Formatting quality          : 10 points
    """

    # Required structural sections for a strong ATS score
    REQUIRED_SECTIONS = ["experience", "education", "skills", "summary"]
    PREFERRED_SECTIONS = ["projects", "certifications", "achievements"]

    def __init__(self, resume_data: dict):
        """
        Args:
            resume_data (dict): Structured data returned by ResumeParser.parse()
        """
        self.resume_data = resume_data
        self.raw_text = resume_data.get("raw_text", "").lower()
        self.found_skills = {s.lower() for s in resume_data.get("skills", [])}

    # ── Public API ──────────────────────────────────────────────────────────

    def calculate_score(self) -> dict:
        """
        Run all scoring sub-routines and return a comprehensive result dict.

        Returns:
            dict: {
                overall_score, keyword_score, structure_score, format_score,
                category_scores, missing_skills, present_skills,
                suggestions, grade, word_count_ok
            }
        """
        keyword_score, category_scores = self._score_keywords()
        structure_score = self._score_structure()
        format_score = self._score_formatting()

        # Weighted overall (out of 100)
        overall_score = round(
            keyword_score * 0.70 + structure_score * 0.20 + format_score * 0.10, 1
        )

        missing_skills = self._get_missing_skills()
        present_skills = self._get_present_skills()
        suggestions = self._generate_suggestions(
            overall_score, category_scores, missing_skills
        )

        return {
            "overall_score": min(overall_score, 100),
            "keyword_score": round(keyword_score, 1),
            "structure_score": round(structure_score, 1),
            "format_score": round(format_score, 1),
            "category_scores": category_scores,
            "missing_skills": missing_skills,
            "present_skills": present_skills,
            "suggestions": suggestions,
            "grade": self._get_grade(overall_score),
            "word_count_ok": 300 <= self.resume_data.get("word_count", 0) <= 700,
            "word_count": self.resume_data.get("word_count", 0),
            "page_count": self.resume_data.get("page_count", 1),
        }

    # ── Scoring Sub-routines ────────────────────────────────────────────────

    def _score_keywords(self) -> tuple:
        """
        Score based on weighted keyword matching across ATS categories.

        Returns:
            tuple: (total_keyword_score_0_to_100, {category: score_pct})
        """
        category_scores = {}
        total_weighted = 0.0

        for category, keywords in ATS_KEYWORDS.items():
            matches = [kw for kw in keywords if self._keyword_found(kw)]
            pct = len(matches) / len(keywords) * 100 if keywords else 0
            category_scores[category] = round(pct, 1)
            weight = ATS_SCORING_WEIGHTS.get(category, 0.05)
            total_weighted += pct * weight

        # Normalise to 100
        total_weight = sum(ATS_SCORING_WEIGHTS.values())
        normalised = (total_weighted / total_weight) if total_weight else 0
        return normalised, category_scores

    def _score_structure(self) -> float:
        """
        Award points for presence of key resume sections.
        Max 100 (scaled to 20 in final).
        """
        score = 0
        # Required sections: 15 pts each (max 60)
        for section in self.REQUIRED_SECTIONS:
            pattern = r"(?i)\b" + re.escape(section) + r"\b"
            if re.search(pattern, self.raw_text):
                score += 15

        # Preferred sections: 10 pts each (max 30)
        for section in self.PREFERRED_SECTIONS:
            pattern = r"(?i)\b" + re.escape(section) + r"\b"
            if re.search(pattern, self.raw_text):
                score += 10

        # Contact info bonus (10 pts)
        if self.resume_data.get("email"):
            score += 5
        if self.resume_data.get("phone"):
            score += 5

        return min(score, 100)

    def _score_formatting(self) -> float:
        """
        Heuristic formatting checks: word count, page count, bullet points.
        Max 100 (scaled to 10 in final).
        """
        score = 0
        word_count = self.resume_data.get("word_count", 0)
        page_count = self.resume_data.get("page_count", 1)

        # Word count in ideal range
        if 300 <= word_count <= 700:
            score += 40
        elif 200 <= word_count < 300 or 700 < word_count <= 900:
            score += 25

        # Ideal page count (1–2 pages)
        if 1 <= page_count <= 2:
            score += 30
        elif page_count == 3:
            score += 15

        # Bullet points present
        if re.search(r"[•\-\*]\s+\w", self.raw_text):
            score += 30

        return min(score, 100)

    # ── Helper Methods ──────────────────────────────────────────────────────

    def _keyword_found(self, keyword: str) -> bool:
        """Check if a keyword exists as a whole word in the resume text."""
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        return bool(re.search(pattern, self.raw_text))

    def _get_missing_skills(self) -> dict:
        """Return top missing keywords per category (max 5 per category)."""
        missing = {}
        for category, keywords in ATS_KEYWORDS.items():
            not_found = [kw for kw in keywords if not self._keyword_found(kw)]
            if not_found:
                missing[category] = not_found[:5]
        return missing

    def _get_present_skills(self) -> dict:
        """Return detected keywords per category."""
        present = {}
        for category, keywords in ATS_KEYWORDS.items():
            found = [kw for kw in keywords if self._keyword_found(kw)]
            if found:
                present[category] = found
        return present

    def _generate_suggestions(
        self, score: float, category_scores: dict, missing_skills: dict
    ) -> list:
        """
        Build a prioritised list of actionable improvement suggestions.
        """
        suggestions = []

        # Score-based global tips
        if score < 40:
            suggestions.append(
                "🚨 Critical: Your ATS score is very low. Significantly expand your skills section."
            )
        elif score < 60:
            suggestions.append(
                "⚠️ Your resume needs improvement to pass most ATS filters."
            )
        elif score < 80:
            suggestions.append(
                "📈 Good resume! A few targeted additions will push you into the top tier."
            )
        else:
            suggestions.append(
                "✅ Excellent ATS score! Your resume is well-optimised."
            )

        # Category-specific tips
        for category, cat_score in sorted(category_scores.items(), key=lambda x: x[1]):
            if cat_score < 20 and category in missing_skills:
                top_missing = ", ".join(missing_skills[category][:3])
                suggestions.append(
                    f"💡 Add {category} skills. Consider including: {top_missing}."
                )

        # Structural tips
        if not self.resume_data.get("email"):
            suggestions.append("📧 Add your email address — it's essential for ATS.")
        if not self.resume_data.get("phone"):
            suggestions.append("📞 Add your phone number to the contact section.")

        word_count = self.resume_data.get("word_count", 0)
        if word_count < 300:
            suggestions.append(
                f"📝 Your resume is too short ({word_count} words). "
                "Aim for 300–700 words for best ATS results."
            )
        elif word_count > 700:
            suggestions.append(
                f"✂️ Your resume is quite long ({word_count} words). "
                "Consider condensing to 1–2 pages."
            )

        return suggestions

    @staticmethod
    def _get_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"
