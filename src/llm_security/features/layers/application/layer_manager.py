from __future__ import annotations

from typing import List, Dict, Optional
from collections import OrderedDict

from ..domain.interfaces import ILayer
from ..domain.entities import LayerConfig


class LayerManager:
    """Менеджер для управления всеми слоями защиты."""

    def __init__(self):
        self._layers: OrderedDict[str, ILayer] = OrderedDict()
        self._configs: Dict[str, LayerConfig] = {}

    def register_layer(self, layer: ILayer, config: LayerConfig) -> None:
        """Регистрирует слой с его конфигурацией."""
        self._layers[layer.id] = layer
        self._configs[layer.id] = config

    def unregister_layer(self, layer_id: str) -> bool:
        """Удаляет слой из менеджера."""
        if layer_id in self._layers:
            del self._layers[layer_id]
            del self._configs[layer_id]
            return True
        return False

    def get_layer(self, layer_id: str) -> Optional[ILayer]:
        """Получает слой по ID."""
        return self._layers.get(layer_id)

    def get_config(self, layer_id: str) -> Optional[LayerConfig]:
        """Получает конфигурацию слоя по ID."""
        return self._configs.get(layer_id)

    def get_enabled_layers(self) -> List[ILayer]:
        """Возвращает список включенных слоев."""
        return [layer for layer in self._layers.values() if layer.enabled]

    def get_all_layers(self) -> List[ILayer]:
        """Возвращает все зарегистрированные слои."""
        return list(self._layers.values())

    def update_config(self, layer_id: str, config: LayerConfig) -> bool:
        """Обновляет конфигурацию слоя."""
        if layer_id in self._layers:
            self._configs[layer_id] = config
            # Синхронизируем enabled статус
            self._layers[layer_id].enabled = config.enabled
            return True
        return False

    def enable_layer(self, layer_id: str) -> bool:
        """Включает слой."""
        if layer_id in self._layers:
            self._layers[layer_id].enabled = True
            self._configs[layer_id].enabled = True
            return True
        return False

    def disable_layer(self, layer_id: str) -> bool:
        """Отключает слой."""
        if layer_id in self._layers:
            self._layers[layer_id].enabled = False
            self._configs[layer_id].enabled = False
            return True
        return False

    def reorder_layers(self, layer_ids: List[str]) -> bool:
        """Изменяет порядок слоев."""
        if set(layer_ids) != set(self._layers.keys()):
            return False

        new_order = OrderedDict()
        for layer_id in layer_ids:
            new_order[layer_id] = self._layers[layer_id]
        self._layers = new_order
        return True

    def clear(self) -> None:
        """Очищает все слои."""
        self._layers.clear()
        self._configs.clear()

    @property
    def layer_count(self) -> int:
        """Количество зарегистрированных слоев."""
        return len(self._layers)

    @property
    def enabled_count(self) -> int:
        """Количество включенных слоев."""
        return len(self.get_enabled_layers())