# ============================================================
#  report_generator.py — PDF Report Generation via ReportLab
# ============================================================

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from config import REPORTS_DIR


class ReportGenerator:
    """
    Generates a professional PDF interview report using ReportLab.

    Report sections:
      1. Cover Page — candidate info + overall score
      2. ATS Analysis — score breakdown
      3. Interview Q&A — each question with answer and evaluation
      4. Performance Summary — criterion scores, strengths, weaknesses
      5. Recommendations
    """

    # ── Brand colours ────────────────────────────────────────────────────────
    PRIMARY = colors.HexColor("#6C63FF")
    SECONDARY = colors.HexColor("#FF6584")
    ACCENT = colors.HexColor("#43E97B")
    DARK = colors.HexColor("#1A1A2E")
    LIGHT_GREY = colors.HexColor("#F0F0F5")
    TEXT = colors.HexColor("#2D3748")
    WHITE = colors.white

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_styles()

    # ── Public API ──────────────────────────────────────────────────────────

    def generate(self, report_data: dict) -> str:
        """
        Generate the full PDF report and save it to the reports directory.

        Args:
            report_data (dict): {
                candidate_name, ats_score, overall_score, session_id,
                qa_results (list), ats_data (dict), aggregate (dict)
            }

        Returns:
            str: Absolute path to the generated PDF file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = (report_data.get("candidate_name", "Candidate")
                     .replace(" ", "_"))
        filename = f"Report_{safe_name}_{timestamp}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = []
        story += self._build_cover(report_data)
        story += self._build_ats_section(report_data)
        story += self._build_qa_section(report_data)
        story += self._build_performance_section(report_data)
        story += self._build_recommendations(report_data)

        doc.build(story)
        return filepath

    # ── Section Builders ────────────────────────────────────────────────────

    def _build_cover(self, data: dict) -> list:
        """Cover page with candidate name, date, and overall score."""
        story = []

        # Header banner (simulated with coloured table)
        header_data = [[Paragraph(
            '<font color="white" size="22"><b>🤖 AI Interview Assistant</b></font>'
            '<br/><font color="#B8B4FF" size="11">Performance Report</font>',
            self.styles["center_white"],
        )]]
        header_table = Table(header_data, colWidths=[17 * cm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.PRIMARY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 20),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
            ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.8 * cm))

        # Candidate info block
        name = data.get("candidate_name", "Candidate")
        date_str = datetime.now().strftime("%d %B %Y")
        session_id = data.get("session_id", "N/A")
        overall = data.get("overall_score", 0)
        ats = data.get("ats_score", 0)

        info_rows = [
            ["👤 Candidate Name", name],
            ["📅 Report Date", date_str],
            ["🔖 Session ID", session_id],
            ["📊 ATS Score", f"{ats}/100"],
            ["🏆 Overall Interview Score", f"{overall}/100"],
        ]

        info_table = Table(info_rows, colWidths=[7 * cm, 10 * cm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("TEXTCOLOR", (0, 0), (0, -1), self.PRIMARY),
            ("TEXTCOLOR", (1, 0), (1, -1), self.TEXT),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [self.LIGHT_GREY, self.WHITE]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5 * cm))

        # Score badge
        grade_colour = self._grade_colour(overall)
        score_data = [[Paragraph(
            f'<font size="36"><b>{overall:.0f}</b></font>'
            f'<br/><font size="12">out of 100</font>',
            self.styles["center_score"],
        )]]
        score_table = Table(score_data, colWidths=[17 * cm])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), grade_colour),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 15),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
        ]))
        story.append(score_table)
        story.append(PageBreak())
        return story

    def _build_ats_section(self, data: dict) -> list:
        """ATS score analysis section."""
        story = []
        story.append(self._section_heading("📋 ATS Score Analysis"))

        ats_data = data.get("ats_data", {})
        if not ats_data:
            story.append(Paragraph("ATS data not available.", self.styles["body"]))
            story.append(Spacer(1, 0.5 * cm))
            return story

        # Category scores table
        cat_scores = ats_data.get("category_scores", {})
        if cat_scores:
            rows = [["Category", "Score (%)", "Status"]]
            for cat, score in cat_scores.items():
                status = "✅ Good" if score >= 50 else ("⚠️ Fair" if score >= 25 else "❌ Needs Work")
                rows.append([cat, f"{score:.0f}%", status])

            table = Table(rows, colWidths=[8 * cm, 4 * cm, 5 * cm])
            table.setStyle(self._standard_table_style())
            story.append(table)
            story.append(Spacer(1, 0.4 * cm))

        # Suggestions
        suggestions = ats_data.get("suggestions", [])
        if suggestions:
            story.append(Paragraph("<b>Improvement Suggestions:</b>", self.styles["subheading"]))
            for sug in suggestions[:5]:
                story.append(Paragraph(f"• {sug}", self.styles["body"]))
        story.append(PageBreak())
        return story

    def _build_qa_section(self, data: dict) -> list:
        """Question & Answer review section."""
        story = []
        story.append(self._section_heading("🎤 Interview Questions & Answers"))

        qa_results = data.get("qa_results", [])
        if not qa_results:
            story.append(Paragraph("No interview data recorded.", self.styles["body"]))
            return story

        for i, qa in enumerate(qa_results, 1):
            block = []
            # Question
            block.append(Paragraph(
                f"<b>Q{i}: {qa.get('question', 'N/A')}</b>",
                self.styles["question"],
            ))
            block.append(Spacer(1, 2 * mm))

            # Category & Difficulty badges
            meta = (f"Category: {qa.get('category', '—')}  |  "
                    f"Difficulty: {qa.get('difficulty', '—')}  |  "
                    f"Score: {qa.get('overall_score', 0):.0f}/100")
            block.append(Paragraph(meta, self.styles["meta"]))
            block.append(Spacer(1, 2 * mm))

            # Answer
            answer = qa.get("answer", "No answer provided.")
            block.append(Paragraph("<b>Answer:</b>", self.styles["subheading"]))
            block.append(Paragraph(answer[:800], self.styles["body"]))
            block.append(Spacer(1, 2 * mm))

            # Feedback
            feedback = qa.get("feedback", "")
            if feedback:
                block.append(Paragraph(f"<i>📝 Feedback: {feedback}</i>", self.styles["feedback"]))

            block.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0")))
            block.append(Spacer(1, 3 * mm))
            story.append(KeepTogether(block))

        story.append(PageBreak())
        return story

    def _build_performance_section(self, data: dict) -> list:
        """Overall performance summary with criterion scores."""
        story = []
        story.append(self._section_heading("📊 Performance Summary"))

        aggregate = data.get("aggregate", {})
        criterion_scores = aggregate.get("criterion_scores", {})

        if criterion_scores:
            rows = [["Criterion", "Score (avg)", "Out of 10"]]
            for criterion, score in criterion_scores.items():
                bar = "█" * int(score) + "░" * (10 - int(score))
                rows.append([criterion, f"{score:.1f}", bar])

            table = Table(rows, colWidths=[7 * cm, 4 * cm, 6 * cm])
            table.setStyle(self._standard_table_style())
            story.append(table)
            story.append(Spacer(1, 0.4 * cm))

        # Category scores
        cat_scores = aggregate.get("category_scores", {})
        if cat_scores:
            story.append(Paragraph("<b>Category Scores:</b>", self.styles["subheading"]))
            for cat, score in cat_scores.items():
                story.append(Paragraph(f"• {cat}: {score:.0f}/100", self.styles["body"]))

        story.append(Spacer(1, 0.5 * cm))
        return story

    def _build_recommendations(self, data: dict) -> list:
        """Final recommendations section."""
        story = []
        story.append(self._section_heading("🎯 Recommendations"))

        qa_results = data.get("qa_results", [])
        all_improvements = []
        all_strengths = []

        for qa in qa_results:
            all_improvements.extend(qa.get("improvements", []))
            all_strengths.extend(qa.get("strengths", []))

        # Deduplicate
        unique_improvements = list(dict.fromkeys(all_improvements))[:6]
        unique_strengths = list(dict.fromkeys(all_strengths))[:4]

        if unique_strengths:
            story.append(Paragraph("<b>✅ Key Strengths Demonstrated:</b>", self.styles["subheading"]))
            for s in unique_strengths:
                story.append(Paragraph(f"• {s}", self.styles["body"]))
            story.append(Spacer(1, 3 * mm))

        if unique_improvements:
            story.append(Paragraph("<b>📈 Areas for Improvement:</b>", self.styles["subheading"]))
            for imp in unique_improvements:
                story.append(Paragraph(f"• {imp}", self.styles["body"]))
            story.append(Spacer(1, 3 * mm))

        # Footer
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            "Generated by AI Interview Assistant | Powered by Gemini & OpenRouter",
            self.styles["footer"],
        ))
        return story

    # ── Style Helpers ────────────────────────────────────────────────────────

    def _register_styles(self):
        """Register custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            "center_white", parent=self.styles["Normal"],
            alignment=TA_CENTER, textColor=colors.white,
        ))
        self.styles.add(ParagraphStyle(
            "center_score", parent=self.styles["Normal"],
            alignment=TA_CENTER, textColor=colors.white,
        ))
        self.styles.add(ParagraphStyle(
            "section_heading", parent=self.styles["Heading1"],
            textColor=self.PRIMARY, fontSize=16, spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            "subheading", parent=self.styles["Normal"],
            textColor=self.TEXT, fontSize=11, fontName="Helvetica-Bold",
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            "body", parent=self.styles["Normal"],
            textColor=self.TEXT, fontSize=10, spaceAfter=4, leading=14,
        ))
        self.styles.add(ParagraphStyle(
            "question", parent=self.styles["Normal"],
            textColor=self.PRIMARY, fontSize=11, fontName="Helvetica-Bold",
        ))
        self.styles.add(ParagraphStyle(
            "meta", parent=self.styles["Normal"],
            textColor=colors.HexColor("#718096"), fontSize=9, fontName="Helvetica-Oblique",
        ))
        self.styles.add(ParagraphStyle(
            "feedback", parent=self.styles["Normal"],
            textColor=colors.HexColor("#4A5568"), fontSize=9, leading=13,
        ))
        self.styles.add(ParagraphStyle(
            "footer", parent=self.styles["Normal"],
            textColor=colors.HexColor("#A0AEC0"), fontSize=8,
            alignment=TA_CENTER,
        ))

    def _section_heading(self, title: str):
        """Return a styled section heading paragraph."""
        return Paragraph(title, self.styles["section_heading"])

    def _standard_table_style(self) -> TableStyle:
        """Return a consistent table style for data tables."""
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.LIGHT_GREY, self.WHITE]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ])

    @staticmethod
    def _grade_colour(score: float) -> colors.Color:
        """Return a colour based on score band."""
        if score >= 80:
            return colors.HexColor("#43E97B")   # Green
        elif score >= 60:
            return colors.HexColor("#4299E1")   # Blue
        elif score >= 40:
            return colors.HexColor("#ECC94B")   # Yellow
        else:
            return colors.HexColor("#FC8181")   # Red
