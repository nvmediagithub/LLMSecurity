from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Protocol
import time


class AttackCategory(str, Enum):
    """Категории атак."""

    L1_INPUT_SANITIZATION = "l1_input_sanitization"
    L2_PROMPT_CLASSIFICATION = "l2_prompt_classification"
    L3_CONTEXT_FIREWALL = "l3_context_firewall"
    L4_POLICY_ENGINE = "l4_policy_engine"
    L5_TOOL_GATEKEEPER = "l5_tool_gatekeeper"
    L6_SUFFIX_DETECTOR = "l6_suffix_detector"
    L7_OUTPUT_GUARD = "l7_output_guard"
    L8_MEMORY_GUARD = "l8_memory_guard"
    L9_RATE_SCOPE_GUARD = "l9_rate_scope_guard"
    HTML_INJECTION = "html_injection"
    PROMPT_INJECTION = "prompt_injection"
    DATA_LEAKAGE = "data_leakage"


@dataclass(slots=True)
class AttackDefinition:
    """Определение атаки."""

    id: str
    name: str
    description: str
    category: AttackCategory
    payload: str
    target_layer: str  # ID слоя, на который направлена атака
    expected_success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AttackResult:
    """Результат выполнения атаки."""

    attack: AttackDefinition
    success: bool
    layer_response: Optional[dict[str, Any]] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None

    @property
    def layer_decision(self) -> Optional[str]:
        """Получить решение слоя защиты."""
        if self.layer_response:
            return self.layer_response.get("decision")
        return None

    @property
    def layer_reason(self) -> Optional[str]:
        """Получить причину решения слоя."""
        if self.layer_response:
            return self.layer_response.get("reason")
        return None


@dataclass(slots=True)
class AttackSuite:
    """Набор атак для тестирования слоя."""

    id: str
    name: str
    description: str
    target_layer: str
    attacks: list[AttackDefinition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AttackExecutionContext:
    """Контекст выполнения атаки."""

    attack: AttackDefinition
    prompt_bundle: Any  # PromptBundle из defense.domain
    layer_instance: Any  # ILayer instance
    metadata: dict[str, Any] = field(default_factory=dict)


class IAttackEmulator(Protocol):
    """Единый интерфейс для всех эмуляторов атак."""

    def emulate_attack(self, context: AttackExecutionContext) -> AttackResult:
        """Эмулировать атаку в заданном контексте."""
        ...


class IAttackResultEvaluator(Protocol):
    """Интерфейс для оценки результатов атак."""

    def evaluate_result(self, result: AttackResult) -> bool:
        """Оценить результат атаки (True - атака успешна)."""
        ...