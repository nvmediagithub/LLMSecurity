from __future__ import annotations

from typing import Protocol, Any, Dict, runtime_checkable

from ...defense.domain.entities import DefenseResult, PromptBundle


@runtime_checkable
class ILayer(Protocol):
    """Единый интерфейс для всех слоев защиты (L1-L9)."""

    id: str
    enabled: bool

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        ...

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        ...