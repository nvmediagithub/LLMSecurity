from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Decision(str, Enum):
    """Возможные решения защитного слоя."""

    ALLOW = "allow"
    BLOCK = "block"
    REWRITE = "rewrite"
    ESCALATE = "escalate"


@dataclass(slots=True)
class DefenseResult:
    """Результат работы слоя защиты."""

    decision: Decision
    reason: str = ""
    layer_id: str = ""
    rewritten_text: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allow(cls, layer_id: str, *, reason: str = "", metadata: Optional[dict[str, Any]] = None) -> "DefenseResult":
        return cls(decision=Decision.ALLOW, layer_id=layer_id, reason=reason, metadata=metadata or {})

    @classmethod
    def block(cls, layer_id: str, *, reason: str, metadata: Optional[dict[str, Any]] = None) -> "DefenseResult":
        return cls(decision=Decision.BLOCK, layer_id=layer_id, reason=reason, metadata=metadata or {})

    @classmethod
    def rewrite(cls, layer_id: str, *, rewritten_text: str, reason: str = "", metadata: Optional[dict[str, Any]] = None) -> "DefenseResult":
        return cls(
            decision=Decision.REWRITE,
            layer_id=layer_id,
            reason=reason,
            rewritten_text=rewritten_text,
            metadata=metadata or {},
        )

    @classmethod
    def escalate(cls, layer_id: str, *, reason: str, metadata: Optional[dict[str, Any]] = None) -> "DefenseResult":
        return cls(decision=Decision.ESCALATE, layer_id=layer_id, reason=reason, metadata=metadata or {})


@dataclass(slots=True)
class PromptBundle:
    """Структура, передаваемая в защиты и модель."""

    system_prompt: str
    user_prompt: str
    context: dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs: Any) -> "PromptBundle":
        data = {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "context": dict(self.context),
        }
        data.update(kwargs)
        return PromptBundle(**data)

