from __future__ import annotations

from abc import ABC

from ...domain.entities import Decision, DefenseResult, PromptBundle
from ...domain.interfaces import IDefenseLayer


class BaseDefenseLayer(IDefenseLayer, ABC):
    id: str = "base"
    enabled: bool = True

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        return DefenseResult.allow(self.id)

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        return DefenseResult.allow(self.id)

