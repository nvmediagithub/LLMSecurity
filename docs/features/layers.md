# Фича Layers

## Обзор

Фича **Layers** представляет унифицированную архитектуру для управления и конфигурации слоев защиты LLM. Она предоставляет плагинную систему для динамического управления слоями защиты, унифицированные интерфейсы и централизованное управление конфигурациями.

## Архитектура

```text
src/llm_security/features/layers/
├── domain/
│   ├── entities.py          # LayerMetadata, LayerConfig, LayerPlugin
│   └── interfaces.py        # ILayer - унифицированный интерфейс
├── application/
│   ├── layer_manager.py     # LayerManager - менеджер слоев
│   └── layer_config_service.py # управление конфигурациями
└── infrastructure/
    ├── layer_registry.py    # реестр плагинов слоев
    ├── layer_factory.py     # фабрика создания слоев
    └── defense_layer_adapter.py # адаптер для существующих слоев
```

## Принципы унифицированной архитектуры

### 1. Единый интерфейс ILayer

Все слои защиты (L1-L9) реализуют единый интерфейс [`ILayer`](src/llm_security/features/layers/domain/interfaces.py:9):

```python
@runtime_checkable
class ILayer(Protocol):
    """Единый интерфейс для всех слоев защиты (L1-L9)."""

    id: str
    enabled: bool

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        ...

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        ...
```

### 2. Метаданные и конфигурация

Каждый слой имеет метаданные [`LayerMetadata`](src/llm_security/features/layers/domain/entities.py:9) и унифицированную конфигурацию [`LayerConfig`](src/llm_security/features/layers/domain/entities.py:21).

### 3. Плагинная система

Слои регистрируются как плагины через [`LayerPlugin`](src/llm_security/features/layers/domain/entities.py:33) интерфейс, позволяя динамическую загрузку и управление.

## API Reference

### LayerManager

Центральный компонент для управления слоями:

```python
class LayerManager:
    def register_layer(self, layer: ILayer, config: LayerConfig) -> None:
        """Регистрирует слой с его конфигурацией."""

    def get_layer(self, layer_id: str) -> Optional[ILayer]:
        """Получает слой по ID."""

    def get_enabled_layers(self) -> List[ILayer]:
        """Возвращает список включенных слоев."""

    def update_config(self, layer_id: str, config: LayerConfig) -> bool:
        """Обновляет конфигурацию слоя."""

    def enable_layer(self, layer_id: str) -> bool:
        """Включает слой."""

    def disable_layer(self, layer_id: str) -> bool:
        """Отключает слой."""

    def reorder_layers(self, layer_ids: List[str]) -> bool:
        """Изменяет порядок слоев."""
```

### LayerConfigService

Сервис для управления конфигурациями слоев:

```python
class LayerConfigService:
    def load_layer_configs(self, profile_name: str) -> Dict[str, LayerConfig]:
        """Загружает конфигурации слоев из профиля."""

    def save_layer_configs(self, profile_name: str, configs: Dict[str, LayerConfig]) -> None:
        """Сохраняет конфигурации слоев в профиль."""

    def validate_config(self, config: LayerConfig) -> bool:
        """Валидирует конфигурацию слоя."""
```

### LayerRegistry

Реестр плагинов слоев:

```python
class LayerRegistry:
    def register_plugin(self, plugin: LayerPlugin) -> None:
        """Регистрирует плагин слоя."""

    def get_plugin(self, layer_id: str) -> Optional[LayerPlugin]:
        """Получает плагин по ID слоя."""

    def list_plugins(self) -> List[LayerPlugin]:
        """Возвращает список всех плагинов."""
```

## Примеры использования

### Регистрация и управление слоем

```python
from llm_security.features.layers.application.layer_manager import LayerManager
from llm_security.features.layers.domain.entities import LayerConfig

# Создание менеджера
manager = LayerManager()

# Регистрация слоя
config = LayerConfig(
    layer_id="l1_input_sanitizer",
    enabled=True,
    parameters={"max_length": 1000, "encoding": "utf-8"}
)

# Предполагаем, что у нас есть экземпляр слоя
# manager.register_layer(layer_instance, config)

# Управление слоем
manager.enable_layer("l1_input_sanitizer")
enabled_layers = manager.get_enabled_layers()
```

### Работа с конфигурациями

```python
from llm_security.features.layers.application.layer_config_service import LayerConfigService

config_service = LayerConfigService()

# Загрузка конфигураций из профиля
configs = config_service.load_layer_configs("strict_demo")

# Обновление конфигурации
layer_config = configs["l1_input_sanitizer"]
layer_config.parameters["max_length"] = 2000

# Сохранение изменений
config_service.save_layer_configs("strict_demo", configs)
```

### Динамическая загрузка плагинов

```python
from llm_security.features.layers.infrastructure.layer_registry import LayerRegistry
from llm_security.features.layers.infrastructure.layer_factory import LayerFactory

registry = LayerRegistry()
factory = LayerFactory(registry)

# Регистрация плагина
# registry.register_plugin(my_layer_plugin)

# Создание слоя через фабрику
layer = factory.create_layer("l1_input_sanitizer", config)
```

## Интеграция с существующими фичами

### Defense Pipeline

Фича Layers интегрируется с [`DefensePipeline`](src/llm_security/features/defense/application/pipeline.py) через [`DefenseLayerAdapter`](src/llm_security/features/layers/infrastructure/defense_layer_adapter.py), который адаптирует существующие слои L1-L9 к унифицированному интерфейсу ILayer.

```python
class DefenseLayerAdapter:
    """Адаптер для интеграции существующих слоев с унифицированной архитектурой."""

    def __init__(self, existing_layer):
        self._layer = existing_layer

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        return self._layer.before_send(prompt_bundle)

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        return self._layer.after_recv(prompt_bundle, response_text)
```

### Attacks System

Фича Layers предоставляет целевые слои для тестирования в [`Attacks`](src/llm_security/features/attacks/domain/entities.py). Атаки могут быть направлены на конкретные слои через поле `target_layer` в [`AttackDefinition`](src/llm_security/features/attacks/domain/entities.py:27).

### UI Integration

PyQt UI может использовать [`LayerManager`](src/llm_security/features/layers/application/layer_manager.py) для динамического отображения и управления слоями в интерфейсе управления профилями защиты.

## Миграционные гайды

### Для существующих слоев L1-L9

1. **Обновление интерфейса**: Убедитесь, что ваш слой реализует [`ILayer`](src/llm_security/features/layers/domain/interfaces.py:9) интерфейс.

2. **Создание плагина**: Реализуйте [`LayerPlugin`](src/llm_security/features/layers/domain/entities.py:33) для вашего слоя:

```python
class MyLayerPlugin:
    def get_metadata(self) -> LayerMetadata:
        return LayerMetadata(
            id="my_layer",
            name="My Custom Layer",
            description="Description of my layer",
            version="1.0.0",
            config_schema={"type": "object", "properties": {...}}
        )

    def create_layer(self, config: LayerConfig) -> ILayer:
        return MyLayer(config)
```

3. **Регистрация в фабрике**: Зарегистрируйте плагин в [`LayerRegistry`](src/llm_security/features/layers/infrastructure/layer_registry.py).

### Для конфигурационных файлов

Обновите `config/profiles.yaml` для использования новой структуры конфигураций:

```yaml
profiles:
  strict_demo:
    layers:
      l1_input_sanitizer:
        enabled: true
        parameters:
          max_length: 1000
      l2_prompt_classifier:
        enabled: true
        parameters:
          threshold: 0.8
```

### Для тестов

Обновите тесты для использования унифицированных интерфейсов:

```python
# Вместо прямого вызова слоя
# result = layer.before_send(bundle)

# Используйте LayerManager
layer = manager.get_layer("l1_input_sanitizer")
result = layer.before_send(bundle)
```

## Заключение

Фича Layers предоставляет мощную и гибкую систему для управления слоями защиты LLM, обеспечивая:

- **Унифицированные интерфейсы** для всех слоев
- **Плагинную архитектуру** для расширяемости
- **Централизованное управление** конфигурациями
- **Динамическую загрузку** и управление слоями
- **Плавную интеграцию** с существующими компонентами

Эта архитектура значительно упрощает разработку, тестирование и развертывание новых слоев защиты, делая систему более модульной и поддерживаемой.