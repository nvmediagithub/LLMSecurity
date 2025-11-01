from __future__ import annotations

from typing import Iterable

from ...domain.entities import DefenseResult, PromptBundle
from .base import BaseDefenseLayer


class OutputGuardLayer(BaseDefenseLayer):
    id = "L7"

    def __init__(self, *, blocked_keywords: Iterable[str] | None = None):
        self.blocked_keywords = {kw.lower() for kw in (blocked_keywords or [])}

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        lowered = response_text.lower()
        for keyword in self.blocked_keywords:
            if keyword in lowered:
                return DefenseResult.block(self.id, reason=f"blocked_keyword:{keyword}")
        return DefenseResult.allow(self.id)

