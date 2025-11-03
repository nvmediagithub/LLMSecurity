from __future__ import annotations

from ..domain.entities import L1LayerConfig
from ..domain.interfaces import IL1ConfigRepository
from ..domain.policy import L1Policy


class L1ConfigService:
    """Сервис для управления конфигурацией L1 слоя."""

    def __init__(self, config_repo: IL1ConfigRepository):
        self._config_repo = config_repo

    async def get_config(self) -> L1LayerConfig:
        """Получить текущую конфигурацию."""
        return await self._config_repo.get_config()

    async def update_config(self, config: L1LayerConfig) -> None:
        """Обновить конфигурацию с валидацией."""
        errors = L1Policy.validate_config(config)
        if errors:
            raise ValueError(f"Invalid config: {', '.join(errors)}")
        await self._config_repo.save_config(config)

    async def reset_to_default(self) -> L1LayerConfig:
        """Сбросить конфигурацию к значениям по умолчанию."""
        default_config = L1Policy.get_default_config()
        await self._config_repo.save_config(default_config)
        return default_config