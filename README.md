# LLMSecurity Lab

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt-6.6+-orange.svg)](https://pypi.org/project/PyQt6/)

**Русский** | [English](#english)

LLMSecurity Lab - унифицированная платформа на базе Clean Architecture и Feature First для тестирования устойчивости LLM к prompt-инъекциям. Платформа автоматизирует выполнение тестов, применяет многоуровневые конвейеры защиты и визуализирует результаты через CLI и PyQt UI.

## Ключевые возможности

- **Унифицированная система слоев** – плагинная архитектура для управления девятью модульными слоями (L1–L9) защиты.
- **Система атак и эмуляторов** – симуляция реальных атак на конкретные слои защиты, включая L1 эмуляторы.
- **Комплексный анализ** – выявление уязвимостей и генерация рекомендаций на основе результатов тестирования.
- **Test Runner & A/B режим** – сравнение поведения с защитой и без нее, сбор богатых метрик и логов по слоям.
- **Множественные подключения к моделям** – переключение между dummy/локальными клиентами и удаленными провайдерами (OpenRouter, Azure OpenAI и др.).
- **Отчетность** – экспорт сводок в CSV/JSON/HTML, включая вклад слоев и ложные срабатывания.
- **PyQt UI** – дружественный интерфейс для исследователей с живым статусом, фильтрами и A/B переключателями.
- **Соответствие OpenAI рекомендациям** – реализация политик безопасности, логирования и human-in-the-loop механизмов.

## Архитектура

Платформа построена на принципах **Clean Architecture** и **Feature First** дизайна:

```
src/llm_security/
├── core/                 # общие сервисы (загрузчик конфигураций, логирование)
├── shared/               # зарезервировано для общих помощников
└── features/             # feature-first модули
    ├── layers/           # унифицированная система слоев защиты (ILayer, LayerManager)
    ├── attacks/          # система атак и эмуляторов (AttackDefinition, AttackExecutor)
    ├── analysis/         # комплексный анализ результатов и генерация отчетов
    ├── defense/          # Defense Pipeline (L1–L9 слои)
    ├── models/           # клиенты моделей и сервис подключений
    ├── testing/          # prompt тесты, runner и evaluator
    ├── reporting/        # агрегатор метрик и экспортеры
    ├── ui/               # PyQt presentation layer
    └── l1/               # специализированный модуль для L1 атак и эмуляторов
```

Каждая фича следует внутренней структуре Clean Architecture:
- `domain` – entities и contracts (Decision, PromptTest, PolicyRules, ILayer).
- `application` – use-case logic (DefensePipeline, TestRunner, LayerManager).
- `infrastructure` – adapters (PromptTestRepository, DummyModelClient, layer implementations).

Подробная документация: [`docs/architecture.md`](docs/architecture.md).

## Установка

### Требования
- Python 3.10+
- pip

### Установка из исходников
```bash
git clone https://github.com/your-username/llm-security-lab.git
cd llm-security-lab
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e .
```

### Установка GUI (PyQt6)
Для использования графического интерфейса установите PyQt6:
```bash
pip install PyQt6
```

### Опциональные зависимости для разработки
```bash
pip install -e ".[dev]"
```

## Использование

### CLI Команды

#### Управление подключениями к LLM
```bash
# Список доступных подключений
llm-security-cli connections

# Добавить новое подключение (OpenRouter)
llm-security-cli connections add --name openrouter --provider openrouter --api-key-env OPENROUTER_API_KEY --model gpt-4

# Удалить подключение
llm-security-cli connections remove --name dummy
```

#### Запуск тестов
```bash
# Запуск тестов с профилем защиты и подключением
llm-security-cli run --profile strict_demo --connection dummy

# Запуск в A/B режиме (сравнение с baseline)
llm-security-cli run --profile strict_demo --connection dummy --ab-mode

# Экспорт отчета в JSON
llm-security-cli run --profile strict_demo --connection dummy --export-json report.json
```

### Графический интерфейс
```bash
llm-security-ui
```

Интерфейс предоставляет:
- Выбор профиля защиты и подключения
- Фильтрацию по категориям атак
- A/B переключатель для сравнения
- Таблицу результатов с drill-down по слоям
- Экспорт отчетов

### Примеры сценариев

#### Базовое тестирование
```python
from llm_security.features.testing.application.service import TestSuiteService
from llm_security.features.defense.application.profiles_service import ProfilesService

# Загрузка профиля и запуск тестов
profiles_service = ProfilesService()
profile = profiles_service.get_profile("strict_demo")

service = TestSuiteService()
results = service.run_baseline_tests("dummy", profile)
```

#### Симуляция атак на L1
```python
from llm_security.features.l1.application.emulation_service import EmulationService

service = EmulationService()
result = service.emulate_attack("encoding_attack", {"input": "test input"})
```

## Тестирование

Проект использует pytest для автоматизированного тестирования.

### Запуск всех тестов
```bash
pytest
```

### Запуск конкретных тестов
```bash
pytest tests/test_defense.py
pytest tests/test_l1_emulators.py -v
```

### Тестирование с покрытием
```bash
pytest --cov=src/llm_security --cov-report=html
```

### Тестирование GUI (требует PyQt6)
```bash
pytest --qt=qt6 tests/
```

## Документация

- **Обзор архитектуры**: [`docs/architecture.md`](docs/architecture.md)
- **Сводка требований**: [`docs/requirements_summary.md`](docs/requirements_summary.md)
- **Политика агентов и безопасность**: [`AGENTS.md`](AGENTS.md)
- **Руководства по фичам**:
  - [`docs/features/layers.md`](docs/features/layers.md) – унифицированная система слоев
  - [`docs/features/attacks.md`](docs/features/attacks.md) – система атак и эмуляторов
  - [`docs/features/analysis.md`](docs/features/analysis.md) – комплексный анализ
  - [`docs/features/defense.md`](docs/features/defense.md) – Defense Pipeline (L1–L9)
  - [`docs/features/models.md`](docs/features/models.md) – клиенты моделей
  - [`docs/features/testing.md`](docs/features/testing.md) – тестирование
  - [`docs/features/ui.md`](docs/features/ui.md) – PyQt интерфейс
  - [`docs/features/l1/`](docs/features/l1/) – специализированная документация по L1

## Лицензия

Этот проект лицензирован под [MIT License](LICENSE).

## Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md) для получения инструкций.

### Как внести вклад
1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Сделайте коммит изменений (`git commit -m 'Add some amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

### Требования к коду
- Код должен следовать PEP 8
- Добавляйте тесты для новых функций
- Обновляйте документацию при необходимости
- Используйте type hints

### Контакты
- Issues: [GitHub Issues](https://github.com/your-username/llm-security-lab/issues)
- Discussions: [GitHub Discussions](https://github.com/your-username/llm-security-lab/discussions)

---

# English

LLMSecurity Lab is a unified platform based on Clean Architecture and Feature First design for testing LLM resilience to prompt injections. The platform automates test execution, applies multi-level defense pipelines, and visualizes results through CLI and PyQt UI.

## Key Features

- **Unified Layer System** – Plugin architecture for managing nine modular defense layers (L1–L9).
- **Attack & Emulator System** – Simulation of real attacks targeting specific defense layers, including L1 emulators.
- **Comprehensive Analysis** – Vulnerability detection and recommendation generation based on test results.
- **Test Runner & A/B Mode** – Comparison of behavior with and without protection, collecting rich metrics and layer logs.
- **Multiple Model Connections** – Switching between dummy/local clients and remote providers (OpenRouter, Azure OpenAI, etc.).
- **Reporting** – Export summaries to CSV/JSON/HTML, including layer contributions and false positives.
- **PyQt UI** – User-friendly interface for researchers with live status, filters, and A/B toggles.
- **OpenAI Compliance** – Implementation of safety policies, logging, and human-in-the-loop mechanisms.

## Architecture

The platform is built on **Clean Architecture** and **Feature First** design principles:

```
src/llm_security/
├── core/                 # shared services (config loader, logging)
├── shared/               # reserved for shared helpers
└── features/             # feature-first modules
    ├── layers/           # unified defense layer system (ILayer, LayerManager)
    ├── attacks/          # attack and emulator system (AttackDefinition, AttackExecutor)
    ├── analysis/         # comprehensive result analysis and report generation
    ├── defense/          # Defense Pipeline (L1–L9 layers)
    ├── models/           # model clients and connection service
    ├── testing/          # prompt tests, runner and evaluator
    ├── reporting/        # metrics aggregator and exporters
    ├── ui/               # PyQt presentation layer
    └── l1/               # specialized L1 attacks and emulators module
```

Each feature follows the internal Clean Architecture structure:
- `domain` – entities and contracts (Decision, PromptTest, PolicyRules, ILayer).
- `application` – use-case logic (DefensePipeline, TestRunner, LayerManager).
- `infrastructure` – adapters (PromptTestRepository, DummyModelClient, layer implementations).

Detailed documentation: [`docs/architecture.md`](docs/architecture.md).
