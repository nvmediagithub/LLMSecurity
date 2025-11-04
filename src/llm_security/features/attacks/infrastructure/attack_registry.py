from __future__ import annotations

from typing import Any, Dict

from ..domain.entities import AttackDefinition, IAttackEmulator
from ..domain.interfaces import IAttackRepository


class AttackRegistry:
    """Реестр для регистрации эмуляторов атак как плагинов."""

    def __init__(self):
        self._emulators: Dict[str, IAttackEmulator] = {}
        self._attack_definitions: Dict[str, AttackDefinition] = {}

    def register_emulator(self, attack_id: str, emulator: IAttackEmulator) -> None:
        """Зарегистрировать эмулятор атаки."""
        self._emulators[attack_id] = emulator

    def register_attack_definition(self, attack: AttackDefinition) -> None:
        """Зарегистрировать определение атаки."""
        self._attack_definitions[attack.id] = attack

    def get_emulator(self, attack_id: str) -> IAttackEmulator | None:
        """Получить эмулятор по ID атаки."""
        return self._emulators.get(attack_id)

    def get_attack_definition(self, attack_id: str) -> AttackDefinition | None:
        """Получить определение атаки по ID."""
        return self._attack_definitions.get(attack_id)

    def get_registered_attack_ids(self) -> list[str]:
        """Получить список всех зарегистрированных ID атак."""
        return list(self._emulators.keys())

    def get_registered_attacks(self) -> list[AttackDefinition]:
        """Получить все зарегистрированные определения атак."""
        return list(self._attack_definitions.values())

    def unregister_emulator(self, attack_id: str) -> None:
        """Удалить регистрацию эмулятора."""
        self._emulators.pop(attack_id, None)

    def unregister_attack_definition(self, attack_id: str) -> None:
        """Удалить регистрацию определения атаки."""
        self._attack_definitions.pop(attack_id, None)

    def clear_all(self) -> None:
        """Очистить все регистрации."""
        self._emulators.clear()
        self._attack_definitions.clear()

    def is_registered(self, attack_id: str) -> bool:
        """Проверить, зарегистрирована ли атака."""
        return attack_id in self._emulators and attack_id in self._attack_definitions

    def get_emulators_by_category(self, category: str) -> Dict[str, IAttackEmulator]:
        """Получить эмуляторы по категории."""
        return {
            attack_id: emulator
            for attack_id, emulator in self._emulators.items()
            if attack_id in self._attack_definitions
            and self._attack_definitions[attack_id].category.value == category
        }

    def get_attack_definitions_by_category(self, category: str) -> list[AttackDefinition]:
        """Получить определения атак по категории."""
        return [
            attack for attack in self._attack_definitions.values()
            if attack.category.value == category
        ]

    def bulk_register(self, attacks_and_emulators: Dict[str, tuple[AttackDefinition, IAttackEmulator]]) -> None:
        """Массово зарегистрировать атаки и эмуляторы."""
        for attack_id, (attack_def, emulator) in attacks_and_emulators.items():
            self.register_attack_definition(attack_def)
            self.register_emulator(attack_id, emulator)