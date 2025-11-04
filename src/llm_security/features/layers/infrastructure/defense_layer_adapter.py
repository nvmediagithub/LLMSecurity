from __future__ import annotations

from typing import Optional, Any
import inspect

from ...defense.domain.interfaces import IDefenseLayer
from ...defense.domain.entities import DefenseResult
from ..domain.interfaces import ILayer
from ..domain.entities import LayerConfig, LayerMetadata


class DefenseLayerAdapter(ILayer):
    """Адаптер для интеграции существующих слоев защиты в новую систему."""

    def __init__(self, defense_layer: IDefenseLayer, config: LayerConfig):
        self._defense_layer = defense_layer
        self._config = config

        # Синхронизируем ID и enabled статус
        self.id = defense_layer.id
        self.enabled = config.enabled

    @classmethod
    def create_from_defense_layer(cls, defense_layer: IDefenseLayer, config: Optional[LayerConfig] = None) -> DefenseLayerAdapter:
        """Создает адаптер из существующего слоя защиты."""
        if config is None:
            config = LayerConfig(
                layer_id=defense_layer.id,
                enabled=defense_layer.enabled,
                parameters={}
            )
        return cls(defense_layer, config)

    def before_send(self, prompt_bundle: Any) -> Any:
        """Адаптирует вызов before_send."""
        if not self.enabled:
            return DefenseResult.allow(self.id)

        # Преобразуем PromptBundle из новой системы в старую, если необходимо
        # В данном случае они совместимы
        return self._defense_layer.before_send(prompt_bundle)

    def after_recv(self, prompt_bundle: Any, response_text: str) -> Any:
        """Адаптирует вызов after_recv."""
        if not self.enabled:
            return DefenseResult.allow(self.id)

        return self._defense_layer.after_recv(prompt_bundle, response_text)

    def update_config(self, config: LayerConfig) -> None:
        """Обновляет конфигурацию адаптера."""
        self._config = config
        self.enabled = config.enabled

        # Если слой поддерживает параметры, передаем их
        if hasattr(self._defense_layer, 'config') and hasattr(self._defense_layer.config, 'update'):
            # Обновляем параметры в оригинальном слое
            self._defense_layer.config.parameters.update(config.parameters)


def create_layer_metadata_from_defense_layer(defense_layer: IDefenseLayer) -> LayerMetadata:
    """Создает метаданные для существующего слоя защиты."""
    # Извлекаем информацию из класса слоя
    layer_class = defense_layer.__class__

    # Получаем описание из docstring
    description = (layer_class.__doc__ or f"Defense layer {defense_layer.id}").strip()

    # Создаем базовую схему конфигурации
    config_schema = {
        "type": "object",
        "properties": {
            "enabled": {
                "type": "boolean",
                "description": "Whether the layer is enabled",
                "default": True
            }
        }
    }

    # Если слой имеет дополнительные параметры, добавляем их в схему
    if hasattr(defense_layer, 'config') and hasattr(defense_layer.config, 'parameters'):
        for param_name, param_value in defense_layer.config.parameters.items():
            param_type = type(param_value).__name__
            if param_type == 'str':
                param_type = 'string'
            elif param_type == 'int':
                param_type = 'integer'
            elif param_type == 'bool':
                param_type = 'boolean'

            config_schema["properties"][param_name] = {
                "type": param_type,
                "default": param_value
            }

    return LayerMetadata(
        id=defense_layer.id,
        name=getattr(layer_class, 'name', defense_layer.id.replace('_', ' ').title()),
        description=description,
        version=getattr(layer_class, 'version', '1.0.0'),
        config_schema=config_schema
    )