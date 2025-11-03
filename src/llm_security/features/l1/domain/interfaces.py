from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .entities import L1Attack, L1AttackResult, L1LayerConfig


class IL1AttackRepository(ABC):
    """Интерфейс для репозитория атак L1."""

    @abstractmethod
    async def get_all_attacks(self) -> list[L1Attack]:
        """Получить все доступные атаки L1."""
        ...

    @abstractmethod
    async def get_attack_by_id(self, attack_id: str) -> L1Attack | None:
        """Получить атаку по ID."""
        ...


class IL1ConfigRepository(ABC):
    """Интерфейс для репозитория конфигураций L1."""

    @abstractmethod
    async def get_config(self) -> L1LayerConfig:
        """Получить конфигурацию L1 слоя."""
        ...

    @abstractmethod
    async def save_config(self, config: L1LayerConfig) -> None:
        """Сохранить конфигурацию L1 слоя."""
        ...


class IL1AttackEmulator(Protocol):
    """Интерфейс для эмулятора атак L1."""

    def emulate_attack(self, attack: L1Attack, text: str) -> L1AttackResult:
        """Эмулировать атаку на тексте."""
        ...


class IL1ResultEvaluator(Protocol):
    """Интерфейс для оценки результатов атак L1."""

    def evaluate_result(self, result: L1AttackResult) -> bool:
        """Оценить результат атаки (True - атака успешна)."""
        ...