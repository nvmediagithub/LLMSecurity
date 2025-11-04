from __future__ import annotations

import asyncio
import time
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


class AttackScheduler:
    """Планировщик для асинхронного выполнения атак."""

    def __init__(
        self,
        attack_repository: IAttackRepository,
        suite_repository: IAttackSuiteRepository,
        executor: AttackExecutor,
        result_storage: IAttackResultStorage | None = None,
        max_concurrent: int = 5,
    ):
        self._attack_repository = attack_repository
        self._suite_repository = suite_repository
        self._executor = executor
        self._result_storage = result_storage
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def schedule_attack_suite(
        self,
        suite_id: str,
        prompt_bundle: PromptBundle,
        layer: ILayer,
        delay_between_attacks: float = 0.1,
    ) -> list[AttackResult]:
        """Запланировать выполнение набора атак с задержками."""
        suite = await self._suite_repository.get_suite_by_id(suite_id)
        if not suite:
            return []

        results = []
        for attack in suite.attacks:
            async with self._semaphore:
                result = await self._executor.execute_attack(attack, prompt_bundle, layer)
                results.append(result)

                if delay_between_attacks > 0:
                    await asyncio.sleep(delay_between_attacks)

        return results

    async def schedule_parallel_execution(
        self,
        attack_ids: list[str],
        prompt_bundle: PromptBundle,
        layer: ILayer,
    ) -> list[AttackResult]:
        """Выполнить несколько атак параллельно."""
        async def execute_single(attack_id: str) -> AttackResult | None:
            async with self._semaphore:
                return await self._execute_attack_by_id(attack_id, prompt_bundle, layer)

        # Создаем задачи для параллельного выполнения
        tasks = [execute_single(attack_id) for attack_id in attack_ids]
        task_results = await asyncio.gather(*tasks)

        # Фильтруем None результаты (не найденные атаки)
        return [r for r in task_results if r is not None]

    async def schedule_layer_sweep(
        self,
        attack_id: str,
        prompt_bundle: PromptBundle,
        layers: list[ILayer],
        max_parallel_layers: int = 3,
    ) -> list[AttackResult]:
        """Выполнить атаку на нескольких слоях с ограничением параллелизма."""
        semaphore = asyncio.Semaphore(max_parallel_layers)

        async def execute_on_layer(layer: ILayer) -> AttackResult | None:
            async with semaphore:
                return await self._execute_attack_by_id(attack_id, prompt_bundle, layer)

        tasks = [execute_on_layer(layer) for layer in layers]
        task_results = await asyncio.gather(*tasks)

        return [r for r in task_results if r is not None]

    async def schedule_comprehensive_test(
        self,
        suite_ids: list[str],
        prompt_bundle: PromptBundle,
        layers: list[ILayer],
        progress_callback: callable = None,
    ) -> dict[str, list[AttackResult]]:
        """Выполнить комплексное тестирование нескольких наборов на нескольких слоях."""
        results = {}
        total_operations = len(suite_ids) * len(layers)
        completed = 0

        for suite_id in suite_ids:
            suite_results = []

            for layer in layers:
                # Выполняем набор атак на слое
                layer_results = await self.schedule_attack_suite(
                    suite_id, prompt_bundle, layer
                )
                suite_results.extend(layer_results)

                completed += 1
                if progress_callback:
                    progress_callback(completed / total_operations)

            results[suite_id] = suite_results

        return results

    async def schedule_stress_test(
        self,
        attack_id: str,
        prompt_bundle: PromptBundle,
        layer: ILayer,
        iterations: int = 100,
        batch_size: int = 10,
    ) -> dict[str, Any]:
        """Выполнить стресс-тестирование атаки."""
        start_time = time.time()
        all_results = []

        # Выполняем в батчах
        for i in range(0, iterations, batch_size):
            batch_end = min(i + batch_size, iterations)
            batch_size_actual = batch_end - i

            # Создаем батч задач
            tasks = [
                self._executor.execute_attack(attack_id, prompt_bundle, layer)
                for _ in range(batch_size_actual)
            ]

            batch_results = await asyncio.gather(*tasks)
            all_results.extend(batch_results)

        total_time = time.time() - start_time

        # Анализируем результаты
        successful = sum(1 for r in all_results if r.success)
        failed = len(all_results) - successful

        return {
            "total_iterations": iterations,
            "total_time": total_time,
            "avg_time_per_iteration": total_time / iterations,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / iterations,
            "throughput": iterations / total_time,  # атак в секунду
            "results": all_results,
        }

    async def _execute_attack_by_id(
        self,
        attack_id: str,
        prompt_bundle: PromptBundle,
        layer: ILayer,
    ) -> AttackResult | None:
        """Вспомогательный метод для выполнения атаки по ID."""
        attack = await self._attack_repository.get_attack_by_id(attack_id)
        if not attack:
            return None

        return await self._executor.execute_attack(attack, prompt_bundle, layer)