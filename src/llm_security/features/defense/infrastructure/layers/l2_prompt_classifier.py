from __future__ import annotations

import re
from typing import Iterable, Sequence

from ...domain.entities import DefenseResult, PromptBundle
from .base import BaseDefenseLayer


SUSPICIOUS_PATTERNS: Sequence[re.Pattern[str]] = [
    re.compile(r"\bignore (all|previous) instructions", re.IGNORECASE),
    re.compile(r"\bигнорируй\b", re.IGNORECASE),
    re.compile(r"\breveal (hidden|system) prompt", re.IGNORECASE),
    re.compile(r"\bраскрой\b.*\bпромпт\b", re.IGNORECASE),
    re.compile(r"\bDAN\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"\bmalware\b", re.IGNORECASE),
]


class PromptClassifierLayer(BaseDefenseLayer):
    id = "L2"

    def __init__(
        self,
        *,
        block_keywords: Iterable[str] | None = None,
        threshold: float = 0.5,
        classifier: str | None = None,
    ):
        self.block_keywords = {kw.lower() for kw in (block_keywords or [])}
        self.threshold = threshold
        self.classifier = classifier

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        text = f"{prompt_bundle.system_prompt}\n{prompt_bundle.user_prompt}".lower()
        score = self._score(text)
        if score >= self.threshold or self._has_block_keyword(text):
            return DefenseResult.block(self.id, reason=f"classifier_score={score:.2f}", metadata={"score": f"{score:.2f}"})
        return DefenseResult.allow(self.id)

    def _has_block_keyword(self, text: str) -> bool:
        return any(keyword in text for keyword in self.block_keywords)

    @staticmethod
    def _score(text: str) -> float:
        hits = sum(1 for pattern in SUSPICIOUS_PATTERNS if pattern.search(text))
        return min(1.0, hits / max(1, len(SUSPICIOUS_PATTERNS)))
