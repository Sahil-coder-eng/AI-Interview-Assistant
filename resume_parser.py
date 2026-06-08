# ============================================================
#  resume_parser.py — PDF text extraction & skill analysis
# ============================================================

import re
import pdfplumber
from config import ATS_KEYWORDS


class ResumeParser:
    """
    Extracts and structures information from a PDF resume.
    Uses pdfplumber for text extraction and regex for entity recognition.
    """

    # ── Common section header patterns ──────────────────────────────────────
    SECTION_HEADERS = {
        "skills": r"(?i)(skills?|technical\s+skills?|core\s+competencies|technologies)",
        "experience": r"(?i)(experience|work\s+history|employment|professional\s+background)",
        "education": r"(?i)(education|academic|qualifications?|degree)",
        "projects": r"(?i)(projects?|personal\s+projects?|key\s+projects?)",
        "certifications": r"(?i)(certifications?|licenses?|credentials?|courses?)",
        "summary": r"(?i)(summary|objective|profile|about\s+me|overview)",
        "contact": r"(?i)(contact|personal\s+info|reach\s+me)",
    }

    def __init__(self, pdf_path: str):
        """
        Initialise the parser with a path to a PDF file.

        Args:
            pdf_path (str): Absolute path to the uploaded PDF resume.
        """
        self.pdf_path = pdf_path
        self.raw_text = ""
        self.structured_data = {}

    # ── Public API ──────────────────────────────────────────────────────────

    def parse(self) -> dict:
        """
        Main entry point. Extracts text then structures it.

        Returns:
            dict: {raw_text, skills, experience, education,
                   projects, certifications, summary, contact, email, phone}
        """
        self.raw_text = self._extract_text()
        self.structured_data = {
            "raw_text": self.raw_text,
            "skills": self._extract_skills(),
            "technologies": self._extract_technologies(),
            "experience": self._extract_section("experience"),
            "education": self._extract_section("education"),
            "projects": self._extract_section("projects"),
            "certifications": self._extract_section("certifications"),
            "summary": self._extract_section("summary"),
            "email": self._extract_email(),
            "phone": self._extract_phone(),
            "name": self._extract_name(),
            "word_count": len(self.raw_text.split()),
            "page_count": self._get_page_count(),
        }
        return self.structured_data

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _extract_text(self) -> str:
        """
        Use pdfplumber to extract plain text from all PDF pages.
        Falls back to empty string on any error.
        """
        text_parts = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            print(f"[ResumeParser] PDF extraction error: {e}")
        return "\n".join(text_parts)

    def _get_page_count(self) -> int:
        """Return the number of pages in the PDF."""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0

    def _extract_email(self) -> str:
        """Regex-based email extraction."""
        pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        match = re.search(pattern, self.raw_text)
        return match.group(0) if match else ""

    def _extract_phone(self) -> str:
        """Regex-based phone number extraction."""
        pattern = r"(\+?\d[\d\s\-().]{8,15}\d)"
        match = re.search(pattern, self.raw_text)
        return match.group(0).strip() if match else ""

    def _extract_name(self) -> str:
        """
        Heuristic: the candidate name is usually in the first 2 lines
        of the resume before any section header.
        """
        lines = [l.strip() for l in self.raw_text.split("\n") if l.strip()]
        for line in lines[:5]:
            # Skip lines that look like headers or contact info
            if (
                len(line.split()) <= 4
                and not re.search(r"[@|]", line)
                and not re.search(r"\d", line)
                and re.match(r"^[A-Z][a-zA-Z\s]+$", line)
            ):
                return line
        return lines[0] if lines else "Candidate"

    def _extract_section(self, section_key: str) -> str:
        """
        Extract the content block under a detected section header.
        Returns raw text of that section.
        """
        pattern = self.SECTION_HEADERS.get(section_key, "")
        if not pattern:
            return ""

        lines = self.raw_text.split("\n")
        section_text = []
        inside_section = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.search(pattern, stripped) and len(stripped) < 60:
                inside_section = True
                continue
            if inside_section:
                # Stop at next recognised section header (different section)
                is_new_section = any(
                    re.search(p, stripped) and len(stripped) < 60
                    for k, p in self.SECTION_HEADERS.items()
                    if k != section_key
                )
                if is_new_section:
                    break
                if stripped:
                    section_text.append(stripped)

        return "\n".join(section_text)

    def _extract_skills(self) -> list:
        """
        Match resume text against the global ATS keyword database.
        Returns a deduplicated, sorted list of found skills.
        """
        text_lower = self.raw_text.lower()
        found_skills = set()

        for _category, keywords in ATS_KEYWORDS.items():
            for keyword in keywords:
                # Whole-word match to avoid partial hits
                pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    found_skills.add(keyword.title())

        return sorted(found_skills)

    def _extract_technologies(self) -> dict:
        """
        Returns skills grouped by ATS category for richer display.
        """
        text_lower = self.raw_text.lower()
        categorised = {}

        for category, keywords in ATS_KEYWORDS.items():
            found = []
            for keyword in keywords:
                pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    found.append(keyword)
            if found:
                categorised[category] = found

        return categorised
