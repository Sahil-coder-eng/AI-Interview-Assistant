# ============================================================
#  app.py — Main Streamlit Application
#  AI Interview Assistant
# ============================================================

import os
import json
import time
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Local modules ─────────────────────────────────────────────────────────────
from config import APP_TITLE, APP_ICON, UPLOAD_DIR, REPORTS_DIR, QUESTION_CATEGORIES, DIFFICULTY_LEVELS, COMPANY_LIST, COMPANY_PROFILES
from resume_parser import ResumeParser
from ats_checker import ATSChecker
from question_generator import QuestionGenerator
from answer_evaluator import AnswerEvaluator
from chatbot import ChatbotAssistant
from report_generator import ReportGenerator
from database import SessionDatabase


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG — must be the very first Streamlit call
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "About": "AI Interview Assistant — Powered by OpenRouter",
    },
)


# ══════════════════════════════════════════════════════════════════════════════
#  CSS INJECTION
# ══════════════════════════════════════════════════════════════════════════════
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════
def init_session_state():
    """Initialise all Streamlit session state keys with default values."""
    defaults = {
        # Navigation
        "page": "🏠 Home",
        # Resume
        "resume_data": None,
        "resume_uploaded": False,
        "pdf_path": None,
        # ATS
        "ats_results": None,
        # Interview
        "questions": [],
        "current_q_index": 0,
        "answers": [],
        "interview_active": False,
        "interview_complete": False,
        "interview_difficulty": "Intermediate",
        "interview_category": "Technical",
        "interview_job_role": "",
        "interview_company": "",
        "num_questions": 5,
        # Evaluation
        "session_evaluation": None,
        # Chatbot
        "chatbot": None,
        "chat_messages": [],
        # Session history
        "db": SessionDatabase(),
        # Theme
        "dark_mode": True,
        # Report
        "last_report_path": None,
        # Profile summary
        "profile_summary": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def score_colour(score: float) -> str:
    """Return hex colour based on score range."""
    if score >= 80: return "#43E97B"
    if score >= 60: return "#38BDF8"
    if score >= 40: return "#FBB724"
    return "#FF6584"


def make_gauge(value: float, title: str, max_val: float = 100) -> go.Figure:
    """Create a Plotly gauge chart."""
    colour = score_colour(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={"text": title, "font": {"size": 16, "color": "#E2E8F0", "family": "Inter"}},
        number={"font": {"size": 32, "color": colour, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, max_val], "tickcolor": "#64748B", "tickwidth": 1},
            "bar": {"color": colour, "thickness": 0.3},
            "bgcolor": "#1A1A2E",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],        "color": "rgba(255, 101, 132, 0.1)"},
                {"range": [40, 70],       "color": "rgba(251, 191, 36, 0.1)"},
                {"range": [70, max_val],  "color": "rgba(67, 233, 123, 0.1)"},
            ],
            "threshold": {
                "line": {"color": colour, "width": 3},
                "thickness": 0.8,
                "value": value,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": "#E2E8F0"},
        margin=dict(l=20, r=20, t=60, b=20),
        height=240,
    )
    return fig


def make_radar(criteria_scores: dict) -> go.Figure:
    """Create a Plotly radar / spider chart for evaluation criteria."""
    categories = list(criteria_scores.keys())
    values = list(criteria_scores.values())
    values_closed = values + [values[0]]   # Close the polygon
    categories_closed = categories + [categories[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(108, 99, 255, 0.2)",
        line=dict(color="#6C63FF", width=2),
        name="Your Score",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(26,26,46,0.8)",
            radialaxis=dict(visible=True, range=[0, 10], tickcolor="#64748B", gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(tickcolor="#94A3B8", gridcolor="rgba(255,255,255,0.05)"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": "#E2E8F0"},
        margin=dict(l=60, r=60, t=40, b=40),
        height=350,
        showlegend=False,
    )
    return fig


def make_bar_chart(data: dict, title: str, x_label: str, y_label: str) -> go.Figure:
    """Generic horizontal bar chart."""
    categories = list(data.keys())
    values = list(data.values())
    colours = [score_colour(v) for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation="h",
        marker=dict(color=colours, opacity=0.85),
        text=[f"{v:.0f}%" for v in values],
        textposition="outside",
        textfont=dict(color="#E2E8F0"),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#E2E8F0", family="Inter")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,26,46,0.4)",
        font=dict(family="Inter", color="#94A3B8"),
        xaxis=dict(title=x_label, range=[0, 110], gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title=y_label, autorange="reversed"),
        margin=dict(l=20, r=60, t=50, b=40),
        height=300 + 30 * len(categories),
    )
    return fig


def html_card(content: str, extra_class: str = "") -> str:
    return f'<div class="glass-card {extra_class}">{content}</div>'


def skill_tags_html(skills: list) -> str:
    tags = "".join(f'<span class="skill-tag">{s}</span>' for s in skills)
    return f'<div style="line-height: 2.2;">{tags}</div>'


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        # Logo / Brand
        st.markdown("""
        <div style="text-align:center; padding: 1rem 0 1.5rem;">
            <div style="font-size:3rem;">🤖</div>
            <div style="font-size:1.3rem; font-weight:800; 
                        background:linear-gradient(135deg,#6C63FF,#38BDF8);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                        margin-top:0.3rem;">AI Interview</div>
            <div style="font-size:1.3rem; font-weight:800;
                        background:linear-gradient(135deg,#38BDF8,#43E97B);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                        Assistant</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # Navigation menu
        pages = [
            ("🏠 Home",                  "Home"),
            ("📄 Resume Upload",          "Upload"),
            ("📊 ATS Score Checker",      "ATS"),
            ("🎯 Interview Setup",        "Setup"),
            ("🎤 Interview Mode",         "Interview"),
            ("📈 Performance Dashboard",  "Dashboard"),
            ("💬 AI Career Chatbot",      "Chatbot"),
            ("🗂️ Session History",       "History"),
        ]

        for page_name, page_key in pages:
            is_active = st.session_state.page == page_name
            btn_style = "background:rgba(108,99,255,0.2);border-left:3px solid #6C63FF;" if is_active else ""
            if st.button(
                page_name,
                key=f"nav_{page_key}",
                use_container_width=True,
            ):
                st.session_state.page = page_name
                st.rerun()

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # Resume status indicator
        if st.session_state.resume_uploaded:
            name = st.session_state.resume_data.get("name", "Candidate")
            st.markdown(f"""
            <div class="glass-card" style="padding:0.8rem; margin-top:0.5rem;">
                <div style="color:#43E97B; font-weight:600; font-size:0.85rem;">✅ Resume Loaded</div>
                <div style="color:#94A3B8; font-size:0.8rem; margin-top:0.2rem;">👤 {name}</div>
                <div style="color:#64748B; font-size:0.75rem;">
                    {len(st.session_state.resume_data.get('skills', []))} skills detected
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(255,101,132,0.1); border:1px solid rgba(255,101,132,0.2);
                        border-radius:8px; padding:0.7rem; margin-top:0.5rem;">
                <div style="color:#FF6584; font-size:0.82rem; font-weight:500;">
                    ⚠️ No Resume Uploaded
                </div>
                <div style="color:#64748B; font-size:0.75rem;">Upload a PDF to begin</div>
            </div>
            """, unsafe_allow_html=True)

        # DB stats
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        stats = st.session_state.db.get_stats()
        st.markdown(f"""
        <div style="color:#64748B; font-size:0.78rem; text-align:center; padding:0.5rem;">
            📁 {stats['total_sessions']} sessions  •  
            ⭐ Best: {stats['best_score']:.0f}/100
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════

def page_home():
    st.markdown("""
    <div class="hero-header">
        <h1>🤖 AI Interview Assistant</h1>
        <p>Your personal AI-powered mock interview coach — Upload your resume and start practising in seconds.</p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    features = [
        ("📄", "Resume Analysis",         "AI-powered skill extraction and profile summary generation."),
        ("📊", "ATS Score Checker",       "Know your ATS compatibility score before applying."),
        ("🎤", "AI Mock Interview",       "Personalised questions evaluated by AI in real time."),
        ("📈", "Performance Dashboard",   "Radar charts, category scores, and actionable insights."),
        ("💬", "Career Chatbot",          "Ask anything about interviews, code, or your career path."),
        ("📑", "PDF Report",              "Download a full interview report to track your growth."),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="glass-card" style="height:140px;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">{icon}</div>
                <div style="font-weight:700; color:#E2E8F0; margin-bottom:0.3rem;">{title}</div>
                <div style="color:#94A3B8; font-size:0.88rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Quick stats
    stats = st.session_state.db.get_stats()
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, icon in [
        (c1, "Interviews Done",    stats["total_sessions"],      "🎤"),
        (c2, "Questions Answered", stats["total_questions"],     "❓"),
        (c3, "Avg Score",         f"{stats['avg_score']:.0f}%", "📊"),
        (c4, "Best Score",        f"{stats['best_score']:.0f}%","🏆"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.8rem;">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Getting started CTA
    st.markdown("""
    <div class="glass-card" style="text-align:center; padding:2rem;">
        <div style="font-size:1.4rem; font-weight:700; color:#E2E8F0; margin-bottom:0.5rem;">
            🚀 Ready to ace your next interview?
        </div>
        <div style="color:#94A3B8; margin-bottom:1rem;">
            Start by uploading your resume — it takes less than 10 seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📄 Upload My Resume →", use_container_width=True):
        st.session_state.page = "📄 Resume Upload"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: RESUME UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

def page_resume_upload():
    st.markdown('<div class="hero-header"><h1>📄 Resume Upload & Analysis</h1><p>Upload your PDF resume to get started with AI-powered analysis.</p></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your PDF resume here",
        type=["pdf"],
        help="Only PDF format is supported. Max file size: 10 MB.",
        label_visibility="collapsed",
    )

    if uploaded_file:
        # Save to uploads dir
        safe_name = uploaded_file.name.replace(" ", "_")
        pdf_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        with st.spinner("🔍 Extracting and analysing resume..."):
            parser = ResumeParser(pdf_path)
            resume_data = parser.parse()

        st.session_state.resume_data = resume_data
        st.session_state.resume_uploaded = True
        st.session_state.pdf_path = pdf_path
        st.session_state.ats_results = None   # Reset ATS on new upload

        st.success(f"✅ Resume parsed successfully! Found **{len(resume_data['skills'])} skills** across {resume_data['page_count']} page(s).")

    if st.session_state.resume_uploaded and st.session_state.resume_data:
        data = st.session_state.resume_data
        _render_resume_details(data)


def _render_resume_details(data: dict):
    """Render extracted resume data in a structured layout."""
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 👤 Extracted Information")

    c1, c2 = st.columns([1, 2])

    with c1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:3rem; text-align:center; margin-bottom:0.5rem;">👤</div>
            <div style="text-align:center;">
                <div style="font-size:1.2rem; font-weight:700; color:#E2E8F0;">{data.get('name', 'Candidate')}</div>
                <div style="color:#94A3B8; font-size:0.88rem; margin-top:0.3rem;">{data.get('email', '—')}</div>
                <div style="color:#94A3B8; font-size:0.88rem;">{data.get('phone', '—')}</div>
            </div>
            <div class="section-divider"></div>
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#64748B;">
                <span>📝 {data.get('word_count',0)} words</span>
                <span>📄 {data.get('page_count',1)} page(s)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        tab1, tab2, tab3, tab4 = st.tabs(["🛠️ Skills", "💼 Experience", "🎓 Education", "🚀 Projects"])

        with tab1:
            skills = data.get("skills", [])
            if skills:
                st.markdown(skill_tags_html(skills), unsafe_allow_html=True)
            else:
                st.info("No skills detected. Ensure your resume has a clearly labelled Skills section.")

        with tab2:
            exp = data.get("experience", "")
            if exp:
                st.markdown(f'<div class="glass-card" style="white-space:pre-wrap; font-size:0.9rem; color:#CBD5E0;">{exp[:1200]}</div>', unsafe_allow_html=True)
            else:
                st.info("No experience section detected.")

        with tab3:
            edu = data.get("education", "")
            if edu:
                st.markdown(f'<div class="glass-card" style="white-space:pre-wrap; font-size:0.9rem; color:#CBD5E0;">{edu[:800]}</div>', unsafe_allow_html=True)
            else:
                st.info("No education section detected.")

        with tab4:
            proj = data.get("projects", "")
            if proj:
                st.markdown(f'<div class="glass-card" style="white-space:pre-wrap; font-size:0.9rem; color:#CBD5E0;">{proj[:1000]}</div>', unsafe_allow_html=True)
            else:
                st.info("No projects section detected.")

    # Technologies by category
    techs = data.get("technologies", {})
    if techs:
        st.markdown("### 🔧 Detected Technologies by Category")
        for cat, items in techs.items():
            with st.expander(f"**{cat}** ({len(items)} found)"):
                st.markdown(skill_tags_html(items), unsafe_allow_html=True)

    # AI Profile Summary
    st.markdown("### ✨ AI-Generated Profile Summary")
    if st.button("🔮 Generate Profile Summary", use_container_width=True):
        with st.spinner("Generating your professional summary..."):
            gen = QuestionGenerator()
            summary = gen.generate_profile_summary(data)
            st.session_state.profile_summary = summary

    if st.session_state.profile_summary:
        st.markdown(f'<div class="glass-card">{st.session_state.profile_summary}</div>', unsafe_allow_html=True)

    # Raw text expander
    with st.expander("📋 View Raw Extracted Text"):
        st.text_area("Raw Resume Text", data.get("raw_text", ""), height=300)

    # Navigation
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 Check ATS Score →", use_container_width=True):
            st.session_state.page = "📊 ATS Score Checker"
            st.rerun()
    with c2:
        if st.button("🎯 Start Interview →", use_container_width=True):
            st.session_state.page = "🎯 Interview Setup"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: ATS CHECKER
# ══════════════════════════════════════════════════════════════════════════════

def page_ats_checker():
    st.markdown('<div class="hero-header"><h1>📊 ATS Score Checker</h1><p>Paste a job description to see how well your resume matches that specific role.</p></div>', unsafe_allow_html=True)

    if not st.session_state.resume_uploaded:
        st.warning("⚠️ Please upload your resume first.")
        if st.button("📄 Go to Resume Upload"):
            st.session_state.page = "📄 Resume Upload"
            st.rerun()
        return

    # ── Job Description Input ────────────────────────────────────────────────
    st.markdown("### 📝 Paste Job Description")
    st.markdown(
        '<div style="color:#94A3B8; font-size:0.88rem; margin-bottom:0.5rem;">'
        'Paste the full job description below. The AI will extract keywords and '
        'score your resume against this specific role.</div>',
        unsafe_allow_html=True,
    )

    job_description = st.text_area(
        "Job Description",
        height=220,
        placeholder="Paste the complete job description here...\n\nExample:\nWe are looking for a Senior Backend Engineer with experience in Python, Django, REST APIs, PostgreSQL, Docker, and Kubernetes. The ideal candidate has 3+ years of experience building scalable microservices...",
        label_visibility="collapsed",
        key="ats_jd_input",
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        analyse_jd = st.button(
            "🔍 Analyse Against This Job Description",
            use_container_width=True,
            disabled=not job_description.strip(),
        )
    with c2:
        analyse_generic = st.button(
            "📋 Generic ATS Scan",
            use_container_width=True,
            help="Run a general ATS scan against industry keywords without a specific JD.",
        )

    # ── Trigger Analysis ─────────────────────────────────────────────────────
    if analyse_jd and job_description.strip():
        with st.spinner("🤖 AI is analysing the job description and scoring your resume..."):
            checker = ATSChecker(st.session_state.resume_data)
            st.session_state.ats_results = checker.calculate_score(job_description=job_description.strip())

    if analyse_generic:
        with st.spinner("🔍 Running generic ATS compatibility scan..."):
            checker = ATSChecker(st.session_state.resume_data)
            st.session_state.ats_results = checker.calculate_score(job_description="")

    # ── Display Results ──────────────────────────────────────────────────────
    if st.session_state.ats_results is None:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:2rem; border:1px dashed #64748B40;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">📋</div>
            <div style="font-size:1.1rem; font-weight:600; color:#E2E8F0; margin-bottom:0.3rem;">
                No ATS Analysis Yet
            </div>
            <div style="color:#94A3B8; font-size:0.9rem;">
                Paste a job description above and click <strong>Analyse</strong> to see how your resume matches.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    results = st.session_state.ats_results
    mode = results.get("mode", "generic")

    # Mode badge
    if mode == "job_description":
        st.markdown("""
        <div style="background:rgba(108,99,255,0.15); border:1px solid rgba(108,99,255,0.3);
                    border-radius:8px; padding:0.6rem 1rem; margin-bottom:1rem; display:inline-block;">
            <span style="color:#6C63FF; font-weight:600; font-size:0.88rem;">🎯 JD-Specific Analysis</span>
            <span style="color:#94A3B8; font-size:0.82rem;"> — Scored against the job description you provided</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(251,183,36,0.15); border:1px solid rgba(251,183,36,0.3);
                    border-radius:8px; padding:0.6rem 1rem; margin-bottom:1rem; display:inline-block;">
            <span style="color:#FBB724; font-weight:600; font-size:0.88rem;">📋 Generic Scan</span>
            <span style="color:#94A3B8; font-size:0.82rem;"> — Scored against industry keyword database</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Overall Score Gauge ─────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        overall = results["overall_score"]
        fig = make_gauge(overall, "ATS Compatibility Score")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        grade = results["grade"]
        colour = score_colour(overall)
        st.markdown(f"""
        <div class="glass-card" style="text-align:center; padding:1.5rem;">
            <div style="font-size:0.9rem; color:#94A3B8; margin-bottom:0.3rem;">GRADE</div>
            <div style="font-size:4rem; font-weight:800; color:{colour};">{grade}</div>
            <div style="color:#94A3B8; font-size:0.85rem;">
                Word count: {results.get('word_count', 0)}<br>
                Pages: {results.get('page_count', 1)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        sub_scores = {
            "🔑 Keyword": results["keyword_score"],
            "🏗️ Structure": results["structure_score"],
            "🎨 Formatting": results["format_score"],
        }
        st.markdown('<div class="glass-card" style="padding:1rem;">', unsafe_allow_html=True)
        st.markdown("**Score Breakdown**")
        for label, score in sub_scores.items():
            colour = score_colour(score)
            st.markdown(f"""
            <div style="margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:2px;">
                    <span style="color:#94A3B8;">{label}</span>
                    <span style="color:{colour}; font-weight:600;">{score:.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(int(score) / 100)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── JD Keywords Extracted (only in JD mode) ─────────────────────────────
    if mode == "job_description" and results.get("jd_keywords"):
        st.markdown("### 🔑 Keywords Extracted from Job Description")
        jd_kw = results["jd_keywords"]
        cols = st.columns(3)
        col_idx = 0
        for cat, keywords in jd_kw.items():
            if keywords:
                with cols[col_idx % 3]:
                    st.markdown(f"**{cat}**")
                    st.markdown(skill_tags_html(keywords), unsafe_allow_html=True)
                col_idx += 1
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Category Scores Bar Chart ───────────────────────────────────────────
    cat_scores = results.get("category_scores", {})
    if cat_scores:
        fig = make_bar_chart(cat_scores, "Keyword Match by Category", "Match %", "Category")
        st.plotly_chart(fig, use_container_width=True)

    # ── Present & Missing Skills ────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### ✅ Matched Keywords")
        present = results.get("present_skills", {})
        if present:
            for cat, skills in present.items():
                with st.expander(f"**{cat}** ({len(skills)})"):
                    st.markdown(skill_tags_html(skills), unsafe_allow_html=True)
        else:
            st.info("No keyword matches found.")

    with c2:
        st.markdown("### ❌ Missing Keywords")
        missing = results.get("missing_skills", {})
        if missing:
            for cat, skills in missing.items():
                with st.expander(f"**{cat}** — {len(skills)} missing"):
                    st.markdown(skill_tags_html(skills), unsafe_allow_html=True)
        else:
            st.success("No critical keywords missing!")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Suggestions ─────────────────────────────────────────────────────────
    st.markdown("### 💡 Improvement Suggestions")
    for sug in results.get("suggestions", []):
        st.markdown(f"""
        <div class="glass-card" style="padding:0.8rem 1rem; margin-bottom:0.5rem; border-left:3px solid #6C63FF;">
            {sug}
        </div>
        """, unsafe_allow_html=True)

    # Clear results button
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    if st.button("🔄 Run New Analysis", use_container_width=True):
        st.session_state.ats_results = None
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: INTERVIEW SETUP
# ══════════════════════════════════════════════════════════════════════════════

def page_interview_setup():
    st.markdown('<div class="hero-header"><h1>🎯 Interview Setup</h1><p>Customise your interview session before you begin.</p></div>', unsafe_allow_html=True)

    if not st.session_state.resume_uploaded:
        st.warning("⚠️ Please upload your resume first.")
        if st.button("📄 Go to Resume Upload"):
            st.session_state.page = "📄 Resume Upload"
            st.rerun()
        return

    with st.form("interview_config_form"):
        st.markdown("### ⚙️ Configure Your Interview")

        c1, c2 = st.columns(2)
        with c1:
            category = st.selectbox("📂 Question Category", QUESTION_CATEGORIES)
            difficulty = st.selectbox("📶 Difficulty Level", DIFFICULTY_LEVELS, index=1)
        with c2:
            num_questions = st.slider("❓ Number of Questions", 3, 10, 5)
            job_role = st.text_input("💼 Target Job Role (optional)", placeholder="e.g. Data Scientist, Backend Engineer")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ── Company Selection ────────────────────────────────────────────────
        st.markdown("### 🏢 Target Company")
        st.markdown(
            '<div style="color:#94A3B8; font-size:0.88rem; margin-bottom:0.5rem;">'
            'Select a target company to get questions tailored to their specific interview style, '
            'culture, and evaluation criteria.</div>',
            unsafe_allow_html=True,
        )
        c_left, c_right = st.columns(2)
        with c_left:
            selected_company = st.selectbox(
                "🏢 Select Company",
                COMPANY_LIST,
                index=0,
                help="Choose a company to get interview questions matching their actual hiring process.",
            )
        with c_right:
            custom_company = st.text_input(
                "✏️ Or type a company name",
                placeholder="e.g. Stripe, Razorpay, Zomato...",
                help="If your target company isn't listed, type it here.",
            )

        # Resolve final company name
        if selected_company == "Other (specify below)" and custom_company.strip():
            target_company = custom_company.strip()
        elif selected_company and selected_company != "-- No specific company --":
            target_company = selected_company
        else:
            target_company = ""

        # Show company interview profile if available
        if target_company and target_company in COMPANY_PROFILES:
            profile = COMPANY_PROFILES[target_company]
            focus_html = "".join(f'<span class="skill-tag">{f}</span>' for f in profile.get("question_focus", []))
            st.markdown(f"""
            <div class="glass-card" style="border-left:3px solid #6C63FF; padding:1rem;">
                <div style="font-weight:700; color:#E2E8F0; margin-bottom:0.5rem;">🎯 {target_company} Interview Profile</div>
                <div style="color:#94A3B8; font-size:0.88rem; margin-bottom:0.5rem;">{profile.get('interview_style', '')}</div>
                <div style="font-size:0.82rem; color:#64748B; margin-bottom:0.3rem;">Focus areas:</div>
                <div style="line-height:2.2;">{focus_html}</div>
                <div style="color:#64748B; font-size:0.8rem; margin-top:0.5rem; font-style:italic;">💡 {profile.get('interview_rounds', '')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        generate_all = st.checkbox("🎲 Generate questions for ALL categories", value=False)

        submitted = st.form_submit_button("🚀 Generate Interview Questions", use_container_width=True)

        if submitted:
            with st.spinner("🤖 Generating personalised questions..."):
                gen = QuestionGenerator()
                if generate_all:
                    all_cats = gen.generate_all_categories(
                        st.session_state.resume_data,
                        difficulty,
                        num_per_category=max(2, num_questions // 4),
                        job_role=job_role,
                        target_company=target_company,
                    )
                    questions = []
                    for cat_questions in all_cats.values():
                        questions.extend(cat_questions)
                else:
                    questions = gen.generate_questions(
                        st.session_state.resume_data,
                        category,
                        difficulty,
                        num_questions,
                        job_role,
                        target_company=target_company,
                    )

            st.session_state.questions = questions
            st.session_state.interview_difficulty = difficulty
            st.session_state.interview_category = category if not generate_all else "Mixed"
            st.session_state.interview_job_role = job_role
            st.session_state.interview_company = target_company
            st.session_state.current_q_index = 0
            st.session_state.answers = []
            st.session_state.interview_active = False
            st.session_state.interview_complete = False
            st.session_state.session_evaluation = None

            st.success(f"✅ Generated **{len(questions)} questions** — Ready to begin!")

    # Preview generated questions
    if st.session_state.questions:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📋 Question Preview")

        for i, q in enumerate(st.session_state.questions, 1):
            col = score_colour(100)
            diff_badge = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}.get(q.get("difficulty", ""), "⚪")
            st.markdown(f"""
            <div class="question-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.3rem;">
                    <span style="color:#6C63FF; font-weight:700; font-size:0.85rem;">Q{i} • {q.get('category','')}</span>
                    <span style="font-size:0.8rem; color:#94A3B8;">{diff_badge} {q.get('difficulty','')}</span>
                </div>
                <div style="color:#E2E8F0; font-size:0.95rem;">{q.get('question','')}</div>
                {f'<div style="color:#64748B; font-size:0.8rem; margin-top:0.4rem; font-style:italic;">💡 {q.get("hint","")}</div>' if q.get('hint') else ''}
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        if st.button("🎤 Start Interview Mode →", use_container_width=True):
            st.session_state.page = "🎤 Interview Mode"
            st.session_state.interview_active = True
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: INTERVIEW MODE
# ══════════════════════════════════════════════════════════════════════════════

def page_interview_mode():
    company = st.session_state.get("interview_company", "")
    company_label = f" — Preparing for <strong style='color:#6C63FF;'>{company}</strong>" if company else ""
    st.markdown(f'<div class="hero-header"><h1>🎤 Interview Mode</h1><p>Answer each question as if you were in a real interview.{company_label}</p></div>', unsafe_allow_html=True)

    if not st.session_state.questions:
        st.warning("⚠️ No questions generated yet. Please set up your interview first.")
        if st.button("🎯 Go to Interview Setup"):
            st.session_state.page = "🎯 Interview Setup"
            st.rerun()
        return

    questions = st.session_state.questions
    total = len(questions)
    idx = st.session_state.current_q_index

    # ── Progress Bar ────────────────────────────────────────────────────────
    progress_pct = idx / total
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#94A3B8; margin-bottom:0.3rem;">
        <span>Question {idx + 1} of {total}</span>
        <span>{int(progress_pct * 100)}% complete</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(progress_pct)
    st.markdown("")

    if st.session_state.interview_complete:
        _render_interview_complete()
        return

    # ── Current Question ────────────────────────────────────────────────────
    q = questions[idx]
    diff_colours = {"Beginner": "#43E97B", "Intermediate": "#FBB724", "Advanced": "#FF6584"}
    diff_colour = diff_colours.get(q.get("difficulty", ""), "#94A3B8")

    st.markdown(f"""
    <div class="glass-card" style="border-left:4px solid #6C63FF; padding:1.5rem;">
        <div style="display:flex; gap:0.5rem; margin-bottom:0.8rem; flex-wrap:wrap;">
            <span class="score-badge badge-info">📂 {q.get('category','')}</span>
            <span style="background:rgba(0,0,0,0.2); color:{diff_colour}; border:1px solid {diff_colour}40;
                         padding:3px 12px; border-radius:50px; font-size:0.82rem; font-weight:600;">
                ⚡ {q.get('difficulty','')}
            </span>
            <span class="score-badge badge-success">⏱ {q.get('expected_duration','60 seconds')}</span>
        </div>
        <div style="font-size:1.15rem; font-weight:600; color:#E2E8F0; line-height:1.6;">
            {q.get('question','')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hint toggle
    if q.get("hint"):
        with st.expander("💡 Show Hint"):
            st.markdown(f'<div style="color:#94A3B8; font-style:italic;">{q["hint"]}</div>', unsafe_allow_html=True)

    # ── Answer Input ────────────────────────────────────────────────────────
    st.markdown("### ✍️ Your Answer")
    answer_key = f"answer_{idx}"
    user_answer = st.text_area(
        "Type your answer here...",
        key=answer_key,
        height=180,
        placeholder="Provide a detailed, structured answer. Use examples where possible.",
        label_visibility="collapsed",
    )

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        submit = st.button("✅ Submit Answer", use_container_width=True)
    with c2:
        skip = st.button("⏭️ Skip Question", use_container_width=True)
    with c3:
        end = st.button("🏁 End Interview", use_container_width=True)

    if submit and user_answer.strip():
        _handle_submit_answer(user_answer, q, idx, total)

    if skip:
        _handle_submit_answer("", q, idx, total, skipped=True)

    if end:
        st.session_state.interview_complete = True
        st.rerun()

    # ── Previous Answers ────────────────────────────────────────────────────
    if st.session_state.answers:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📝 Submitted Answers")
        for i, ans in enumerate(st.session_state.answers):
            status = "⏭️ Skipped" if not ans.get("answer") else "✅ Answered"
            with st.expander(f"Q{i+1}: {questions[i].get('question','')[:60]}... — {status}"):
                st.markdown(f"**Your answer:** {ans.get('answer', '*No answer provided*')}")


def _handle_submit_answer(answer: str, question: dict, idx: int, total: int, skipped: bool = False):
    """Record the answer and advance to next question or complete the interview."""
    st.session_state.answers.append({
        "question": question.get("question", ""),
        "answer": answer,
        "category": question.get("category", "General"),
        "difficulty": question.get("difficulty", "Intermediate"),
        "skipped": skipped,
    })

    next_idx = idx + 1
    if next_idx >= total:
        st.session_state.interview_complete = True
    else:
        st.session_state.current_q_index = next_idx

    st.rerun()


def _render_interview_complete():
    """Show completion screen and trigger evaluation."""
    st.markdown("""
    <div class="glass-card" style="text-align:center; padding:2rem; border:1px solid #43E97B40;">
        <div style="font-size:3rem; margin-bottom:0.5rem;">🎉</div>
        <div style="font-size:1.4rem; font-weight:700; color:#43E97B;">Interview Complete!</div>
        <div style="color:#94A3B8; margin-top:0.5rem;">
            All answers submitted. Evaluating your performance with AI...
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.session_evaluation is None:
        with st.spinner("🤖 AI is evaluating your answers... this may take 30–60 seconds."):
            evaluator = AnswerEvaluator()
            evaluation = evaluator.evaluate_session(
                st.session_state.answers,
                target_company=st.session_state.get("interview_company", ""),
            )
            st.session_state.session_evaluation = evaluation

            # Save session to DB
            agg = evaluation.get("aggregate", {})
            session_id = st.session_state.db.save_session({
                "candidate_name": st.session_state.resume_data.get("name", "Candidate"),
                "overall_score": agg.get("overall_score", 0),
                "ats_score": st.session_state.ats_results.get("overall_score", 0) if st.session_state.ats_results else 0,
                "total_questions": agg.get("total_questions", 0),
                "difficulty": st.session_state.interview_difficulty,
                "category": st.session_state.interview_category,
                "job_role": st.session_state.interview_job_role,
                "qa_results": evaluation.get("results", []),
                "aggregate": agg,
            })
        st.success(f"✅ Evaluation complete! Session saved as **#{session_id}**")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📈 View Full Dashboard →", use_container_width=True):
            st.session_state.page = "📈 Performance Dashboard"
            st.rerun()
    with c2:
        if st.button("🔄 Start New Interview", use_container_width=True):
            st.session_state.questions = []
            st.session_state.answers = []
            st.session_state.current_q_index = 0
            st.session_state.interview_complete = False
            st.session_state.session_evaluation = None
            st.session_state.page = "🎯 Interview Setup"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: PERFORMANCE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    st.markdown('<div class="hero-header"><h1>📈 Performance Dashboard</h1><p>Deep-dive into your interview performance with AI-powered analytics.</p></div>', unsafe_allow_html=True)

    evaluation = st.session_state.session_evaluation
    if not evaluation:
        st.warning("⚠️ No interview session evaluated yet. Complete an interview first.")
        if st.button("🎤 Start an Interview"):
            st.session_state.page = "🎯 Interview Setup"
            st.rerun()
        return

    agg = evaluation.get("aggregate", {})
    results = evaluation.get("results", [])
    overall = agg.get("overall_score", 0)

    # ── Top Metrics ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, icon in [
        (c1, "Overall Score",    f"{overall:.0f}/100",                  "🏆"),
        (c2, "Questions",        agg.get("total_questions", 0),          "❓"),
        (c3, "Best Q Score",     f"{agg.get('max_score', 0):.0f}",      "⭐"),
        (c4, "Weakest Q Score",  f"{agg.get('min_score', 0):.0f}",      "📉"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.6rem;">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Charts Row ───────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        fig = make_gauge(overall, "Overall Performance Score")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        criterion_scores = agg.get("criterion_scores", {})
        if criterion_scores:
            fig = make_radar(criterion_scores)
            st.plotly_chart(fig, use_container_width=True)

    # ── Category Scores ──────────────────────────────────────────────────────
    cat_scores = agg.get("category_scores", {})
    if cat_scores:
        fig = make_bar_chart(cat_scores, "Score by Question Category", "Score", "Category")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Per-question Breakdown ───────────────────────────────────────────────
    st.markdown("### 🔍 Question-by-Question Breakdown")
    for i, qa in enumerate(results, 1):
        q_score = qa.get("overall_score", 0)
        colour = score_colour(q_score)
        with st.expander(f"Q{i}: {qa.get('question','')[:70]}... — Score: {q_score:.0f}/100"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**📝 Your Answer:**\n\n{qa.get('answer', '*No answer*')}")
                st.markdown(f"**💬 Feedback:**\n\n{qa.get('feedback', '')}")
                if qa.get("strengths"):
                    st.markdown("**✅ Strengths:**")
                    for s in qa["strengths"]:
                        st.markdown(f"  - {s}")
                if qa.get("improvements"):
                    st.markdown("**📈 Improvements:**")
                    for imp in qa["improvements"]:
                        st.markdown(f"  - {imp}")
                if qa.get("model_answer_hint"):
                    st.info(f"💡 **Ideal answer covers:** {qa['model_answer_hint']}")
            with c2:
                scores = qa.get("scores", {})
                for criterion, score in scores.items():
                    st.markdown(f"""
                    <div style="margin-bottom:0.4rem;">
                        <div style="font-size:0.8rem; color:#94A3B8; margin-bottom:1px;">{criterion}</div>
                        <div style="display:flex; align-items:center; gap:0.5rem;">
                    """, unsafe_allow_html=True)
                    st.progress(score / 10)
                    st.markdown(f"<span style='color:{score_colour(score*10)}; font-weight:600;'>{score}/10</span></div></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Download Report ──────────────────────────────────────────────────────
    st.markdown("### 📑 Download Interview Report")
    if st.button("📥 Generate PDF Report", use_container_width=True):
        with st.spinner("Generating your PDF report..."):
            gen = ReportGenerator()
            report_path = gen.generate({
                "candidate_name": st.session_state.resume_data.get("name", "Candidate"),
                "ats_score": st.session_state.ats_results.get("overall_score", 0) if st.session_state.ats_results else 0,
                "overall_score": overall,
                "session_id": "CURRENT",
                "qa_results": results,
                "ats_data": st.session_state.ats_results or {},
                "aggregate": agg,
            })
            st.session_state.last_report_path = report_path

    if st.session_state.last_report_path and os.path.exists(st.session_state.last_report_path):
        with open(st.session_state.last_report_path, "rb") as f:
            st.download_button(
                label="⬇️ Download PDF Report",
                data=f.read(),
                file_name=os.path.basename(st.session_state.last_report_path),
                mime="application/pdf",
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: CHATBOT
# ══════════════════════════════════════════════════════════════════════════════

def page_chatbot():
    st.markdown('<div class="hero-header"><h1>💬 AI Career Chatbot</h1><p>Ask anything about interviews, programming, resume tips, or career growth.</p></div>', unsafe_allow_html=True)

    # Initialise chatbot
    if st.session_state.chatbot is None:
        st.session_state.chatbot = ChatbotAssistant()

    chatbot: ChatbotAssistant = st.session_state.chatbot

    # ── Quick Prompts ────────────────────────────────────────────────────────
    if not st.session_state.chat_messages:
        st.markdown("### 🚀 Quick Starter Prompts")
        prompts = chatbot.get_quick_prompts()
        cols = st.columns(2)
        for i, prompt in enumerate(prompts):
            with cols[i % 2]:
                if st.button(prompt, key=f"quick_{i}", use_container_width=True):
                    _send_chat_message(prompt, chatbot)

    # ── Chat History ─────────────────────────────────────────────────────────
    if st.session_state.chat_messages:
        st.markdown("### 💬 Conversation")
        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-assistant">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Input ────────────────────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            user_input = st.text_input(
                "Message",
                placeholder="Ask about interviews, coding, resume tips, or career advice...",
                label_visibility="collapsed",
            )
        with c2:
            send = st.form_submit_button("Send 🚀", use_container_width=True)

        if send and user_input.strip():
            resume_ctx = st.session_state.resume_data.get("raw_text", "")[:500] if st.session_state.resume_data else ""
            _send_chat_message(user_input, chatbot, resume_ctx)

    # Clear button
    if st.session_state.chat_messages:
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.chat_messages = []
            chatbot.clear_history()
            st.rerun()


def _send_chat_message(message: str, chatbot: ChatbotAssistant, resume_ctx: str = ""):
    """Send a message to the chatbot and append both turns to chat_messages."""
    st.session_state.chat_messages.append({"role": "user", "content": message})

    with st.spinner("🤖 CareerAI is thinking..."):
        reply = chatbot.chat(message, resume_ctx)

    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: SESSION HISTORY
# ══════════════════════════════════════════════════════════════════════════════

def page_history():
    st.markdown('<div class="hero-header"><h1>🗂️ Session History</h1><p>Review your past interview sessions and track your progress over time.</p></div>', unsafe_allow_html=True)

    db: SessionDatabase = st.session_state.db
    sessions = db.get_all_sessions()
    stats = db.get_stats()

    # ── Stats Row ────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, icon in [
        (c1, "Total Sessions",    stats["total_sessions"],      "📁"),
        (c2, "Total Questions",   stats["total_questions"],     "❓"),
        (c3, "Average Score",    f"{stats['avg_score']:.0f}%", "📊"),
        (c4, "Personal Best",    f"{stats['best_score']:.0f}%","🏆"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.6rem;">{icon}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if not sessions:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:3rem;">
            <div style="font-size:3rem;">📭</div>
            <div style="font-size:1.2rem; color:#94A3B8; margin-top:0.5rem;">
                No sessions yet. Complete your first interview to see history here!
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Score Trend Chart ────────────────────────────────────────────────────
    if len(sessions) > 1:
        df = pd.DataFrame([
            {
                "Date": s.get("date_display", ""),
                "Score": s.get("overall_score", 0),
                "Category": s.get("category", "Mixed"),
            }
            for s in reversed(sessions)
        ])
        fig = px.line(
            df, x="Date", y="Score", markers=True, color_discrete_sequence=["#6C63FF"],
            title="📈 Score Trend Over Time",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,26,46,0.4)",
            font=dict(family="Inter", color="#94A3B8"),
            yaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.05)"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        )
        fig.update_traces(marker=dict(size=10, color="#6C63FF"), line=dict(width=3))
        st.plotly_chart(fig, use_container_width=True)

    # ── Session List ─────────────────────────────────────────────────────────
    st.markdown("### 📋 All Sessions")
    for session in sessions:
        score = session.get("overall_score", 0)
        colour = score_colour(score)
        with st.expander(
            f"**#{session['id']}** — {session.get('date_display', '')} — "
            f"Score: {score:.0f}/100 — {session.get('category', 'Mixed')} / {session.get('difficulty', '—')}"
        ):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Overall Score", f"{score:.0f}/100")
                st.metric("ATS Score", f"{session.get('ats_score', 0):.0f}/100")
            with c2:
                st.metric("Questions", session.get("total_questions", 0))
                st.metric("Category", session.get("category", "—"))
            with c3:
                st.metric("Difficulty", session.get("difficulty", "—"))
                st.metric("Job Role", session.get("job_role", "—") or "General")

            # Delete button
            if st.button(f"🗑️ Delete Session #{session['id']}", key=f"del_{session['id']}"):
                db.delete_session(session["id"])
                st.success(f"Session #{session['id']} deleted.")
                st.rerun()

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear ALL Sessions", use_container_width=True):
        count = db.clear_all()
        st.success(f"Deleted {count} session(s).")
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def main():
    render_sidebar()

    page = st.session_state.page
    if page == "🏠 Home":
        page_home()
    elif page == "📄 Resume Upload":
        page_resume_upload()
    elif page == "📊 ATS Score Checker":
        page_ats_checker()
    elif page == "🎯 Interview Setup":
        page_interview_setup()
    elif page == "🎤 Interview Mode":
        page_interview_mode()
    elif page == "📈 Performance Dashboard":
        page_dashboard()
    elif page == "💬 AI Career Chatbot":
        page_chatbot()
    elif page == "🗂️ Session History":
        page_history()
    else:
        page_home()


if __name__ == "__main__":
    main()
