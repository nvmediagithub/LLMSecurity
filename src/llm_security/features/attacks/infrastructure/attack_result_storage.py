from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from ..domain.entities import AttackResult
from ..domain.interfaces import IAttackResultStorage


class InMemoryAttackResultStorage(IAttackResultStorage):
    """In-memory хранилище результатов атак."""

    def __init__(self):
        self._results: list[AttackResult] = []
        self._results_by_attack: dict[str, list[AttackResult]] = {}
        self._results_by_layer: dict[str, list[AttackResult]] = {}

    async def save_result(self, result: AttackResult) -> None:
        """Сохранить результат атаки."""
        self._results.append(result)

        # Индексируем по атаке
        if result.attack.id not in self._results_by_attack:
            self._results_by_attack[result.attack.id] = []
        self._results_by_attack[result.attack.id].append(result)

        # Индексируем по слою
        if result.attack.target_layer not in self._results_by_layer:
            self._results_by_layer[result.attack.target_layer] = []
        self._results_by_layer[result.attack.target_layer].append(result)

    async def get_results_by_attack(self, attack_id: str) -> list[AttackResult]:
        """Получить результаты по ID атаки."""
        return self._results_by_attack.get(attack_id, [])

    async def get_results_by_layer(self, layer_id: str) -> list[AttackResult]:
        """Получить результаты по ID слоя."""
        return self._results_by_layer.get(layer_id, [])

    async def get_recent_results(self, limit: int = 100) -> list[AttackResult]:
        """Получить последние результаты атак."""
        return sorted(self._results, key=lambda r: r.timestamp, reverse=True)[:limit]

    def clear(self) -> None:
        """Очистить хранилище."""
        self._results.clear()
        self._results_by_attack.clear()
        self._results_by_layer.clear()


class FileAttackResultStorage(IAttackResultStorage):
    """Файловое хранилище результатов атак."""

    def __init__(self, storage_dir: str | Path):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._results_file = self._storage_dir / "attack_results.jsonl"
        self._index_file = self._storage_dir / "index.json"

        # Загружаем индекс при инициализации
        self._attack_index: dict[str, list[int]] = {}
        self._layer_index: dict[str, list[int]] = {}
        self._load_index()

    async def save_result(self, result: AttackResult) -> None:
        """Сохранить результат атаки."""
        # Получаем текущую позицию файла
        position = self._results_file.stat().st_size if self._results_file.exists() else 0

        # Сериализуем результат
        result_data = {
            "attack_id": result.attack.id,
            "attack_name": result.attack.name,
            "target_layer": result.attack.target_layer,
            "success": result.success,
            "layer_response": result.layer_response,
            "metrics": result.metrics,
            "timestamp": result.timestamp,
            "error": result.error,
        }

        # Записываем в файл
        async with asyncio.Lock():
            with open(self._results_file, "a", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False)
                f.write("\n")

            # Обновляем индекс
            self._update_index(result, position)

    async def get_results_by_attack(self, attack_id: str) -> list[AttackResult]:
        """Получить результаты по ID атаки."""
        positions = self._attack_index.get(attack_id, [])
        return await self._load_results_by_positions(positions)

    async def get_results_by_layer(self, layer_id: str) -> list[AttackResult]:
        """Получить результаты по ID слоя."""
        positions = self._layer_index.get(layer_id, [])
        return await self._load_results_by_positions(positions)

    async def get_recent_results(self, limit: int = 100) -> list[AttackResult]:
        """Получить последние результаты атак."""
        if not self._results_file.exists():
            return []

        results = []
        with open(self._results_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]  # Берем последние limit строк

            for line in lines:
                data = json.loads(line.strip())
                result = self._deserialize_result(data)
                results.append(result)

        return results

    async def _load_results_by_positions(self, positions: list[int]) -> list[AttackResult]:
        """Загрузить результаты по позициям в файле."""
        results = []

        async with asyncio.Lock():
            with open(self._results_file, "r", encoding="utf-8") as f:
                for pos in positions:
                    f.seek(pos)
                    line = f.readline()
                    if line:
                        data = json.loads(line.strip())
                        result = self._deserialize_result(data)
                        results.append(result)

        return results

    def _deserialize_result(self, data: dict[str, Any]) -> AttackResult:
        """Десериализовать результат из данных."""
        from ..domain.entities import AttackDefinition, AttackResult, AttackCategory

        attack = AttackDefinition(
            id=data["attack_id"],
            name=data["attack_name"],
            description="",  # Не храним в файле для экономии места
            category=AttackCategory(data.get("category", "unknown")),
            payload="",  # Не храним
            target_layer=data["target_layer"],
        )

        return AttackResult(
            attack=attack,
            success=data["success"],
            layer_response=data.get("layer_response"),
            metrics=data.get("metrics", {}),
            timestamp=data.get("timestamp", time.time()),
            error=data.get("error"),
        )

    def _update_index(self, result: AttackResult, position: int) -> None:
        """Обновить индекс."""
        # Индекс по атаке
        if result.attack.id not in self._attack_index:
            self._attack_index[result.attack.id] = []
        self._attack_index[result.attack.id].append(position)

        # Индекс по слою
        if result.attack.target_layer not in self._layer_index:
            self._layer_index[result.attack.target_layer] = []
        self._layer_index[result.attack.target_layer].append(position)

        # Сохраняем индекс
        self._save_index()

    def _load_index(self) -> None:
        """Загрузить индекс из файла."""
        if self._index_file.exists():
            with open(self._index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._attack_index = data.get("attack_index", {})
                self._layer_index = data.get("layer_index", {})

    def _save_index(self) -> None:
        """Сохранить индекс в файл."""
        data = {
            "attack_index": self._attack_index,
            "layer_index": self._layer_index,
        }
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)