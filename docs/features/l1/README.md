# L1 Input Sanitization Layer

## Обзор (Overview)

L1 слой обеспечивает первичную защиту от prompt-инъекций путем санитизации и нормализации входных данных. Этот слой работает на самом низком уровне архитектуры защиты, обрабатывая текст до его передачи в модель.

The L1 layer provides primary protection against prompt injections through input sanitization and normalization. This layer operates at the lowest level of the defense architecture, processing text before it is passed to the model.

## Архитектура (Architecture)

### Структура проекта (Project Structure)

```
src/llm_security/features/l1/
├── domain/              # Бизнес-логика (Domain Logic)
│   ├── entities.py      # Сущности (Entities)
│   ├── interfaces.py    # Интерфейсы (Interfaces)
│   └── policy.py        # Политики (Policies)
├── application/         # Сервисы приложения (Application Services)
│   ├── config_service.py
│   ├── emulation_service.py
│   └── evaluation_service.py
├── infrastructure/      # Инфраструктура (Infrastructure)
│   ├── attack_repository.py
│   ├── config_repository.py
│   └── base_emulator.py
```

### Компоненты (Components)

#### Domain Layer
- **L1Attack**: Представляет атаку L1 уровня (Represents L1 level attack)
- **L1AttackCategory**: Категории атак (Attack categories)
- **L1LayerConfig**: Конфигурация слоя (Layer configuration)
- **L1AttackResult**: Результат эмуляции атаки (Attack emulation result)

#### Application Layer
- **L1ConfigService**: Управление конфигурацией (Configuration management)
- **L1EmulationService**: Эмуляция атак (Attack emulation)
- **L1EvaluationService**: Оценка результатов (Result evaluation)

#### Infrastructure Layer
- **YamlL1AttackRepository**: YAML репозиторий атак (YAML attack repository)
- **YamlL1ConfigRepository**: YAML репозиторий конфигурации (YAML config repository)
- **BaseL1AttackEmulator**: Базовый эмулятор атак (Base attack emulator)

## Функциональность (Functionality)

### Категории атак (Attack Categories)

1. **INJECTION**: Прямые инъекции (Direct injections)
2. **NORMALIZATION**: Атаки на нормализацию (Normalization attacks)
3. **SANITIZATION**: Обход санитизации (Sanitization bypass)
4. **LENGTH_ATTACK**: Атаки на ограничение длины (Length limit attacks)
5. **ENCODING_ATTACK**: Атаки через кодировки (Encoding attacks)

### Конфигурация (Configuration)

```yaml
max_length: 5000
enabled_categories:
  - injection
  - normalization
  - sanitization
sanitize_zero_width: true
normalize_unicode: true
```

### Использование (Usage)

```python
from src.llm_security.features.l1.application.config_service import L1ConfigService
from src.llm_security.features.l1.infrastructure.config_repository import YamlL1ConfigRepository

# Создание сервиса конфигурации
config_repo = YamlL1ConfigRepository("config/l1_config.yaml")
config_service = L1ConfigService(config_repo)

# Получение конфигурации
config = await config_service.get_config()
```

## Интеграция с архитектурой (Architecture Integration)

L1 слой интегрируется с общей системой защиты как первый слой в конвейере `DefensePipeline`. Он обрабатывает `PromptBundle` перед передачей в следующие слои.

The L1 layer integrates with the overall defense system as the first layer in the `DefensePipeline`. It processes the `PromptBundle` before passing it to subsequent layers.

## Тестирование (Testing)

Для тестирования L1 слоя используются:
- Эмуляция атак на основе YAML-конфигурации
- Оценка эффективности санитизации
- A/B тестирование с baseline моделью

For testing the L1 layer:
- Attack emulation based on YAML configuration
- Sanitization effectiveness evaluation
- A/B testing with baseline model