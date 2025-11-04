from __future__ import annotations

from typing import Any

from ...defense.domain.entities import PromptBundle
from ...layers.domain.interfaces import ILayer
from ..domain.entities import AttackDefinition, AttackResult, AttackSuite
from ..domain.interfaces import (
    IAttackRepository,
    IAttackSuiteRepository,
    IAttackResultStorage,
)
from .attack_executor import AttackExecutor


class AttackManager:
    """Менеджер для управления коллекциями атак."""

    def __init__(
        self,
        attack_repository: IAttackRepository,
        suite_repository: IAttackSuiteRepository,
        executor: AttackExecutor,
        result_storage: IAttackResultStorage | None = None,
    ):
        self._attack_repository = attack_repository
        self._suite_repository = suite_repository
        self._executor = executor
        self._result_storage = result_storage

    async def get_available_attacks(self) -> list[AttackDefinition]:
        """Получить все доступные атаки."""
        return await self._attack_repository.get_all_attacks()

    async def get_attacks_by_category(self, category: str) -> list[AttackDefinition]:
        """Получить атаки по категории."""
        return await self._attack_repository.get_attacks_by_category(category)

    async def get_attacks_for_layer(self, layer_id: str) -> list[AttackDefinition]:
        """Получить атаки, направленные на конкретный слой."""
        return await self._attack_repository.get_attacks_by_layer(layer_id)

    async def get_attack_suites(self) -> list[AttackSuite]:
        """Получить все наборы атак."""
        return await self._suite_repository.get_all_suites()

    async def get_suites_for_layer(self, layer_id: str) -> list[AttackSuite]:
        """Получить наборы атак для конкретного слоя."""
        return await self._suite_repository.get_suites_by_layer(layer_id)

    async def execute_attack(
        self,
        attack_id: str,
        prompt_bundle: PromptBundle,
        layer: ILayer,
    ) -> AttackResult | None:
        """Выполнить конкретную атаку по ID."""
        attack = await self._attack_repository.get_attack_by_id(attack_id)
        if not attack:
            return None

        return await self._executor.execute_attack(attack, prompt_bundle, layer)

    async def execute_suite(
        self,
        suite_id: str,
        prompt_bundle: PromptBundle,
        layer: ILayer,
    ) -> list[AttackResult]:
        """Выполнить набор атак."""
        suite = await self._suite_repository.get_suite_by_id(suite_id)
        if not suite:
            return []

        return await self._executor.execute_attack_suite(
            suite.attacks, prompt_bundle, layer
        )

    async def execute_attacks_on_multiple_layers(
        self,
        attack_ids: list[str],
        prompt_bundle: PromptBundle,
        layers: list[ILayer],
    ) -> list[AttackResult]:
        """Выполнить несколько атак на нескольких слоях."""
        results = []

        # Получаем все атаки
        attacks = []
        for attack_id in attack_ids:
            attack = await self._attack_repository.get_attack_by_id(attack_id)
            if attack:
                attacks.append(attack)

        # Выполняем каждую атаку на каждом слое
        for attack in attacks:
            for layer in layers:
                result = await self._executor.execute_attack(attack, prompt_bundle, layer)
                results.append(result)

        return results

    async def get_attack_statistics(self, attack_id: str) -> dict[str, Any]:
        """Получить статистику выполнения атаки."""
        if not self._result_storage:
            return {}

        results = await self._result_storage.get_results_by_attack(attack_id)

        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        success_rate = successful / total if total > 0 else 0

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "average_execution_time": sum(r.metrics.get("execution_time", 0) for r in results) / total if total > 0 else 0,
        }

    async def get_layer_statistics(self, layer_id: str) -> dict[str, Any]:
        """Получить статистику атак на слой."""
        if not self._result_storage:
            return {}

        results = await self._result_storage.get_results_by_layer(layer_id)

        total = len(results)
        blocked = sum(1 for r in results if r.layer_decision == "BLOCK")
        allowed = sum(1 for r in results if r.layer_decision == "ALLOW")
        rewritten = sum(1 for r in results if r.layer_decision == "REWRITE")

        return {
            "total_attacks": total,
            "blocked": blocked,
            "allowed": allowed,
            "rewritten": rewritten,
            "block_rate": blocked / total if total > 0 else 0,
        }