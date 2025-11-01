from __future__ import annotations

import math
import string
from typing import Iterable

from ...domain.entities import DefenseResult, PromptBundle
from .base import BaseDefenseLayer


class AdversarialSuffixLayer(BaseDefenseLayer):
    id = "L6"

    def __init__(self, *, entropy_threshold: float = 4.0, min_length: int = 20):
        self.entropy_threshold = entropy_threshold
        self.min_length = min_length

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        tail = prompt_bundle.user_prompt[-100:]
        entropy = self._shannon_entropy(tail)
        if len(tail) >= self.min_length and entropy >= self.entropy_threshold:
            cleaned = prompt_bundle.user_prompt[:-100].rstrip()
            return DefenseResult.rewrite(self.id, rewritten_text=cleaned, reason=f"entropy_tail:{entropy:.2f}")
        return DefenseResult.allow(self.id)

    @staticmethod
    def _shannon_entropy(text: str) -> float:
        if not text:
            return 0.0
        freqs: dict[str, int] = {}
        for char in text:
            if char in string.whitespace:
                continue
            freqs[char] = freqs.get(char, 0) + 1
        length = sum(freqs.values())
        if length == 0:
            return 0.0
        return -sum((count / length) * math.log2(count / length) for count in freqs.values())

