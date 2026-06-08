# 🤖 AI Interview Assistant

A production-ready, full-stack AI-powered mock interview platform built with **Python**, **Streamlit**, **Gemini 2.5 Flash**, and **OpenRouter**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Resume Upload** | Parse PDF resumes — extract skills, experience, education, projects |
| ✨ **AI Profile Summary** | Gemini generates a professional 3–5 sentence profile summary |
| 📊 **ATS Score Checker** | Score (0–100), grade, missing skills, Plotly charts |
| 🎯 **Interview Setup** | Category + difficulty + job role + question count |
| 🎤 **Interview Mode** | Answer questions one at a time, skip or end early |
| 🤖 **AI Evaluation** | Gemini scores 5 criteria per answer (Technical Accuracy, Problem Solving, Communication, Completeness, Confidence) |
| 📈 **Performance Dashboard** | Gauge, radar, bar charts + per-question breakdown |
| 📑 **PDF Report** | Full ReportLab report — download anytime |
| 💬 **Career Chatbot** | OpenRouter-powered chatbot for interview prep & career guidance |
| 🗂️ **Session History** | Local JSON storage — trend chart, all past sessions |

---

## 🚀 Quick Start

### 1. Clone / Download

```bash
cd AI_Interview_Assistant
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note for Windows users:** If `pyaudio` fails, install it via:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 4. Configure API Keys

Open `.env` and fill in your keys:

```env
# Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# OpenRouter key (for chatbot) — already pre-filled
OPENROUTER_API_KEY=sk-or-v1-...
```

### 5. Run the App

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** 🎉

---

## 📁 Project Structure

```
AI_Interview_Assistant/
├── app.py                  # Main Streamlit app (8 pages, full navigation)
├── config.py               # API keys, constants, ATS keyword database
├── resume_parser.py        # PDF extraction (pdfplumber) + NLP skill detection
├── ats_checker.py          # ATS scoring: keywords, structure, formatting
├── question_generator.py   # Gemini-powered question generation
├── answer_evaluator.py     # Gemini-powered answer evaluation (5 criteria)
├── chatbot.py              # OpenRouter chatbot (Llama 3.3 70B)
├── report_generator.py     # ReportLab PDF report generator
├── database.py             # Local JSON session storage
├── requirements.txt        # All Python dependencies
├── .env                    # API keys (do NOT commit this)
├── README.md
│
├── assets/
│   └── style.css           # Full dark-theme CSS (glassmorphism + animations)
├── uploads/                # Uploaded PDF resumes (auto-created)
├── reports/                # Generated PDF reports (auto-created)
└── data/
    └── sessions.json       # Local session history
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit + Custom CSS (glassmorphism dark theme) |
| **AI / LLM** | Google Gemini 2.5 Flash (questions, evaluation, summaries) |
| **Chatbot** | OpenRouter → Meta Llama 3.3 70B Instruct |
| **PDF Parsing** | pdfplumber |
| **Charts** | Plotly (gauge, radar, bar, line) |
| **PDF Reports** | ReportLab |
| **Storage** | Local JSON (no database setup needed) |
| **Config** | python-dotenv |

---

## 📊 ATS Scoring Breakdown

| Component | Weight |
|---|---|
| Keyword Match (by category) | 70% |
| Resume Structure (sections) | 20% |
| Formatting (word count, bullets) | 10% |

Categories scored: Programming Languages, Web Frameworks, Data Science & ML, Cloud & DevOps, Databases, Tools & Practices, Soft Skills.

---

## 🤖 Evaluation Criteria

Each answer is evaluated by Gemini on:

| Criterion | Weight |
|---|---|
| Technical Accuracy | 30% |
| Problem Solving | 25% |
| Communication Skills | 20% |
| Completeness | 15% |
| Confidence | 10% |

---

## 💬 Chatbot Capabilities

The chatbot (powered by OpenRouter + Llama 3.3 70B) can help with:
- 🔧 Programming questions & debugging
- 🎯 Interview preparation & STAR technique
- 📝 Resume review & ATS optimisation
- 💼 Career guidance & salary negotiation
- 🚀 Skill roadmaps & learning recommendations

---

## 🔐 Security Notes

- The `.env` file contains your API keys — **never commit it to Git**.
- Add `.env` to your `.gitignore`.
- Resume PDFs are stored locally in `uploads/` — clear them periodically.

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| `pdfplumber` can't read text | Ensure the PDF is not a scanned image (use text-based PDFs) |
| Gemini API error | Check `GEMINI_API_KEY` in `.env` is valid |
| Chatbot not responding | Verify `OPENROUTER_API_KEY` and internet connection |
| pyaudio install fails | Use `pipwin install pyaudio` on Windows |
| Report not generating | Ensure `reports/` directory exists (auto-created on startup) |

---

## 📄 License

MIT License — free for personal and commercial use.

---

*Built with ❤️ using Streamlit + Gemini + OpenRouter*
