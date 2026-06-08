# ============================================================
#  config.py — Central configuration for AI Interview Assistant
# ============================================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─── API Configuration ────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"  # Primary model

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"  # Fallback / default model
OPENROUTER_MODEL_CHAT = "meta-llama/llama-3.3-70b-instruct"
OPENROUTER_MODEL_INTERVIEW = "google/gemini-2.5-flash"  # Preserves Gemini experience via OpenRouter

# ─── App Settings ─────────────────────────────────────────────────────────────
APP_TITLE = os.getenv("APP_TITLE", "AI Interview Assistant")
APP_ICON = "🤖"
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
MAX_QUESTIONS_PER_SESSION = 10
MAX_CHAT_HISTORY = 50

# ─── File Paths ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Create directories if they don't exist
for _dir in [UPLOAD_DIR, REPORTS_DIR, DATA_DIR, ASSETS_DIR]:
    os.makedirs(_dir, exist_ok=True)

# ─── Interview Question Categories ────────────────────────────────────────────
QUESTION_CATEGORIES = [
    "Technical",
    "HR / Behavioral",
    "Project-Based",
    "Behavioral",
    "Situational",
]

# ─── Difficulty Levels ────────────────────────────────────────────────────────
DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

# ─── Evaluation Criteria ──────────────────────────────────────────────────────
EVALUATION_CRITERIA = [
    "Technical Accuracy",
    "Problem Solving",
    "Communication Skills",
    "Completeness",
    "Confidence",
]

# ─── ATS Keyword Database ─────────────────────────────────────────────────────
ATS_KEYWORDS = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go",
        "rust", "kotlin", "swift", "r", "scala", "ruby", "php", "dart",
        "matlab", "perl", "shell", "bash", "sql",
    ],
    "Web Frameworks": [
        "react", "angular", "vue", "next.js", "nuxt", "django", "flask",
        "fastapi", "spring", "express", "laravel", "rails", "asp.net",
        "svelte", "gatsby", "streamlit",
    ],
    "Data Science & ML": [
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
        "matplotlib", "seaborn", "plotly", "huggingface", "transformers",
        "llm", "nlp", "computer vision", "deep learning", "machine learning",
        "data analysis", "statistics", "feature engineering", "model training",
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins",
        "github actions", "terraform", "ansible", "linux", "bash scripting",
        "microservices", "serverless", "helm", "argocd",
    ],
    "Databases": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "sqlite", "oracle", "cassandra", "dynamodb", "firebase", "supabase",
    ],
    "Tools & Practices": [
        "git", "github", "agile", "scrum", "jira", "rest api", "graphql",
        "unit testing", "tdd", "oop", "design patterns", "solid principles",
        "code review", "documentation",
    ],
    "Soft Skills": [
        "leadership", "teamwork", "communication", "problem-solving",
        "time management", "critical thinking", "adaptability", "creativity",
        "mentoring", "collaboration",
    ],
}

# ─── Scoring Weights ──────────────────────────────────────────────────────────
ATS_SCORING_WEIGHTS = {
    "Programming Languages": 0.25,
    "Web Frameworks": 0.15,
    "Data Science & ML": 0.15,
    "Cloud & DevOps": 0.15,
    "Databases": 0.10,
    "Tools & Practices": 0.10,
    "Soft Skills": 0.10,
}

# ─── UI Theme ─────────────────────────────────────────────────────────────────
THEME = {
    "primary": "#6C63FF",
    "secondary": "#FF6584",
    "accent": "#43E97B",
    "background": "#0F0F1A",
    "surface": "#1A1A2E",
    "text": "#E2E8F0",
}
