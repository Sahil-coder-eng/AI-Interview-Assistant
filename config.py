# ============================================================
#  config.py — Central configuration for AI Interview Assistant
#  Updated: Company profiles, ATS JD-based scoring
# ============================================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─── API Configuration ────────────────────────────────────────────────────────

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"  # Fallback / default model
OPENROUTER_MODEL_CHAT = "meta-llama/llama-3.3-70b-instruct"
OPENROUTER_MODEL_INTERVIEW = "openai/gpt-oss-120b:free"  # Interview model via OpenRouter (free)

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

# ─── Company Interview Profiles ───────────────────────────────────────────────
# Deep knowledge about each company's interview culture, question style,
# evaluation criteria, and what makes a great answer *at that specific company*.

COMPANY_PROFILES = {
    "Google": {
        "interview_style": "Structured, rubric-driven interviews with a strong focus on algorithmic problem-solving and system design. Interviewers use a shared hiring committee model — no single interviewer decides.",
        "question_focus": [
            "Data structures & algorithms (LeetCode medium–hard)",
            "System design (large-scale distributed systems)",
            "Googliness & Leadership (culture fit, collaboration)",
            "Analytical thinking and ambiguity resolution",
        ],
        "culture_values": "Innovation, data-driven decisions, intellectual humility, 'Don't be evil', 10x thinking, psychological safety, collaboration over hierarchy.",
        "what_great_looks_like": "Candidates who think out loud, explore multiple solutions before coding, analyse time/space complexity unprompted, ask clarifying questions, and demonstrate structured communication. Google values depth over breadth.",
        "common_patterns": "Expect graph/tree problems, dynamic programming, sliding window, BFS/DFS. System design: design YouTube, Gmail, Google Maps. Behavioral: 'Tell me about a time you disagreed with a teammate and how you resolved it.'",
        "interview_rounds": "Phone screen → 4–5 on-site loops (2 coding, 1 system design, 1 behavioral/Googliness) → Hiring committee review.",
        "red_flags": "Jumping to code without thinking, not considering edge cases, inability to communicate trade-offs, arrogance.",
    },
    "Amazon": {
        "interview_style": "Heavily behavioral with Leadership Principles (LPs) as the backbone. Every answer is evaluated against one or more LPs. Technical rounds are practical and operations-focused.",
        "question_focus": [
            "Leadership Principles — STAR-format behavioral questions",
            "System design with emphasis on scalability and cost",
            "Object-oriented design and API design",
            "Operational excellence and on-call scenarios",
        ],
        "culture_values": "Customer Obsession, Ownership, Invent and Simplify, Are Right A Lot, Learn and Be Curious, Hire and Develop the Best, Insist on the Highest Standards, Think Big, Bias for Action, Frugality, Earn Trust, Dive Deep, Have Backbone, Deliver Results.",
        "what_great_looks_like": "Candidates who map every answer to a specific Leadership Principle, use the STAR method rigorously (Situation, Task, Action, Result with quantified impact), show ownership and customer obsession. Amazon wants 'builders' who disagree and commit.",
        "common_patterns": "Expect 2–3 LP questions per interviewer. 'Tell me about a time you made a decision without enough data.' 'Describe when you went above and beyond for a customer.' System design: design an e-commerce checkout, a notification service.",
        "interview_rounds": "Online Assessment → Phone screen → 5–6 on-site loops (mix of LP behavioral + technical) → Bar Raiser round.",
        "red_flags": "Vague stories without metrics, blaming teammates, not showing ownership, answers that don't map to LPs.",
    },
    "Microsoft": {
        "interview_style": "Collaborative and conversational. Interviewers assess growth mindset, problem-solving approach, and how you handle feedback. The 'As Appropriate' (AA) interviewer makes the final hire/no-hire decision.",
        "question_focus": [
            "Coding fundamentals (clean, readable, production-quality code)",
            "System design with emphasis on real Microsoft products",
            "Growth mindset and learning from failure",
            "Cross-team collaboration scenarios",
        ],
        "culture_values": "Growth mindset, diversity and inclusion, empowerment, innovation, trustworthiness, respectful culture. Satya Nadella's 'learn-it-all vs. know-it-all' philosophy.",
        "what_great_looks_like": "Candidates who write clean, testable code, discuss design trade-offs, show intellectual curiosity, demonstrate they can learn from mistakes, and collaborate well. Microsoft values people who ask 'how can we make this better?' rather than 'I'm already the best.'",
        "common_patterns": "Design questions around Azure, Office 365, Teams. Coding: linked lists, trees, string manipulation, moderate difficulty. Behavioral: 'Tell me about a time you received critical feedback and what you did with it.'",
        "interview_rounds": "Phone screen → 4–5 on-site loops → AA (As Appropriate) interview with senior leader.",
        "red_flags": "Fixed mindset, inability to accept feedback, writing messy code, not asking questions.",
    },
    "Meta (Facebook)": {
        "interview_style": "Fast-paced, efficiency-driven. Coding rounds are timed (45 min, solve 2 problems). System design is product-focused. Strong emphasis on impact and moving fast.",
        "question_focus": [
            "Coding: 2 problems in 45 minutes (LeetCode medium)",
            "System design: design Facebook features (News Feed, Messenger, Instagram Stories)",
            "Behavioral: focus on impact, collaboration, and moving fast",
            "Product sense for product-adjacent roles",
        ],
        "culture_values": "Move Fast, Be Bold, Focus on Impact, Be Open, Build Social Value. Meta values builders who ship fast, iterate, and measure impact with data.",
        "what_great_looks_like": "Candidates who solve problems quickly and efficiently, write bug-free code under time pressure, design systems that handle billions of users, and quantify their past impact with metrics. Speed + quality is the bar.",
        "common_patterns": "Array/string manipulation, graph traversals, interval problems. System design: design News Feed ranking, real-time chat, live video streaming. Behavioral: 'What's the most impactful project you've worked on and how did you measure success?'",
        "interview_rounds": "Coding screen (2 problems) → On-site: 2 coding + 1 system design + 1 behavioral → Team matching.",
        "red_flags": "Slow coding speed, not optimising solutions, inability to articulate impact, over-engineering.",
    },
    "Apple": {
        "interview_style": "Secretive and team-specific. Each team runs its own process. Strong focus on craftsmanship, attention to detail, and passion for Apple products. Domain expertise matters a lot.",
        "question_focus": [
            "Deep domain expertise in the team's specific area",
            "System design with emphasis on user experience and performance",
            "Coding with focus on clean architecture and edge cases",
            "Cultural fit: passion for Apple's mission and products",
        ],
        "culture_values": "Excellence in craft, secrecy, user-first design, attention to detail, integration of hardware and software, simplicity, 'it just works' philosophy.",
        "what_great_looks_like": "Candidates who show deep expertise, care about pixel-perfect details, understand Apple's product philosophy, write elegant code, and demonstrate genuine passion for the role. Apple wants specialists, not generalists.",
        "common_patterns": "Domain-specific deep dives, low-level system questions (memory management, concurrency), UI/UX design discussions. 'Why do you want to work at Apple?' is asked seriously.",
        "interview_rounds": "Phone screen → Technical phone screen → On-site with the specific team (4–6 interviews) → Hiring manager decision.",
        "red_flags": "Not knowing Apple products, sloppy code, lack of attention to detail, generic answers.",
    },
    "Netflix": {
        "interview_style": "Culture-heavy, high-autonomy environment. Interviews focus on senior-level judgment, context-not-control philosophy, and the Netflix Culture Deck values. Less algorithmic, more practical.",
        "question_focus": [
            "Real-world system design and architecture decisions",
            "Culture fit: freedom and responsibility, radical candor",
            "Past impact and decision-making at scale",
            "Domain expertise and technical depth",
        ],
        "culture_values": "Freedom and Responsibility, Context Not Control, Highly Aligned Loosely Coupled, Pay Top of Market, Keeper Test, Radical Candor, No Brilliant Jerks.",
        "what_great_looks_like": "Candidates who demonstrate senior-level judgment, can operate autonomously, give and receive direct feedback, and have a track record of high-impact work. Netflix hires 'stunning colleagues' and pays top-of-market.",
        "common_patterns": "Practical system design (design Netflix streaming, recommendation engine). Deep behavioral: 'Tell me about a time you made an unpopular decision.' 'How do you handle disagreement with your manager?'",
        "interview_rounds": "Recruiter screen → Hiring manager → Technical screen → On-site (4–5 rounds, mix of technical and cultural).",
        "red_flags": "Needing hand-holding, avoiding conflict, not being self-directed, lack of strong opinions.",
    },
    "Uber": {
        "interview_style": "Fast-paced, practical problem-solving focused on real-world systems. Mix of coding, system design, and behavioral. Values entrepreneurial mindset.",
        "question_focus": [
            "Coding: practical problems, moderate–hard difficulty",
            "System design: real-time systems, geolocation, matching algorithms",
            "Behavioral: ownership, working in ambiguity, hustle",
            "Domain: distributed systems, real-time data processing",
        ],
        "culture_values": "We build globally, we live locally. Great minds don't think alike. We act like owners. We persevere. We value ideas over hierarchy. We make big bold bets.",
        "what_great_looks_like": "Candidates who can design real-time, location-aware systems, show entrepreneurial drive, handle ambiguity well, and have experience with high-throughput systems.",
        "common_patterns": "Design ride-matching, surge pricing, ETA prediction. Coding: graph problems, geospatial algorithms. Behavioral: 'Tell me about a time you launched something with incomplete information.'",
        "interview_rounds": "Recruiter screen → Technical phone screen → On-site (4–5 rounds) → Hiring committee.",
        "red_flags": "Inability to handle ambiguity, slow problem-solving, not considering scale.",
    },
    "Flipkart": {
        "interview_style": "Strong focus on Data Structures & Algorithms (DSA), system design, and machine coding rounds. Very competitive, expects clean code and optimal solutions.",
        "question_focus": [
            "DSA: arrays, trees, graphs, DP, greedy — medium to hard",
            "Machine Coding: build a working module in 60–90 minutes",
            "System design: e-commerce scale (inventory, search, payments)",
            "Behavioral: ownership, hustle, startup mindset",
        ],
        "culture_values": "Customer first, speed of execution, audacity, bias for action, integrity, ownership mentality. India's e-commerce pioneer.",
        "what_great_looks_like": "Candidates who write optimal, clean, production-ready code, can design e-commerce systems at scale, demonstrate machine coding skills (LLD), and show a startup builder mindset.",
        "common_patterns": "Machine coding: design a parking lot, split-wise, in-memory cache. System design: design Flipkart search, order management, payment gateway. DSA: DP, graph shortest paths, segment trees.",
        "interview_rounds": "Online coding test → Machine coding round → 2 DSA rounds → System design → Hiring manager.",
        "red_flags": "Brute force only solutions, messy code structure, no consideration of scale, poor LLD skills.",
    },
    "Infosys": {
        "interview_style": "Structured process with aptitude testing, followed by technical and HR rounds. Focus on fundamentals, willingness to learn, and cultural fit. More process-driven than product companies.",
        "question_focus": [
            "Core CS fundamentals: OOP, DBMS, OS, networking basics",
            "Programming basics in Java/Python/C++",
            "Aptitude and logical reasoning",
            "HR: communication skills, adaptability, willingness to relocate",
        ],
        "culture_values": "C-LIFE values: Client Value, Leadership by Example, Integrity and Transparency, Fairness, Excellence. Learning culture, global delivery model.",
        "what_great_looks_like": "Candidates who demonstrate strong fundamentals, clear communication, eagerness to learn, flexibility (willing to work on any technology/project), and alignment with Infosys's values. Freshers should show strong aptitude scores.",
        "common_patterns": "Technical: 'Explain OOP pillars with examples', 'Difference between SQL and NoSQL', 'What is normalization?'. HR: 'Are you willing to relocate?', 'Why Infosys?', 'Where do you see yourself in 5 years?'",
        "interview_rounds": "Online aptitude test (InfyTQ/HackWithInfy) → Technical interview → HR interview → Offer.",
        "red_flags": "Poor fundamentals, unwillingness to relocate, lack of communication skills, no interest in continuous learning.",
    },
    "TCS (Tata Consultancy Services)": {
        "interview_style": "Standardized process, especially for campus hiring (TCS NQT). Focus on aptitude, basic programming, and communication. Values team players and adaptable candidates.",
        "question_focus": [
            "TCS NQT: quantitative aptitude, verbal ability, programming logic",
            "Basic programming: C/Java/Python fundamentals",
            "CS fundamentals: OOP, DBMS basics, networking",
            "HR: adaptability, teamwork, willingness to learn new technologies",
        ],
        "culture_values": "Integrity, Respect for the Individual, Excellence, Learning and Sharing, Customer Value. Global scale, diverse project exposure.",
        "what_great_looks_like": "Candidates who clear NQT with good scores, demonstrate basic but solid programming knowledge, communicate clearly, show adaptability and willingness to work across different domains/technologies.",
        "common_patterns": "NQT: numerical ability, verbal reasoning, coding MCQs. Technical: 'What is polymorphism?', 'Write a program to reverse a string', 'Explain SDLC'. HR: 'Tell me about yourself', 'Why TCS?', 'What are your strengths?'",
        "interview_rounds": "TCS NQT (aptitude + coding) → Technical interview → Managerial/HR interview → Offer.",
        "red_flags": "Failing NQT cutoff, very poor communication, rigidity about technology/location preferences.",
    },
    "Wipro": {
        "interview_style": "Similar to other Indian IT services — aptitude test followed by technical and HR rounds. Emphasis on employability skills, fundamentals, and cultural fit.",
        "question_focus": [
            "Aptitude: verbal, quantitative, logical reasoning",
            "Technical: programming basics, OOP, DBMS, OS",
            "Essay/written communication test",
            "HR: adaptability, career goals, company knowledge",
        ],
        "culture_values": "Spirit of Wipro: Intensity to Win, Act with Sensitivity, Unyielding Integrity. Focus on digital transformation and innovation.",
        "what_great_looks_like": "Clear communication (written and verbal), solid fundamentals, awareness of current tech trends, flexibility, and genuine interest in the IT services model.",
        "common_patterns": "Written test with essay component. Technical: 'What is a primary key?', 'Explain encapsulation', 'Difference between stack and queue'. HR: 'Why Wipro?', 'What do you know about our services?'",
        "interview_rounds": "Online test (aptitude + essay) → Technical interview → HR interview → Offer.",
        "red_flags": "Poor written communication, weak fundamentals, no knowledge of the company.",
    },
    "Startup (General)": {
        "interview_style": "Fast, informal, and practical. Startups value builders who can ship quickly. Often includes a take-home project or live coding. Culture fit is weighed equally with technical skills.",
        "question_focus": [
            "Practical coding: build something real (take-home or live)",
            "Full-stack breadth: can you wear multiple hats?",
            "Product thinking: understanding user needs and business impact",
            "Culture: scrappiness, ownership, comfort with ambiguity",
        ],
        "culture_values": "Speed, ownership, wearing many hats, customer empathy, scrappiness, learning fast, direct communication, flat hierarchy.",
        "what_great_looks_like": "Candidates who can build end-to-end, have shipped real products, show entrepreneurial drive, can make pragmatic trade-offs, and are comfortable with undefined roles and rapid change.",
        "common_patterns": "Take-home project (build a feature in 4–8 hours). System design: design the startup's actual product. Behavioral: 'Tell me about something you built from scratch.' 'How do you prioritize when everything is urgent?'",
        "interview_rounds": "Recruiter call → Take-home challenge → Technical deep-dive → Founder/CTO chat → Offer.",
        "red_flags": "Only wanting to work on one thing, needing constant direction, over-engineering, slow execution.",
    },
}

COMPANY_LIST = [
    "-- No specific company --",
    "Google",
    "Amazon",
    "Microsoft",
    "Meta (Facebook)",
    "Apple",
    "Netflix",
    "Uber",
    "Flipkart",
    "Infosys",
    "TCS (Tata Consultancy Services)",
    "Wipro",
    "Startup (General)",
    "Other (specify below)",
]

# ─── UI Theme ─────────────────────────────────────────────────────────────────
THEME = {
    "primary": "#6C63FF",
    "secondary": "#FF6584",
    "accent": "#43E97B",
    "background": "#0F0F1A",
    "surface": "#1A1A2E",
    "text": "#E2E8F0",
}