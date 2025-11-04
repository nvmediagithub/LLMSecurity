from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .entities import AttackDefinition, AttackResult, AttackSuite, AttackExecutionContext


class IAttackEmulator(Protocol):
    """Единый интерфейс для всех эмуляторов атак."""

    def emulate_attack(self, context: AttackExecutionContext) -> AttackResult:
        """Эмулировать атаку в заданном контексте."""
        ...


class IAttackRepository(ABC):
    """Интерфейс для репозитория атак."""

    @abstractmethod
    async def get_all_attacks(self) -> list[AttackDefinition]:
        """Получить все доступные атаки."""
        ...

    @abstractmethod
    async def get_attack_by_id(self, attack_id: str) -> AttackDefinition | None:
        """Получить атаку по ID."""
        ...

    @abstractmethod
    async def get_attacks_by_category(self, category: str) -> list[AttackDefinition]:
        """Получить атаки по категории."""
        ...

    @abstractmethod
    async def get_attacks_by_layer(self, layer_id: str) -> list[AttackDefinition]:
        """Получить атаки, направленные на конкретный слой."""
        ...


class IAttackSuiteRepository(ABC):
    """Интерфейс для репозитория наборов атак."""

    @abstractmethod
    async def get_all_suites(self) -> list[AttackSuite]:
        """Получить все наборы атак."""
        ...

    @abstractmethod
    async def get_suite_by_id(self, suite_id: str) -> AttackSuite | None:
        """Получить набор атак по ID."""
        ...

    @abstractmethod
    async def get_suites_by_layer(self, layer_id: str) -> list[AttackSuite]:
        """Получить наборы атак для конкретного слоя."""
        ...


class IAttackResultStorage(ABC):
    """Интерфейс для хранения результатов атак."""

    @abstractmethod
    async def save_result(self, result: AttackResult) -> None:
        """Сохранить результат атаки."""
        ...

    @abstractmethod
    async def get_results_by_attack(self, attack_id: str) -> list[AttackResult]:
        """Получить результаты по ID атаки."""
        ...

    @abstractmethod
    async def get_results_by_layer(self, layer_id: str) -> list[AttackResult]:
        """Получить результаты по ID слоя."""
        ...

    @abstractmethod
    async def get_recent_results(self, limit: int = 100) -> list[AttackResult]:
        """Получить последние результаты атак."""
        ...