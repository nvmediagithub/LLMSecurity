from __future__ import annotations

from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

from ..domain.entities import LayerConfig


class LayerConfigService:
    """Сервис для унифицированной конфигурации слоев."""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_layer_configs(self, profile_name: str) -> Dict[str, LayerConfig]:
        """Загружает конфигурации слоев для профиля."""
        config_file = self.config_dir / f"{profile_name}.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        configs = {}
        for layer_id, config_data in data.get('layers', {}).items():
            configs[layer_id] = LayerConfig(
                layer_id=layer_id,
                enabled=config_data.get('enabled', True),
                parameters=config_data.get('parameters', {})
            )

        return configs

    def save_layer_configs(self, profile_name: str, configs: Dict[str, LayerConfig]) -> None:
        """Сохраняет конфигурации слоев для профиля."""
        config_file = self.config_dir / f"{profile_name}.yaml"

        data = {
            'layers': {
                layer_id: {
                    'enabled': config.enabled,
                    'parameters': config.parameters
                }
                for layer_id, config in configs.items()
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def get_layer_config(self, profile_name: str, layer_id: str) -> Optional[LayerConfig]:
        """Получает конфигурацию конкретного слоя."""
        configs = self.load_layer_configs(profile_name)
        return configs.get(layer_id)

    def update_layer_config(self, profile_name: str, config: LayerConfig) -> None:
        """Обновляет конфигурацию слоя."""
        configs = self.load_layer_configs(profile_name)
        configs[config.layer_id] = config
        self.save_layer_configs(profile_name, configs)

    def delete_profile(self, profile_name: str) -> bool:
        """Удаляет профиль конфигурации."""
        config_file = self.config_dir / f"{profile_name}.yaml"
        if config_file.exists():
            config_file.unlink()
            return True
        return False

    def list_profiles(self) -> List[str]:
        """Возвращает список доступных профилей."""
        return [f.stem for f in self.config_dir.glob("*.yaml")]

    def validate_config(self, config: LayerConfig, schema: Optional[Dict[str, Any]] = None) -> List[str]:
        """Валидирует конфигурацию слоя."""
        errors = []

        if not config.layer_id:
            errors.append("Layer ID cannot be empty")

        if schema:
            # Простая валидация по схеме
            for param_name, param_info in schema.get('properties', {}).items():
                if param_name in config.parameters:
                    param_type = param_info.get('type')
                    value = config.parameters[param_name]

                    if param_type == 'integer' and not isinstance(value, int):
                        errors.append(f"Parameter '{param_name}' must be integer")
                    elif param_type == 'string' and not isinstance(value, str):
                        errors.append(f"Parameter '{param_name}' must be string")
                    elif param_type == 'boolean' and not isinstance(value, bool):
                        errors.append(f"Parameter '{param_name}' must be boolean")

        return errors