from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

import requests

from ...defense.domain.entities import PromptBundle


@dataclass
class OpenRouterModelClient:
    """Клиент OpenRouter (упрощённый). Требует OPENROUTER_API_KEY."""

    model_id: str
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    timeout: int = 60

    def generate(self, prompt_bundle: PromptBundle) -> str:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")

        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": prompt_bundle.system_prompt},
                {"role": "user", "content": prompt_bundle.user_prompt},
            ],
        }
        response = requests.post(
            self.base_url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

