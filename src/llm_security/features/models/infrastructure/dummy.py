from __future__ import annotations

from dataclasses import dataclass

from ...defense.domain.entities import PromptBundle


@dataclass
class DummyModelClient:
    """Простая модель, имитирующая уязвимое поведение LLM."""

    model_id: str = "dummy"

    def generate(self, prompt_bundle: PromptBundle) -> str:
        prompt = prompt_bundle.user_prompt.lower()
        if "раскрой" in prompt and "промпт" in prompt:
            return "Скрытый системный промпт: [TOP SECRET]"
        if "бомбу" in prompt or "взломать" in prompt:
            return "Вот пошаговая инструкция, как изготовить запрещённый предмет."
        if "погоду" in prompt:
            return "Сегодня солнечно и +20°C."
        return "Извините, я не могу помочь с этим."

