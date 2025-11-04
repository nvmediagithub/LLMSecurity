from __future__ import annotations

import asyncio
from typing import Any

from ...defense.domain.entities import PromptBundle, DefenseResult
from ...layers.domain.interfaces import ILayer
from ..domain.entities import AttackDefinition, AttackResult, AttackExecutionContext
from ..domain.interfaces import IAttackEmulator, IAttackResultStorage
from ..application.attack_executor import AttackExecutor


class MultiLayerAttackExecutor:
    """Исполнитель атак на нескольких слоях защиты."""

    def __init__(
        self,
        attack_emulator: IAttackEmulator,
        result_storage: IAttackResultStorage | None = None,
    ):
        self._emulator = attack_emulator
        self._result_storage = result_storage

    async def execute_on_pipeline(
        self,
        attack: AttackDefinition,
        prompt_bundle: PromptBundle,
        layers: list[ILayer],
    ) -> dict[str, Any]:
        """Выполнить атаку на конвейере слоев защиты."""
        current_bundle = prompt_bundle
        layer_results = []
        attack_successful = True

        # Проходим через все слои
        for layer in layers:
            # Создаем контекст для текущего слоя
            context = AttackExecutionContext(
                attack=attack,
                prompt_bundle=current_bundle,
                layer_instance=layer,
                metadata={"pipeline_execution": True, "layer_order": len(layer_results)},
            )

            # Эмулируем атаку на слое
            attack_result = self._emulator.emulate_attack(context)

            # Сохраняем результат если есть хранилище
            if self._result_storage:
                await self._result_storage.save_result(attack_result)

            # Добавляем в результаты
            layer_results.append({
                "layer_id": layer.id,
                "layer_enabled": layer.enabled,
                "attack_result": attack_result,
            })

            # Если слой блокирует атаку, прекращаем выполнение
            if attack_result.layer_response and attack_result.layer_response.get("decision") == "block":
                attack_successful = False
                break

            # Обновляем bundle для следующего слоя
            if attack_result.layer_response and attack_result.layer_response.get("decision") == "rewrite":
                current_bundle = current_bundle.update(
                    user_prompt=attack_result.layer_response.get("rewritten_text", current_bundle.user_prompt)
                )

        return {
            "attack": attack,
            "successful": attack_successful,
            "layer_results": layer_results,
            "final_bundle": current_bundle,
            "pipeline_length": len(layers),
            "blocked_at_layer": next(
                (r["layer_id"] for r in layer_results if r["attack_result"].layer_response and
                 r["attack_result"].layer_response.get("decision") == "block"),
                None
            ),
        }

    async def execute_attack_matrix(
        self,
        attacks: list[AttackDefinition],
        prompt_bundle: PromptBundle,
        layers: list[ILayer],
        parallel_layers: bool = False,
    ) -> list[dict[str, Any]]:
        """Выполнить матрицу атак на матрице слоев."""
        results = []

        if parallel_layers:
            # Параллельное выполнение по слоям
            tasks = []
            for attack in attacks:
                for layer in layers:
                    task = self._execute_single_attack_on_layer(attack, prompt_bundle, layer)
                    tasks.append(task)

            batch_results = await asyncio.gather(*tasks)

            # Группируем результаты по атакам
            for i, attack in enumerate(attacks):
                attack_results = batch_results[i * len(layers):(i + 1) * len(layers)]
                results.append({
                    "attack": attack,
                    "layer_results": attack_results,
                })
        else:
            # Последовательное выполнение
            for attack in attacks:
                attack_results = []
                for layer in layers:
                    result = await self._execute_single_attack_on_layer(attack, prompt_bundle, layer)
                    attack_results.append(result)

                results.append({
                    "attack": attack,
                    "layer_results": attack_results,
                })

        return results

    async def execute_layer_bypass_test(
        self,
        attack: AttackDefinition,
        prompt_bundle: PromptBundle,
        layers: list[ILayer],
    ) -> dict[str, Any]:
        """Тестирование обхода конкретного слоя."""
        results = {}

        # Тестируем атаку на каждом слое по отдельности
        for i, target_layer in enumerate(layers):
            # Создаем подмножество слоев до целевого (включая его)
            pipeline_layers = layers[:i + 1]

            pipeline_result = await self.execute_on_pipeline(attack, prompt_bundle, pipeline_layers)

            results[target_layer.id] = {
                "layer_id": target_layer.id,
                "pipeline_result": pipeline_result,
                "bypassed": pipeline_result["successful"],
                "blocked_by_previous": any(
                    r["attack_result"].layer_response and
                    r["attack_result"].layer_response.get("decision") == "block"
                    for r in pipeline_result["layer_results"][:-1]  # Все кроме последнего
                ),
            }

        return {
            "attack": attack,
            "layer_bypass_results": results,
            "overall_success": any(r["bypassed"] for r in results.values()),
            "weakest_layer": next(
                (layer_id for layer_id, r in results.items() if not r["bypassed"]),
                None
            ),
        }

    async def execute_defense_in_depth_analysis(
        self,
        attacks: list[AttackDefinition],
        prompt_bundle: PromptBundle,
        layers: list[ILayer],
    ) -> dict[str, Any]:
        """Анализ defense-in-depth для набора атак."""
        analysis_results = []

        for attack in attacks:
            # Выполняем атаку на полном конвейере
            full_pipeline_result = await self.execute_on_pipeline(attack, prompt_bundle, layers)

            # Выполняем bypass тест
            bypass_result = await self.execute_layer_bypass_test(attack, prompt_bundle, layers)

            analysis_results.append({
                "attack": attack,
                "full_pipeline": full_pipeline_result,
                "bypass_analysis": bypass_result,
                "defense_effectiveness": self._calculate_defense_effectiveness(full_pipeline_result, bypass_result),
            })

        # Агрегируем результаты
        total_attacks = len(attacks)
        successful_attacks = sum(1 for r in analysis_results if r["full_pipeline"]["successful"])
        blocked_attacks = total_attacks - successful_attacks

        return {
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "blocked_attacks": blocked_attacks,
            "success_rate": successful_attacks / total_attacks if total_attacks > 0 else 0,
            "attack_results": analysis_results,
            "layer_effectiveness": self._calculate_layer_effectiveness(analysis_results, layers),
        }

    def _calculate_defense_effectiveness(
        self,
        pipeline_result: dict[str, Any],
        bypass_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Рассчитать эффективность защиты."""
        layer_results = pipeline_result["layer_results"]

        effectiveness = {
            "overall_blocked": not pipeline_result["successful"],
            "layers_contributed": len([r for r in layer_results if not r["attack_result"].success]),
            "first_block_layer": next(
                (r["layer_id"] for r in layer_results if r["attack_result"].layer_response and
                 r["attack_result"].layer_response.get("decision") == "block"),
                None
            ),
            "defense_layers_used": len(layer_results),
        }

        return effectiveness

    def _calculate_layer_effectiveness(
        self,
        analysis_results: list[dict[str, Any]],
        layers: list[ILayer],
    ) -> dict[str, Any]:
        """Рассчитать эффективность каждого слоя."""
        layer_stats = {}

        for layer in layers:
            layer_id = layer.id
            layer_blocks = 0
            layer_total = 0

            for result in analysis_results:
                bypass_info = result["bypass_analysis"]["layer_bypass_results"].get(layer_id)
                if bypass_info:
                    layer_total += 1
                    if not bypass_info["bypassed"]:
                        layer_blocks += 1

            layer_stats[layer_id] = {
                "attacks_tested": layer_total,
                "attacks_blocked": layer_blocks,
                "block_rate": layer_blocks / layer_total if layer_total > 0 else 0,
                "layer_enabled": layer.enabled,
            }

        return layer_stats

    async def _execute_single_attack_on_layer(
        self,
        attack: AttackDefinition,
        prompt_bundle: PromptBundle,
        layer: ILayer,
    ) -> AttackResult:
        """Вспомогательный метод для выполнения атаки на одном слое."""
        context = AttackExecutionContext(
            attack=attack,
            prompt_bundle=prompt_bundle,
            layer_instance=layer,
        )

        result = self._emulator.emulate_attack(context)

        if self._result_storage:
            await self._result_storage.save_result(result)

        return result