# ============================================================
#  database.py — Local JSON-based session storage
# ============================================================

import json
import os
import uuid
from datetime import datetime
from config import DATA_DIR


class SessionDatabase:
    """
    Lightweight local database using a single JSON file.

    Stores interview sessions with:
      - Session ID (UUID)
      - Candidate name
      - Timestamp
      - ATS score
      - Questions & answers
      - Evaluation results
      - Final score

    All data is persisted to data/sessions.json.
    """

    DB_FILE = os.path.join(DATA_DIR, "sessions.json")

    def __init__(self):
        """Ensure the database file exists on startup."""
        self._ensure_db_exists()

    # ── Public API ──────────────────────────────────────────────────────────

    def save_session(self, session_data: dict) -> str:
        """
        Save a new interview session to the database.

        Args:
            session_data (dict): Session payload (see _build_session).

        Returns:
            str: The generated session ID.
        """
        sessions = self._load_all()
        session_id = str(uuid.uuid4())[:8].upper()  # Short readable ID

        session = {
            "id": session_id,
            "timestamp": datetime.now().isoformat(),
            "date_display": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            **session_data,
        }

        sessions.append(session)
        self._save_all(sessions)
        return session_id

    def get_all_sessions(self) -> list[dict]:
        """
        Return all stored sessions, newest first.
        """
        sessions = self._load_all()
        return sorted(sessions, key=lambda s: s.get("timestamp", ""), reverse=True)

    def get_session_by_id(self, session_id: str) -> dict | None:
        """
        Retrieve a specific session by its ID.

        Args:
            session_id (str): The session ID to look up.

        Returns:
            dict or None: The session data, or None if not found.
        """
        sessions = self._load_all()
        for session in sessions:
            if session.get("id") == session_id:
                return session
        return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        sessions = self._load_all()
        new_sessions = [s for s in sessions if s.get("id") != session_id]
        if len(new_sessions) == len(sessions):
            return False  # Not found
        self._save_all(new_sessions)
        return True

    def clear_all(self) -> int:
        """
        Delete ALL sessions from the database.

        Returns:
            int: Number of sessions deleted.
        """
        sessions = self._load_all()
        count = len(sessions)
        self._save_all([])
        return count

    def get_stats(self) -> dict:
        """
        Compute aggregate statistics across all sessions.

        Returns:
            dict: {total_sessions, avg_score, best_score, total_questions}
        """
        sessions = self._load_all()
        if not sessions:
            return {
                "total_sessions": 0,
                "avg_score": 0,
                "best_score": 0,
                "total_questions": 0,
            }

        scores = [s.get("overall_score", 0) for s in sessions]
        questions = [s.get("total_questions", 0) for s in sessions]

        return {
            "total_sessions": len(sessions),
            "avg_score": round(sum(scores) / len(scores), 1),
            "best_score": max(scores),
            "total_questions": sum(questions),
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _ensure_db_exists(self):
        """Create the JSON database file with an empty list if it doesn't exist."""
        if not os.path.exists(self.DB_FILE):
            self._save_all([])

    def _load_all(self) -> list:
        """Load and return all sessions from the JSON file."""
        try:
            with open(self.DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_all(self, sessions: list):
        """Persist the full sessions list to the JSON file."""
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self.DB_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
