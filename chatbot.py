# ============================================================
#  chatbot.py — AI Career Chatbot using OpenRouter API
# ============================================================

import os
import requests
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


class ChatbotAssistant:
    """
    A career-focused AI chatbot powered by OpenRouter.

    Handles multi-turn conversations about:
      - Programming & technical questions
      - Interview preparation tips
      - Resume improvement advice
      - Career guidance & job search strategy

    Uses the OpenRouter REST API directly so no extra SDK is needed.
    Maintains conversation history for context-aware replies.
    """

    SYSTEM_PROMPT = """You are "CareerAI", a world-class career coach, technical mentor, 
and interview preparation expert. You help candidates:

1. **Interview Preparation** — explain concepts, give tips, run mini mock-interview drills.
2. **Programming Help** — answer coding questions, explain algorithms, debug logic.
3. **Resume Advice** — review bullet points, suggest improvements, optimise for ATS.
4. **Career Guidance** — salary negotiation, job search strategy, upskilling roadmaps.

Personality:
- Warm, encouraging, and professional.
- Give concrete, actionable advice — never vague generalities.
- When answering technical questions, use examples and analogies.
- Keep responses concise (3–5 sentences) unless a detailed explanation is needed.
- Use markdown formatting: bullet points, **bold**, `code`, headers.

If a question is off-topic (e.g., non-career related), politely redirect to career topics.
"""

    def __init__(self):
        """Initialise with an empty conversation history."""
        self.history: list[dict] = []
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = OPENROUTER_MODEL

    # ── Public API ──────────────────────────────────────────────────────────

    def chat(self, user_message: str, resume_context: str = "") -> str:
        """
        Send a user message and return the assistant's reply.

        Args:
            user_message (str): The user's input text.
            resume_context (str): Optional resume snippet for context-aware advice.

        Returns:
            str: The AI assistant's markdown-formatted response.
        """
        if not user_message.strip():
            return "Please type a message to get started! 😊"

        # Inject resume context once if provided and history is empty
        context_note = ""
        if resume_context and not self.history:
            context_note = f"\n\n[CONTEXT: Candidate's resume summary — {resume_context[:500]}]"

        # Build messages list: system + history + new user turn
        messages = self._build_messages(user_message + context_note)

        try:
            reply = self._call_openrouter(messages)
        except Exception as e:
            reply = (
                f"⚠️ I'm having trouble connecting right now. "
                f"Please try again in a moment.\n\n*Error: {e}*"
            )

        # Store this exchange in history (without context note to keep clean)
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply})

        # Cap history to last 30 messages (15 turns) to stay within token limits
        if len(self.history) > 30:
            self.history = self.history[-30:]

        return reply

    def clear_history(self):
        """Reset conversation history (start a fresh session)."""
        self.history = []

    def get_history(self) -> list[dict]:
        """Return the full conversation history."""
        return self.history.copy()

    def get_quick_prompts(self) -> list[str]:
        """Return suggested starter prompts shown in the UI."""
        return [
            "💡 How should I prepare for a Python interview?",
            "📝 Review my skills section and suggest improvements",
            "🎯 What are the most in-demand tech skills for 2025?",
            "🔧 Explain the difference between SQL and NoSQL databases",
            "💼 How do I negotiate a better salary offer?",
            "🚀 What projects should I build to get my first dev job?",
            "🤔 How do I answer 'Tell me about yourself' effectively?",
            "⚡ Explain Big-O notation with simple examples",
        ]

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _build_messages(self, user_message: str) -> list[dict]:
        """
        Construct the full message list for the OpenRouter API call.
        Format: [system, ...history, new user message]
        """
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_message})
        return messages

    def _call_openrouter(self, messages: list[dict]) -> str:
        """
        Make an HTTP POST request to the OpenRouter chat completions endpoint.

        Args:
            messages (list): Full message list including system prompt + history.

        Returns:
            str: Assistant reply text.

        Raises:
            Exception: On network error or non-200 HTTP response.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-interview-assistant.app",  # Required by OpenRouter
            "X-Title": "AI Interview Assistant",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
            "top_p": 0.9,
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"OpenRouter API error {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]
