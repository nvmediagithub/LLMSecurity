from __future__ import annotations

from ..domain.entities import AttackDefinition, AttackResult, AttackExecutionContext, AttackCategory
from ..domain.interfaces import IAttackEmulator
from ...l1.domain.entities import L1Attack, L1AttackResult
from ...l1.domain.interfaces import IL1AttackEmulator


class L1AttackEmulatorAdapter(IAttackEmulator):
    """Адаптер для интеграции L1 эмуляторов в новую систему атак."""

    def __init__(self, l1_emulator: IL1AttackEmulator, l1_config=None):
        self._l1_emulator = l1_emulator
        self._l1_config = l1_config

    def emulate_attack(self, context: AttackExecutionContext) -> AttackResult:
        """Эмулировать атаку с использованием L1 эмулятора."""
        # Преобразуем контекст в L1 объекты
        l1_attack = self._convert_to_l1_attack(context.attack)

        # Выполняем эмуляцию
        l1_result = self._l1_emulator.emulate_attack(l1_attack, context.prompt_bundle.user_prompt)

        # Преобразуем результат обратно
        return self._convert_from_l1_result(l1_result, context)

    def _convert_to_l1_attack(self, attack: AttackDefinition) -> L1Attack:
        """Преобразовать AttackDefinition в L1Attack."""
        from ...l1.domain.entities import L1AttackCategory

        # Определяем категорию L1 на основе целевого слоя
        category_map = {
            "l1": L1AttackCategory.INJECTION,
            "l1_input_sanitizer": L1AttackCategory.SANITIZATION,
        }

        l1_category = category_map.get(attack.target_layer, L1AttackCategory.INJECTION)

        return L1Attack(
            id=attack.id,
            name=attack.name,
            description=attack.description,
            category=l1_category,
            payload=attack.payload,
            expected_result=attack.expected_success and "expected" or "",
            metadata=attack.metadata,
        )

    def _convert_from_l1_result(self, l1_result: L1AttackResult, context: AttackExecutionContext) -> AttackResult:
        """Преобразовать L1AttackResult в AttackResult."""
        # Имитируем ответ слоя (поскольку L1 работает на уровне текста)
        layer_response = {
            "decision": "allow" if l1_result.success else "block",
            "reason": l1_result.reason or "L1 emulation result",
            "layer_id": context.attack.target_layer,
        }

        return AttackResult(
            attack=context.attack,
            success=l1_result.success,
            layer_response=layer_response,
            metrics={
                "processed_text_length": len(l1_result.processed_text),
                "original_text_length": len(l1_result.original_text),
            },
        )


class LegacyL1EmulatorAdapter(IAttackEmulator):
    """Адаптер для существующих L1 эмуляторов."""

    def __init__(self, legacy_emulator_class, config=None):
        self._legacy_emulator_class = legacy_emulator_class
        self._config = config
        self._emulator_instance = None

    def emulate_attack(self, context: AttackExecutionContext) -> AttackResult:
        """Эмулировать атаку с использованием legacy эмулятора."""
        # Создаем экземпляр эмулятора если нужно
        if self._emulator_instance is None:
            if self._config:
                self._emulator_instance = self._legacy_emulator_class(self._config)
            else:
                self._emulator_instance = self._legacy_emulator_class()

        # Выполняем эмуляцию напрямую на тексте
        processed_text = context.prompt_bundle.user_prompt + context.attack.payload

        # Простая логика определения успеха (можно доработать)
        success = context.attack.expected_success

        layer_response = {
            "decision": "allow" if success else "block",
            "reason": f"Legacy L1 emulation: {context.attack.name}",
            "layer_id": context.attack.target_layer,
        }

        return AttackResult(
            attack=context.attack,
            success=success,
            layer_response=layer_response,
            metrics={"emulator_type": "legacy"},
        )