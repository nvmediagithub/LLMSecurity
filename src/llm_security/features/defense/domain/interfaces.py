from __future__ import annotations

from typing import Protocol

from .entities import DefenseResult, PromptBundle


class IDefenseLayer(Protocol):
    """Контракт для защитных слоёв."""

    id: str
    enabled: bool

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        ...

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        ...

