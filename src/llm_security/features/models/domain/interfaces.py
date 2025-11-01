from __future__ import annotations

from typing import Protocol

from ...defense.domain.entities import PromptBundle


class ModelClient(Protocol):
    """Унифицированный интерфейс клиента LLM."""

    model_id: str

    def generate(self, prompt_bundle: PromptBundle) -> str:
        ...

