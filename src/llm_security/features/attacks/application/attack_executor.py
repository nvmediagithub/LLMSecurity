from __future__ import annotations

import asyncio
import time
from typing import Any

from ...defense.domain.entities import PromptBundle
from ...layers.domain.interfaces import ILayer
from ..domain.entities import AttackDefinition, AttackResult, AttackExecutionContext
from ..domain.interfaces import IAttackEmulator, IAttackResultStorage


class AttackExecutor:
    """Исполнитель атак на слоях защиты."""

    def __init__(
        self,
        emulator: IAttackEmulator,
        result_storage: IAttackResultStorage | None = None,
    ):
        self._emulator = emulator
        self._result_storage = result_storage

    async def execute_attack(
        self,
        attack: AttackDefinition,
        prompt_bundle: PromptBundle,
        layer: ILayer,
    ) -> AttackResult:
        """Выполнить одну атаку на слое."""
        start_time = time.time()

        # Создаем контекст выполнения
        context = AttackExecutionContext(
            attack=attack,
            prompt_bundle=prompt_bundle,
            layer_instance=layer,
            metadata={"executor": "AttackExecutor"},
        )

        try:
            # Эмулируем атаку
            result = self._emulator.emulate_attack(context)

            # Добавляем метрики выполнения
            execution_time = time.time() - start_time
            result.metrics.update({
                "execution_time": execution_time,
                "executor": "AttackExecutor",
                "layer_id": layer.id,
                "layer_enabled": layer.enabled,
            })

            # Сохраняем результат если есть хранилище
            if self._result_storage:
                await self._result_storage.save_result(result)

            return result

        except Exception as e:
            # Создаем результат с ошибкой
            error_result = AttackResult(
                attack=attack,
                success=False,
                error=str(e),
                metrics={"execution_time": time.time() - start_time, "error": True},
            )

            if self._result_storage:
                await self._result_storage.save_result(error_result)

            return error_result

    async def execute_attack_suite(
        self,
        attacks: list[AttackDefinition],
        prompt_bundle: PromptBundle,
        layer: ILayer,
    ) -> list[AttackResult]:
        """Выполнить набор атак на слое."""
        results = []

        for attack in attacks:
            result = await self.execute_attack(attack, prompt_bundle, layer)
            results.append(result)

            # Небольшая пауза между атаками
            await asyncio.sleep(0.01)

        return results

    async def execute_attack_on_multiple_layers(
        self,
        attack: AttackDefinition,
        prompt_bundle: PromptBundle,
        layers: list[ILayer],
    ) -> list[AttackResult]:
        """Выполнить одну атаку на нескольких слоях."""
        results = []

        for layer in layers:
            result = await self.execute_attack(attack, prompt_bundle, layer)
            results.append(result)

        return results