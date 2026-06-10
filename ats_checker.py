# ============================================================
#  ats_checker.py — ATS Score Calculation & Suggestions
# ============================================================

import re
import json
from ai_client import AIClient
from config import ATS_KEYWORDS, ATS_SCORING_WEIGHTS, OPENROUTER_MODEL_INTERVIEW


class ATSChecker:
    """
    Calculates an ATS (Applicant Tracking System) compatibility score
    for a resume.

    Two modes:
      1. **Job-Description mode** (preferred):
         Uses AI to extract keywords from a real job description,
         then scores the resume against those JD-specific keywords.

      2. **Generic mode** (fallback):
         Scores against a hardcoded industry keyword database.

    Score breakdown (out of 100):
      - Keyword match  : 70 points
      - Structure       : 20 points
      - Formatting      : 10 points
    """

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
        self.client = AIClient()

    # ── Public API ──────────────────────────────────────────────────────────

    def calculate_score(self, job_description: str = "") -> dict:
        """
        Run all scoring sub-routines and return a comprehensive result dict.

        Args:
            job_description (str): If provided, the score is calculated against
                                   this specific JD. Otherwise uses the generic
                                   keyword database.

        Returns:
            dict: {
                overall_score, keyword_score, structure_score, format_score,
                category_scores, missing_skills, present_skills,
                suggestions, grade, word_count, page_count,
                mode, jd_keywords (if JD mode)
            }
        """
        if job_description and job_description.strip():
            return self._score_against_jd(job_description.strip())
        else:
            return self._score_generic()

    # ── JD-Based Scoring ───────────────────────────────────────────────────

    def _score_against_jd(self, job_description: str) -> dict:
        """Score resume against a specific job description using AI extraction."""

        # Step 1: Extract keywords from JD using AI
        jd_keywords = self._extract_jd_keywords(job_description)

        # Step 2: Match resume against JD keywords
        keyword_score, category_scores = self._match_jd_keywords(jd_keywords)
        structure_score = self._score_structure()
        format_score = self._score_formatting()

        overall_score = round(
            keyword_score * 0.70 + structure_score * 0.20 + format_score * 0.10, 1
        )

        missing_skills = self._get_missing_jd_skills(jd_keywords)
        present_skills = self._get_present_jd_skills(jd_keywords)
        suggestions = self._generate_jd_suggestions(
            overall_score, category_scores, missing_skills, jd_keywords
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
            "word_count": self.resume_data.get("word_count", 0),
            "page_count": self.resume_data.get("page_count", 1),
            "mode": "job_description",
            "jd_keywords": jd_keywords,
        }

    def _extract_jd_keywords(self, job_description: str) -> dict:
        """Use AI to extract structured keywords from a job description."""
        prompt = f"""
You are an expert ATS (Applicant Tracking System) analyst.
Extract the important keywords and skills from the following job description.
Categorise them into these groups:

1. "Required Technical Skills" — programming languages, frameworks, tools explicitly required
2. "Preferred Technical Skills" — nice-to-have technologies, tools, certifications
3. "Domain Knowledge" — industry/domain expertise mentioned (e.g., fintech, healthcare, e-commerce)
4. "Soft Skills" — leadership, communication, teamwork etc. mentioned
5. "Experience Requirements" — years of experience, seniority level, specific role expectations
6. "Education" — degree requirements, certifications

Return ONLY a valid JSON object. No markdown fences, no extra text.

Job Description:
\"\"\"
{job_description[:3000]}
\"\"\"

JSON format:
{{
  "Required Technical Skills": ["skill1", "skill2", ...],
  "Preferred Technical Skills": ["skill1", "skill2", ...],
  "Domain Knowledge": ["keyword1", "keyword2", ...],
  "Soft Skills": ["skill1", "skill2", ...],
  "Experience Requirements": ["requirement1", "requirement2", ...],
  "Education": ["requirement1", "requirement2", ...]
}}
"""
        try:
            response = self.client.generate_content(
                prompt, model_name=OPENROUTER_MODEL_INTERVIEW, temperature=0.3
            )
            cleaned = re.sub(r"```(?:json)?", "", response).strip()
            return json.loads(cleaned)
        except Exception as e:
            print(f"[ATSChecker] JD keyword extraction failed: {e}")
            # Fallback: basic keyword extraction from JD text
            return self._basic_jd_extraction(job_description)

    def _basic_jd_extraction(self, job_description: str) -> dict:
        """Fallback: extract keywords from JD using simple pattern matching."""
        jd_lower = job_description.lower()
        result = {
            "Required Technical Skills": [],
            "Preferred Technical Skills": [],
            "Domain Knowledge": [],
            "Soft Skills": [],
            "Experience Requirements": [],
            "Education": [],
        }

        # Match against known keywords
        for category, keywords in ATS_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw.lower()) + r"\b", jd_lower):
                    if category == "Soft Skills":
                        result["Soft Skills"].append(kw)
                    else:
                        result["Required Technical Skills"].append(kw)

        return result

    def _match_jd_keywords(self, jd_keywords: dict) -> tuple:
        """Score resume against JD-extracted keywords."""
        category_weights = {
            "Required Technical Skills": 0.40,
            "Preferred Technical Skills": 0.20,
            "Domain Knowledge": 0.15,
            "Soft Skills": 0.10,
            "Experience Requirements": 0.10,
            "Education": 0.05,
        }

        category_scores = {}
        total_weighted = 0.0
        total_weight = 0.0

        for category, keywords in jd_keywords.items():
            if not keywords:
                continue
            matches = [kw for kw in keywords if self._keyword_found(kw)]
            pct = len(matches) / len(keywords) * 100
            category_scores[category] = round(pct, 1)
            weight = category_weights.get(category, 0.05)
            total_weighted += pct * weight
            total_weight += weight

        normalised = (total_weighted / total_weight) if total_weight else 0
        return normalised, category_scores

    def _get_missing_jd_skills(self, jd_keywords: dict) -> dict:
        """Return keywords from JD not found in resume."""
        missing = {}
        for category, keywords in jd_keywords.items():
            not_found = [kw for kw in keywords if not self._keyword_found(kw)]
            if not_found:
                missing[category] = not_found
        return missing

    def _get_present_jd_skills(self, jd_keywords: dict) -> dict:
        """Return keywords from JD found in resume."""
        present = {}
        for category, keywords in jd_keywords.items():
            found = [kw for kw in keywords if self._keyword_found(kw)]
            if found:
                present[category] = found
        return present

    def _generate_jd_suggestions(
        self, score: float, category_scores: dict,
        missing_skills: dict, jd_keywords: dict
    ) -> list:
        """Build suggestions specific to the job description."""
        suggestions = []

        # Overall score feedback
        if score < 40:
            suggestions.append(
                "🚨 Critical: Your resume is a poor match for this job description. "
                "Major revisions needed to align with the role requirements."
            )
        elif score < 60:
            suggestions.append(
                "⚠️ Your resume partially matches this JD. Add missing keywords "
                "to improve your chances of passing the ATS filter."
            )
        elif score < 80:
            suggestions.append(
                "📈 Good match! A few targeted keyword additions will "
                "significantly boost your ATS score for this role."
            )
        else:
            suggestions.append(
                "✅ Excellent match! Your resume is well-aligned with this job description."
            )

        # Missing required skills are the biggest gap
        req_missing = missing_skills.get("Required Technical Skills", [])
        if req_missing:
            top = ", ".join(req_missing[:5])
            suggestions.append(
                f"🔴 Missing REQUIRED skills from the JD: **{top}**. "
                "Add these to your resume if you have experience with them."
            )

        pref_missing = missing_skills.get("Preferred Technical Skills", [])
        if pref_missing:
            top = ", ".join(pref_missing[:4])
            suggestions.append(
                f"🟡 Missing preferred skills: **{top}**. "
                "Including these gives you an edge over other candidates."
            )

        domain_missing = missing_skills.get("Domain Knowledge", [])
        if domain_missing:
            top = ", ".join(domain_missing[:3])
            suggestions.append(
                f"🏢 The JD mentions domain expertise in: **{top}**. "
                "Highlight relevant domain experience in your resume."
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
                "Aim for 400–700 words for best ATS results."
            )
        elif word_count > 800:
            suggestions.append(
                f"✂️ Your resume is quite long ({word_count} words). "
                "Consider condensing to 1–2 pages."
            )

        return suggestions

    # ── Generic Scoring (fallback) ─────────────────────────────────────────

    def _score_generic(self) -> dict:
        """Original generic scoring against hardcoded keyword database."""
        keyword_score, category_scores = self._score_keywords_generic()
        structure_score = self._score_structure()
        format_score = self._score_formatting()

        overall_score = round(
            keyword_score * 0.70 + structure_score * 0.20 + format_score * 0.10, 1
        )

        missing_skills = self._get_missing_skills_generic()
        present_skills = self._get_present_skills_generic()
        suggestions = self._generate_suggestions_generic(
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
            "word_count": self.resume_data.get("word_count", 0),
            "page_count": self.resume_data.get("page_count", 1),
            "mode": "generic",
        }

    def _score_keywords_generic(self) -> tuple:
        """Score based on weighted keyword matching across ATS categories."""
        category_scores = {}
        total_weighted = 0.0

        for category, keywords in ATS_KEYWORDS.items():
            matches = [kw for kw in keywords if self._keyword_found(kw)]
            pct = len(matches) / len(keywords) * 100 if keywords else 0
            category_scores[category] = round(pct, 1)
            weight = ATS_SCORING_WEIGHTS.get(category, 0.05)
            total_weighted += pct * weight

        total_weight = sum(ATS_SCORING_WEIGHTS.values())
        normalised = (total_weighted / total_weight) if total_weight else 0
        return normalised, category_scores

    def _get_missing_skills_generic(self) -> dict:
        """Return top missing keywords per category (max 5 per category)."""
        missing = {}
        for category, keywords in ATS_KEYWORDS.items():
            not_found = [kw for kw in keywords if not self._keyword_found(kw)]
            if not_found:
                missing[category] = not_found[:5]
        return missing

    def _get_present_skills_generic(self) -> dict:
        """Return detected keywords per category."""
        present = {}
        for category, keywords in ATS_KEYWORDS.items():
            found = [kw for kw in keywords if self._keyword_found(kw)]
            if found:
                present[category] = found
        return present

    def _generate_suggestions_generic(
        self, score: float, category_scores: dict, missing_skills: dict
    ) -> list:
        """Build a prioritised list of actionable improvement suggestions."""
        suggestions = []

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

        for category, cat_score in sorted(category_scores.items(), key=lambda x: x[1]):
            if cat_score < 20 and category in missing_skills:
                top_missing = ", ".join(missing_skills[category][:3])
                suggestions.append(
                    f"💡 Add {category} skills. Consider including: {top_missing}."
                )

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

    # ── Shared Helpers ─────────────────────────────────────────────────────

    def _score_structure(self) -> float:
        """Award points for presence of key resume sections. Max 100."""
        score = 0
        for section in self.REQUIRED_SECTIONS:
            pattern = r"(?i)\b" + re.escape(section) + r"\b"
            if re.search(pattern, self.raw_text):
                score += 15

        for section in self.PREFERRED_SECTIONS:
            pattern = r"(?i)\b" + re.escape(section) + r"\b"
            if re.search(pattern, self.raw_text):
                score += 10

        if self.resume_data.get("email"):
            score += 5
        if self.resume_data.get("phone"):
            score += 5

        return min(score, 100)

    def _score_formatting(self) -> float:
        """Heuristic formatting checks. Max 100."""
        score = 0
        word_count = self.resume_data.get("word_count", 0)
        page_count = self.resume_data.get("page_count", 1)

        if 300 <= word_count <= 700:
            score += 40
        elif 200 <= word_count < 300 or 700 < word_count <= 900:
            score += 25

        if 1 <= page_count <= 2:
            score += 30
        elif page_count == 3:
            score += 15

        if re.search(r"[•\-\*]\s+\w", self.raw_text):
            score += 30

        return min(score, 100)

    def _keyword_found(self, keyword: str) -> bool:
        """Check if a keyword exists as a whole word in the resume text."""
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
        return bool(re.search(pattern, self.raw_text))

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
