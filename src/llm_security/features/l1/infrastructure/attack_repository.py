from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

import yaml

from src.llm_security.core.config.loader import ConfigLoader
from ..domain.entities import L1Attack, L1AttackCategory
from ..domain.interfaces import IL1AttackRepository


class YamlL1AttackRepository(IL1AttackRepository):
    """YAML репозиторий для атак L1 уровня."""

    def __init__(self, file_path: Path | str, loader: ConfigLoader | None = None):
        self._file_path = Path(file_path)
        self._loader = loader or ConfigLoader()
        self._attacks: Dict[str, L1Attack] = {}
        self._loaded = False

    async def get_all_attacks(self) -> list[L1Attack]:
        await self._ensure_loaded()
        return list(self._attacks.values())

    async def get_attack_by_id(self, attack_id: str) -> L1Attack | None:
        await self._ensure_loaded()
        return self._attacks.get(attack_id)

    async def _ensure_loaded(self) -> None:
        """Загрузить атаки из файла, если еще не загружены."""
        if self._loaded:
            return

        if not self._file_path.exists():
            self._loaded = True
            return

        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            # В случае ошибки файл считается пустым
            data = {}

        attacks = {}
        for attack_data in data.get("attacks", []):
            attack = self._parse_attack(attack_data)
            if attack:
                attacks[attack.id] = attack

        self._attacks = attacks
        self._loaded = True

    def _parse_attack(self, data: Dict[str, Any]) -> L1Attack | None:
        """Парсить данные атаки из словаря."""
        try:
            return L1Attack(
                id=data["id"],
                name=data["name"],
                description=data.get("description", ""),
                category=L1AttackCategory(data["category"]),
                payload=data["payload"],
                expected_result=data["expected_result"],
                metadata=data.get("metadata", {}),
            )
        except (KeyError, ValueError):
            return None