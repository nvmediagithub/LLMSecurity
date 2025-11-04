from __future__ import annotations

from typing import Any, Dict, Type

from ..domain.entities import AttackDefinition, IAttackEmulator
from ..domain.interfaces import IAttackRepository, IAttackSuiteRepository


class AttackFactory:
    """Фабрика для создания экземпляров атак и эмуляторов."""

    def __init__(self):
        self._emulator_classes: Dict[str, Type[IAttackEmulator]] = {}
        self._attack_templates: Dict[str, Dict[str, Any]] = {}

    def register_emulator_class(self, attack_type: str, emulator_class: Type[IAttackEmulator]) -> None:
        """Зарегистрировать класс эмулятора для типа атаки."""
        self._emulator_classes[attack_type] = emulator_class

    def register_attack_template(self, attack_type: str, template: Dict[str, Any]) -> None:
        """Зарегистрировать шаблон для создания атак."""
        self._attack_templates[attack_type] = template

    def create_emulator(self, attack_type: str, **kwargs) -> IAttackEmulator | None:
        """Создать экземпляр эмулятора."""
        emulator_class = self._emulator_classes.get(attack_type)
        if not emulator_class:
            return None

        try:
            return emulator_class(**kwargs)
        except Exception:
            return None

    def create_attack_from_template(
        self,
        attack_type: str,
        attack_id: str,
        name: str,
        **overrides
    ) -> AttackDefinition | None:
        """Создать атаку из шаблона."""
        template = self._attack_templates.get(attack_type)
        if not template:
            return None

        # Объединяем шаблон с overrides
        attack_data = {**template, **overrides}
        attack_data["id"] = attack_id
        attack_data["name"] = name

        try:
            return AttackDefinition(**attack_data)
        except Exception:
            return None

    def create_attack_suite(
        self,
        suite_id: str,
        name: str,
        target_layer: str,
        attack_configs: list[Dict[str, Any]],
    ) -> Any:  # AttackSuite
        """Создать набор атак."""
        from ..domain.entities import AttackSuite

        attacks = []
        for config in attack_configs:
            attack = self.create_attack_from_template(**config)
            if attack:
                attacks.append(attack)

        return AttackSuite(
            id=suite_id,
            name=name,
            description=f"Suite for {target_layer}",
            target_layer=target_layer,
            attacks=attacks,
        )

    def create_repository_from_registry(self, registry: Any) -> IAttackRepository:
        """Создать репозиторий из реестра."""
        from .repositories import InMemoryAttackRepository

        return InMemoryAttackRepository(registry.get_registered_attacks())

    def create_suite_repository_from_registry(self, registry: Any) -> IAttackSuiteRepository:
        """Создать репозиторий наборов из реестра."""
        # Для простоты возвращаем пустой репозиторий
        # В реальной реализации нужно создать логику для создания наборов
        from .repositories import InMemoryAttackSuiteRepository

        return InMemoryAttackSuiteRepository([])

    def bulk_create_attacks(self, attack_configs: list[Dict[str, Any]]) -> list[AttackDefinition]:
        """Массово создать атаки из конфигураций."""
        attacks = []
        for config in attack_configs:
            attack = self.create_attack_from_template(**config)
            if attack:
                attacks.append(attack)
        return attacks