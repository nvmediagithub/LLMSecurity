from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class L1AttackCategory(str, Enum):
    """Категории атак L1 уровня."""

    INJECTION = "injection"
    NORMALIZATION = "normalization"
    SANITIZATION = "sanitization"
    LENGTH_ATTACK = "length_attack"
    ENCODING_ATTACK = "encoding_attack"


@dataclass(slots=True)
class L1Attack:
    """Представляет атаку L1 уровня."""

    id: str
    name: str
    description: str
    category: L1AttackCategory
    payload: str
    expected_result: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class L1LayerConfig:
    """Конфигурация для L1 слоя."""

    max_length: int = 5000
    enabled_categories: set[L1AttackCategory] = field(default_factory=lambda: set(L1AttackCategory))
    sanitize_zero_width: bool = True
    normalize_unicode: bool = True


@dataclass(slots=True)
class L1AttackResult:
    """Результат эмуляции атаки L1."""

    attack: L1Attack
    success: bool
    original_text: str
    processed_text: str
    reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)