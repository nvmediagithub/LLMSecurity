# Architecture Guide

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
- Entry point `llm-security-ui` launches the GUI.

## Additional Notes

- CLI (`llm-security-cli`) provides scripted execution and report exports.
- `DummyModelClient` simulates a vulnerable LLM for offline demos.
- Real integrations (e.g., `OpenRouterModelClient`) can be enabled by supplying API credentials; additional guard models can be plugged into L2/L7.

