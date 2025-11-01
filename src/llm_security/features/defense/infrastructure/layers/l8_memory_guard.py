from __future__ import annotations

from ...domain.entities import DefenseResult, PromptBundle
from .base import BaseDefenseLayer


class MemoryGuardLayer(BaseDefenseLayer):
    id = "L8"

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        memory_flag = prompt_bundle.context.get("memory_write")
        if memory_flag and "instruction" in str(memory_flag).lower():
            return DefenseResult.escalate(self.id, reason="memory_instruction_write")
        return DefenseResult.allow(self.id)

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        if "save this instruction" in response_text.lower():
            return DefenseResult.block(self.id, reason="memory_save_instruction")
        return DefenseResult.allow(self.id)

