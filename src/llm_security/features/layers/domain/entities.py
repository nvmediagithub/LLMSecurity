from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol
from abc import ABC


@dataclass(slots=True)
class LayerMetadata:
    """Метаданные слоя защиты."""

    id: str
    name: str
    description: str
    version: str = "1.0.0"
    config_schema: Optional[Dict[str, Any]] = None
    dependencies: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LayerConfig:
    """Унифицированная конфигурация слоя."""

    layer_id: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)

    def get_param(self, key: str, default: Any = None) -> Any:
        """Получить параметр с дефолтным значением."""
        return self.parameters.get(key, default)


class LayerPlugin(Protocol):
    """База для плагинов слоев."""

    def get_metadata(self) -> LayerMetadata:
        """Возвращает метаданные плагина."""
        ...

    def create_layer(self, config: LayerConfig) -> ILayer:
        """Создает экземпляр слоя на основе конфигурации."""
        ...


# Импорт ILayer для избежания циклических импортов
from .interfaces import ILayer