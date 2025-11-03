from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from src.llm_security.core.config.loader import ConfigLoader
from ..domain.entities import L1AttackCategory, L1LayerConfig
from ..domain.interfaces import IL1ConfigRepository


class YamlL1ConfigRepository(IL1ConfigRepository):
    """YAML репозиторий для конфигурации L1 слоя."""

    def __init__(self, file_path: Path | str, loader: ConfigLoader | None = None):
        self._file_path = Path(file_path)
        self._loader = loader or ConfigLoader()
        self._config: L1LayerConfig | None = None

    async def get_config(self) -> L1LayerConfig:
        if self._config is None:
            self._config = await self._load_config()
        return self._config

    async def save_config(self, config: L1LayerConfig) -> None:
        data = self._serialize_config(config)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self._file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

        self._config = config

    async def _load_config(self) -> L1LayerConfig:
        """Загрузить конфигурацию из файла."""
        if not self._file_path.exists():
            return self._get_default_config()

        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            return self._get_default_config()

        return self._parse_config(data)

    def _parse_config(self, data: Dict[str, Any]) -> L1LayerConfig:
        """Парсить конфигурацию из словаря."""
        max_length = data.get("max_length", 5000)
        enabled_categories = data.get("enabled_categories", [])
        sanitize_zero_width = data.get("sanitize_zero_width", True)
        normalize_unicode = data.get("normalize_unicode", True)

        categories = set()
        for cat_name in enabled_categories:
            try:
                categories.add(L1AttackCategory(cat_name))
            except ValueError:
                continue

        return L1LayerConfig(
            max_length=max_length,
            enabled_categories=categories,
            sanitize_zero_width=sanitize_zero_width,
            normalize_unicode=normalize_unicode,
        )

    def _serialize_config(self, config: L1LayerConfig) -> Dict[str, Any]:
        """Сериализовать конфигурацию в словарь."""
        return {
            "max_length": config.max_length,
            "enabled_categories": [cat.value for cat in config.enabled_categories],
            "sanitize_zero_width": config.sanitize_zero_width,
            "normalize_unicode": config.normalize_unicode,
        }

    def _get_default_config(self) -> L1LayerConfig:
        """Получить конфигурацию по умолчанию."""
        return L1LayerConfig(
            max_length=5000,
            enabled_categories=set(L1AttackCategory),
            sanitize_zero_width=True,
            normalize_unicode=True,
        )