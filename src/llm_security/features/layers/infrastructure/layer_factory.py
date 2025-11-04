from __future__ import annotations

from typing import Optional

from ..domain.entities import LayerConfig
from ..domain.interfaces import ILayer
from .layer_registry import LayerRegistry


class LayerFactory:
    """Фабрика для создания экземпляров слоев."""

    def __init__(self, registry: LayerRegistry):
        self.registry = registry

    def create_layer(self, layer_id: str, config: LayerConfig) -> Optional[ILayer]:
        """Создает экземпляр слоя по ID и конфигурации."""
        # Сначала пробуем создать из плагина
        layer = self.registry.create_layer_from_plugin(layer_id, config)
        if layer:
            return layer

        # Если не получилось, пробуем из зарегистрированного класса
        layer = self.registry.create_layer_from_class(layer_id, config)
        if layer:
            return layer

        return None

    def create_layers_from_configs(self, configs: dict[str, LayerConfig]) -> list[ILayer]:
        """Создает несколько слоев из конфигураций."""
        layers = []
        for layer_id, config in configs.items():
            layer = self.create_layer(layer_id, config)
            if layer:
                layers.append(layer)
        return layers