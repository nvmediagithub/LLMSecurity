# Architecture Guide

## Унифицированная архитектура: Clean Architecture + Feature First + Layers + Attacks + Analysis

```
src/llm_security
├── core/                 # shared infrastructure (config loader, logging stubs)
├── shared/               # reusable helpers (reserved)
└── features/            # feature-first modules
    ├── layers/           # унифицированная система слоев защиты
    │   ├── domain/       # ILayer interface, LayerMetadata, LayerConfig
    │   ├── application/  # LayerManager, LayerConfigService
    │   └── infrastructure/ # LayerRegistry, LayerFactory, adapters
    ├── attacks/          # система атак и эмуляторов
    │   ├── domain/       # AttackDefinition, AttackResult, IAttackEmulator
    │   ├── application/  # AttackExecutor, AttackManager
    │   └── infrastructure/ # AttackFactory, repositories, adapters
    ├── analysis/         # комплексный анализ результатов
    │   ├── domain/       # AnalysisResult, UnifiedReport, metrics
    │   ├── application/  # AnalysisService, ResultAnalyzer, ReportGenerator
    │   └── infrastructure/ # report exporters (CSV/JSON/HTML)
    ├── defense/          # Defense Pipeline (L1–L9)
    ├── models/           # model clients (OpenRouter, dummy, etc.)
    ├── testing/          # prompt-injection scenarios and runners
    ├── reporting/        # metrics aggregation and exports
    └── ui/               # PyQt presentation layer
```

Подробная документация по каждой фиче находится в `docs/features/*.md`.

Каждая фича следует единой внутренней структуре Clean Architecture:

- `domain` – entities и contracts (`Decision`, `PromptTest`, `PolicyRules`, `ILayer`, `AttackDefinition`).
- `application` – use-case logic (`DefensePipeline`, `TestRunner`, `LayerManager`, `AttackExecutor`).
- `infrastructure` – adapters (`PromptTestRepository`, `DummyModelClient`, implementations слоев, эмуляторы атак).
- `presentation` – UI adapters (currently only the PyQt feature).

## 
## Clean Architecture + Feature First

```
src/llm_security
├── core/                 # shared infrastructure (config loader, logging stubs)
├── shared/               # reusable helpers (reserved)
└── features/
    ├── defense/          # Defense Pipeline (Domain/Application/Infrastructure)
    ├── models/           # model clients (OpenRouter, dummy, etc.)
    ├── testing/          # prompt-injection scenarios and runners
    ├── reporting/        # metrics aggregation and exports
    └── ui/               # PyQt presentation layer
```

Detailed documentation for every feature lives in `docs/features/*.md`.

Each feature keeps the same internal layering:

- `domain` – entities and contracts (`Decision`, `PromptTest`, `PolicyRules`).
- `application` – use-case logic (`DefensePipeline`, `TestRunner`, `TestSuiteService`).
- `infrastructure` – adapters (`PromptTestRepository`, `DummyModelClient`, layer implementations).
- `presentation` – UI adapters (currently only the PyQt feature).

## Layers (Унифицированная система слоев)

- [`ILayer`](src/llm_security/features/layers/domain/interfaces.py:9) определяет унифицированный контракт для всех слоев защиты.
- [`LayerManager`](src/llm_security/features/layers/application/layer_manager.py:11) управляет жизненным циклом и конфигурацией слоев.
- [`LayerConfigService`](src/llm_security/features/layers/application/layer_config_service.py) обрабатывает конфигурации слоев из профилей.
- [`LayerRegistry`](src/llm_security/features/layers/infrastructure/layer_registry.py) и [`LayerFactory`](src/llm_security/features/layers/infrastructure/layer_factory.py) обеспечивают плагинную архитектуру.
- [`DefenseLayerAdapter`](src/llm_security/features/layers/infrastructure/defense_layer_adapter.py) адаптирует существующие слои L1-L9 к унифицированному интерфейсу.

## Attacks (Система атак и эмуляторов)

- [`AttackDefinition`](src/llm_security/features/attacks/domain/entities.py:27) описывает атаки с категориями и целевыми слоями.
- [`AttackExecutor`](src/llm_security/features/attacks/application/attack_executor.py:14) выполняет атаки асинхронно.
- [`AttackManager`](src/llm_security/features/attacks/application/attack_manager.py) координирует выполнение атак.
- [`AttackFactory`](src/llm_security/features/attacks/infrastructure/attack_factory.py:10) создает эмуляторы и шаблоны атак.
- Репозитории атак поддерживают индексацию по категориям и целевым слоям.

## Analysis (Комплексный анализ)

- [`AnalysisService`](src/llm_security/features/analysis/application/analysis_service.py:14) объединяет результаты тестов и атак.
- [`ResultAnalyzer`](src/llm_security/features/analysis/application/result_analyzer.py:13) выявляет уязвимости и генерирует рекомендации.
- [`MetricsCalculator`](src/llm_security/features/analysis/application/metrics_calculator.py) рассчитывает метрики по слоям и категориям атак.
- Экспортеры отчетов ([`CSV`](src/llm_security/features/analysis/infrastructure/report_exporters.py:28), [`JSON`](src/llm_security/features/analysis/infrastructure/report_exporters.py:74), [`HTML`](src/llm_security/features/analysis/infrastructure/report_exporters.py:144)) поддерживают множественные форматы.

## Defense Pipeline

- `IDefenseLayer` defines the contract (`before_send`, `after_recv`).
- `DefensePipeline` orchestrates sequential layer execution and returns `PipelineDecision`.
- YAML profiles (`config/profiles.yaml`) describe enabled layers and tunable parameters.
- Layer implementations (L1–L9) live under `infrastructure/layers/` and cover normalization, classifiers, policy enforcement, adversarial suffix trimming, output moderation, memory guard, and rate/scope controls drawn from DOC1/DOC2 guidance.

## Testing & Evaluation

- `PromptTestRepository` loads scenarios from `data/prompt_tests.yaml`.
- `TestRunner` coordinates defenses, model calls, evaluation, and timing.
- `OutputEvaluator` checks criteria to mark Pass/Fail.
- `TestSuiteService` exposes baseline, protected, and A/B suites for CLI/UI consumers.

## Reporting

- `MetricsAggregator` computes overall pass-rate, breakdowns by category and defense layer, and false-positive counts.
- Exporters: `json_reporter`, `csv_reporter`, `html_reporter`.

## UI (PyQt)

- `UISuiteController` bridges the PyQt layer with `TestSuiteService`.
- `MainWindow` implements profile selection, category filters, A/B toggles, and result tables.
- `ConnectionManagementDialog` provides CRUD interface for LLM connections with validation.
- Entry point `llm-security-ui` launches the GUI.

## Models (LLM Connections)

- Domain entities: `ConnectionConfig` (full config), `ConnectionInfo` (summary).
- Application service: `ModelConnectionService` handles CRUD, client caching, authentication resolution.
- Infrastructure: `ModelConnectionRepository` persists configs to YAML, with hydration/serialization.
- Supported providers: `DummyModelClient`, `OpenRouterModelClient` (extensible).
- Configuration stored in `config/llm_connections.yaml`, secrets via env vars.

## Additional Notes

- CLI (`llm-security-cli`) provides scripted execution and report exports.
- `DummyModelClient` simulates a vulnerable LLM for offline demos.
- Real integrations (e.g., `OpenRouterModelClient`) can be enabled by supplying API credentials; additional guard models can be plugged into L2/L7.
- LLM connection settings live in `config/llm_connections.yaml` and are resolved via `ModelConnectionService`, keeping secrets in environment variables and supporting per-environment profiles.
