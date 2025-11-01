from __future__ import annotations

import time
from collections import defaultdict

from ...domain.entities import DefenseResult, PromptBundle
from .base import BaseDefenseLayer


class RateScopeGuardLayer(BaseDefenseLayer):
    id = "L9"

    def __init__(self, *, max_calls_per_minute: int = 60, max_prompt_tokens: int = 8000):
        self.max_calls_per_minute = max_calls_per_minute
        self.max_prompt_tokens = max_prompt_tokens
        self._calls = defaultdict(list)

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        now = time.time()
        key = prompt_bundle.context.get("model_id", "default")
        window = self._calls[key]
        window.append(now)
        # purge
        threshold = now - 60
        while window and window[0] < threshold:
            window.pop(0)
        if len(window) > self.max_calls_per_minute:
            return DefenseResult.escalate(self.id, reason="rate_limit_exceeded")
        if len(prompt_bundle.user_prompt) > self.max_prompt_tokens:
            return DefenseResult.escalate(self.id, reason="prompt_too_large")
        return DefenseResult.allow(self.id)

