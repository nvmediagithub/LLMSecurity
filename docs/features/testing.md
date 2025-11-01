# Feature: Testing & Evaluation

## Назначение
Модуль Testing отвечает за выполнение сценариев prompt-инъекций, оценку ответов и сбор метрик. Основные идеи почерпнуты из DOC1/DOC2: автоматизация тестов, A/B сравнение с защитами и визуализация вклада каждого слоя.

## Основные компоненты
- **Domain** `domain/models.py`, `domain/results.py` – описывают `PromptTest`, `PassCriteria`, `TestRunResult`, `LayerLog`.
- **Infrastructure** `infrastructure/repositories/yaml_tests_repository.py` – загрузка `data/prompt_tests.yaml`.
- **Application**
  - `application/evaluator.py` – `OutputEvaluator`, проверяет Pass/Fail по критериям.
  - `application/runner.py` – `TestRunner`, выполняет защиту → модель → оценку.
  - `application/service.py` – `TestSuiteService`, high-level API для CLI и UI, поддерживает baseline/protected/AB режимы.

## Тестовые сценарии
- Определены в `data/prompt_tests.yaml`:
  - Категории: `direct_attack`, `role_play`, `obfuscation`, `payload_split`, `adversarial_suffix`, `prompt_leakage`, `indirect_html`, контрольные запросы.
  - Для каждого теста заданы `system_prompt`, `user_prompt`, `pass_criteria`, `severity`.
- DOC2 содержит описание типовых кейсов (прямые, косвенные, leakage, adversarial suffix) – они отражены в YAML.

## Процесс выполнения теста
1. `TestRunner` формирует `PromptBundle` и запускает `DefensePipeline`.
2. При `BLOCK`/`ESCALATE` фиксирует результат без обращения к модели.
3. При `ALLOW` вызывает `ModelClient.generate`.
4. После `guard_after` выполняется `OutputEvaluator`.
5. Результат логируется в `TestRunResult`.

## Метрики
- `MetricsAggregator` вычисляет:
  - Общий Pass%, Passed/Failed по категориям.
  - Вклад защитных слоёв (`by_layer`), ложные срабатывания на контрольных тестах.
  - Значение используется в отчётах и UI.
- A/B режим (`TestSuiteService.run_ab`) сравнивает baseline vs профиль и рассчитывает `Δ Pass%`.

## Расширение
- Добавление нового теста: обновить `data/prompt_tests.yaml`.
- Точная проверка: `PassCriteria` легко расширить (например, регулярные выражения или scoring).
- Поддержка OpenAI Evaluate: добавить адаптер в `TestSuiteService`.
- Интеграция с внешними метриками (toxicity score, latency) — хранить в `metadata`/`LayerLog`.

