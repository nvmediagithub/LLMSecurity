from __future__ import annotations

import re
import unicodedata

from ...domain.entities import DefenseResult, PromptBundle
from .base import BaseDefenseLayer

ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]")


class InputSanitizerLayer(BaseDefenseLayer):
    id = "L1"

    def __init__(self, *, max_length: int = 5000):
        self.max_length = max_length

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        cleaned = self._sanitize(prompt_bundle.user_prompt)
        if len(cleaned) > self.max_length:
            cleaned = cleaned[: self.max_length]
        if cleaned != prompt_bundle.user_prompt:
            return DefenseResult.rewrite(self.id, rewritten_text=cleaned, reason="normalized")
        return DefenseResult.allow(self.id)

    @staticmethod
    def _sanitize(text: str) -> str:
        normalized = unicodedata.normalize("NFC", text)
        no_zero_width = ZERO_WIDTH_RE.sub("", normalized)
        stripped = no_zero_width.strip()
        return stripped

