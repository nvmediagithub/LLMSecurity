from __future__ import annotations

from typing import Any

from ..domain.entities import AttackDefinition, AttackSuite
from ..domain.interfaces import IAttackRepository, IAttackSuiteRepository


class InMemoryAttackRepository(IAttackRepository):
    """In-memory репозиторий атак."""

    def __init__(self, attacks: list[AttackDefinition] | None = None):
        self._attacks = attacks or []
        self._attacks_by_id = {attack.id: attack for attack in self._attacks}
        self._attacks_by_category: dict[str, list[AttackDefinition]] = {}
        self._attacks_by_layer: dict[str, list[AttackDefinition]] = {}

        # Индексируем атаки
        self._build_indexes()

    async def get_all_attacks(self) -> list[AttackDefinition]:
        """Получить все доступные атаки."""
        return self._attacks.copy()

    async def get_attack_by_id(self, attack_id: str) -> AttackDefinition | None:
        """Получить атаку по ID."""
        return self._attacks_by_id.get(attack_id)

    async def get_attacks_by_category(self, category: str) -> list[AttackDefinition]:
        """Получить атаки по категории."""
        return self._attacks_by_category.get(category, [])

    async def get_attacks_by_layer(self, layer_id: str) -> list[AttackDefinition]:
        """Получить атаки, направленные на конкретный слой."""
        return self._attacks_by_layer.get(layer_id, [])

    def add_attack(self, attack: AttackDefinition) -> None:
        """Добавить атаку в репозиторий."""
        if attack.id in self._attacks_by_id:
            return  # Атака уже существует

        self._attacks.append(attack)
        self._attacks_by_id[attack.id] = attack

        # Обновляем индексы
        self._update_indexes_for_attack(attack)

    def remove_attack(self, attack_id: str) -> None:
        """Удалить атаку из репозитория."""
        if attack_id not in self._attacks_by_id:
            return

        attack = self._attacks_by_id[attack_id]
        self._attacks.remove(attack)
        del self._attacks_by_id[attack_id]

        # Перестраиваем индексы
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Построить индексы для быстрого поиска."""
        self._attacks_by_category.clear()
        self._attacks_by_layer.clear()

        for attack in self._attacks:
            # Индекс по категории
            category = attack.category.value
            if category not in self._attacks_by_category:
                self._attacks_by_category[category] = []
            self._attacks_by_category[category].append(attack)

            # Индекс по слою
            if attack.target_layer not in self._attacks_by_layer:
                self._attacks_by_layer[attack.target_layer] = []
            self._attacks_by_layer[attack.target_layer].append(attack)

    def _update_indexes_for_attack(self, attack: AttackDefinition) -> None:
        """Обновить индексы для новой атаки."""
        # Индекс по категории
        category = attack.category.value
        if category not in self._attacks_by_category:
            self._attacks_by_category[category] = []
        self._attacks_by_category[category].append(attack)

        # Индекс по слою
        if attack.target_layer not in self._attacks_by_layer:
            self._attacks_by_layer[attack.target_layer] = []
        self._attacks_by_layer[attack.target_layer].append(attack)


class InMemoryAttackSuiteRepository(IAttackSuiteRepository):
    """In-memory репозиторий наборов атак."""

    def __init__(self, suites: list[AttackSuite] | None = None):
        self._suites = suites or []
        self._suites_by_id = {suite.id: suite for suite in self._suites}
        self._suites_by_layer: dict[str, list[AttackSuite]] = {}

        # Индексируем наборы
        self._build_suite_indexes()

    async def get_all_suites(self) -> list[AttackSuite]:
        """Получить все наборы атак."""
        return self._suites.copy()

    async def get_suite_by_id(self, suite_id: str) -> AttackSuite | None:
        """Получить набор атак по ID."""
        return self._suites_by_id.get(suite_id)

    async def get_suites_by_layer(self, layer_id: str) -> list[AttackSuite]:
        """Получить наборы атак для конкретного слоя."""
        return self._suites_by_layer.get(layer_id, [])

    def add_suite(self, suite: AttackSuite) -> None:
        """Добавить набор атак."""
        if suite.id in self._suites_by_id:
            return  # Набор уже существует

        self._suites.append(suite)
        self._suites_by_id[suite.id] = suite

        # Обновляем индексы
        self._update_suite_indexes_for_suite(suite)

    def remove_suite(self, suite_id: str) -> None:
        """Удалить набор атак."""
        if suite_id not in self._suites_by_id:
            return

        suite = self._suites_by_id[suite_id]
        self._suites.remove(suite)
        del self._suites_by_id[suite_id]

        # Перестраиваем индексы
        self._build_suite_indexes()

    def _build_suite_indexes(self) -> None:
        """Построить индексы для наборов."""
        self._suites_by_layer.clear()

        for suite in self._suites:
            # Индекс по слою
            if suite.target_layer not in self._suites_by_layer:
                self._suites_by_layer[suite.target_layer] = []
            self._suites_by_layer[suite.target_layer].append(suite)

    def _update_suite_indexes_for_suite(self, suite: AttackSuite) -> None:
        """Обновить индексы для нового набора."""
        if suite.target_layer not in self._suites_by_layer:
            self._suites_by_layer[suite.target_layer] = []
        self._suites_by_layer[suite.target_layer].append(suite)