from __future__ import annotations

from typing import Dict, List, Optional, Type
import importlib
import pkgutil
import inspect

from ..domain.entities import LayerMetadata, LayerPlugin
from ..domain.interfaces import ILayer


class LayerRegistry:
    """Реестр для регистрации слоев как плагинов."""

    def __init__(self):
        self._plugins: Dict[str, LayerPlugin] = {}
        self._metadata: Dict[str, LayerMetadata] = {}
        self._layer_classes: Dict[str, Type[ILayer]] = {}

    def register_plugin(self, plugin: LayerPlugin) -> None:
        """Регистрирует плагин слоя."""
        metadata = plugin.get_metadata()
        self._plugins[metadata.id] = plugin
        self._metadata[metadata.id] = metadata

    def register_layer_class(self, layer_class: Type[ILayer], metadata: LayerMetadata) -> None:
        """Регистрирует класс слоя напрямую."""
        self._layer_classes[metadata.id] = layer_class
        self._metadata[metadata.id] = metadata

    def unregister_plugin(self, plugin_id: str) -> bool:
        """Удаляет плагин из реестра."""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            if plugin_id in self._metadata:
                del self._metadata[plugin_id]
            return True
        return False

    def get_plugin(self, plugin_id: str) -> Optional[LayerPlugin]:
        """Получает плагин по ID."""
        return self._plugins.get(plugin_id)

    def get_metadata(self, plugin_id: str) -> Optional[LayerMetadata]:
        """Получает метаданные плагина по ID."""
        return self._metadata.get(plugin_id)

    def get_all_plugins(self) -> List[LayerPlugin]:
        """Возвращает все зарегистрированные плагины."""
        return list(self._plugins.values())

    def get_all_metadata(self) -> List[LayerMetadata]:
        """Возвращает метаданные всех зарегистрированных плагинов."""
        return list(self._metadata.values())

    def discover_plugins(self, package_path: str) -> int:
        """Автоматически обнаруживает и регистрирует плагины в пакете."""
        count = 0
        try:
            package = importlib.import_module(package_path)
            for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and
                            hasattr(obj, 'get_metadata') and
                            callable(getattr(obj, 'get_metadata')) and
                            hasattr(obj, 'create_layer') and
                            callable(getattr(obj, 'create_layer'))):
                            # Это плагин
                            plugin_instance = obj()
                            self.register_plugin(plugin_instance)
                            count += 1
                except Exception:
                    # Пропускаем модули, которые не могут быть загружены
                    continue
        except Exception:
            pass
        return count

    def create_layer_from_plugin(self, plugin_id: str, config: 'LayerConfig') -> Optional[ILayer]:
        """Создает слой из плагина."""
        plugin = self.get_plugin(plugin_id)
        if plugin:
            return plugin.create_layer(config)
        return None

    def create_layer_from_class(self, layer_id: str, config: 'LayerConfig') -> Optional[ILayer]:
        """Создает слой из зарегистрированного класса."""
        layer_class = self._layer_classes.get(layer_id)
        if layer_class:
            # Предполагаем, что класс принимает config в конструкторе
            return layer_class(config)
        return None

    def clear(self) -> None:
        """Очищает реестр."""
        self._plugins.clear()
        self._metadata.clear()
        self._layer_classes.clear()

    @property
    def plugin_count(self) -> int:
        """Количество зарегистрированных плагинов."""
        return len(self._plugins)

    @property
    def layer_class_count(self) -> int:
        """Количество зарегистрированных классов слоев."""
        return len(self._layer_classes)