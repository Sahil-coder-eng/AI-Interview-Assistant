import os
import requests
from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)

class AIClient:
    def __init__(self):
        self.openrouter_key = OPENROUTER_API_KEY
        self.openrouter_url = OPENROUTER_BASE_URL
        self.openrouter_model = OPENROUTER_MODEL

    def generate_content(
        self,
        prompt: str,
        system_prompt: str = None,
        model_name: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if self.openrouter_key:
            target_model = model_name or self.openrouter_model
            return self._call_openrouter(prompt, system_prompt, target_model, temperature, max_tokens)

        raise ValueError("Configuration Error: OPENROUTER_API_KEY not found.")

    def _call_openrouter(self, prompt: str, system_prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-interview-assistant.app",
            "X-Title": "AI Interview Assistant",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        response = requests.post(f"{self.openrouter_url}/chat/completions", headers=headers, json=payload, timeout=45)
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error (HTTP {response.status_code}): {response.text[:300]}")
        return response.json()["choices"][0]["message"]["content"]