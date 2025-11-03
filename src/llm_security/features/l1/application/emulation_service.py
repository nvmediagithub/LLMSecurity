from __future__ import annotations

from ..domain.entities import L1Attack, L1AttackResult, L1LayerConfig
from ..domain.interfaces import IL1AttackEmulator, IL1AttackRepository, IL1ConfigRepository


class L1EmulationService:
    """Сервис для эмуляции атак L1 уровня."""

    def __init__(
        self,
        attack_repo: IL1AttackRepository,
        config_repo: IL1ConfigRepository,
        emulator: IL1AttackEmulator,
    ):
        self._attack_repo = attack_repo
        self._config_repo = config_repo
        self._emulator = emulator

    async def emulate_all_attacks(self, text: str) -> list[L1AttackResult]:
        """Эмулировать все доступные атаки на тексте."""
        attacks = await self._attack_repo.get_all_attacks()
        config = await self._config_repo.get_config()

        results = []
        for attack in attacks:
            if self._is_attack_enabled(attack, config):
                result = self._emulator.emulate_attack(attack, text)
                results.append(result)

        return results

    async def emulate_attack(self, attack_id: str, text: str) -> L1AttackResult | None:
        """Эмулировать конкретную атаку по ID."""
        attack = await self._attack_repo.get_attack_by_id(attack_id)
        if not attack:
            return None

        config = await self._config_repo.get_config()
        if not self._is_attack_enabled(attack, config):
            return None

        return self._emulator.emulate_attack(attack, text)

    def _is_attack_enabled(self, attack: L1Attack, config: L1LayerConfig) -> bool:
        """Проверить, включена ли атака в конфигурации."""
        return attack.category in config.enabled_categories or not config.enabled_categories