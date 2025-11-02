from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

from ...defense.domain.entities import PromptBundle


@dataclass
class OpenRouterModelClient:
    """Клиент OpenRouter. Требует OPENROUTER_API_KEY или переданный api_key."""

    model_id: str
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    timeout: int = 60
    default_headers: Dict[str, str] | None = None
    api_key: str | None = None

    def generate(self, prompt_bundle: PromptBundle) -> str:
        try:
            import requests  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("requests library is required for OpenRouterModelClient") from exc

        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        if not self.model_id:
            raise ValueError("OpenRouterModelClient requires model_id")

        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": prompt_bundle.system_prompt},
                {"role": "user", "content": prompt_bundle.user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if self.default_headers:
            headers.update(self.default_headers)

        response = requests.post(
            self.base_url,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

