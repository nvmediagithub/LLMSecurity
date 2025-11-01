# Feature: Reporting

## Назначение
Модуль Reporting собирает метрики и формирует артефакты (CSV, JSON, HTML), позволяя демонстрировать эффект защит, как рекомендовано в DOC1 (A/B-прогоны, визуализация вклада слоёв) и DOC2 (отчёты для конференций).

## Компоненты
- `application/aggregator.py` – `MetricsAggregator`, вычисляет Pass%, разбивки по категориям и слоям, количество ложных срабатываний.
- `infrastructure/csv_reporter.py` – экспорт в CSV (разделитель `;`).
- `infrastructure/json_reporter.py` – экспорт подробного JSON (включая layer logs, timestamps).
- `infrastructure/html_reporter.py` – HTML-отчёт с таблицами и краткой сводкой.

## Данные для отчётов
`TestRunResult` содержит:
- `evaluation` (Pass/Fail, причина),
- `defense_decision`,
- `defense_logs_before/after` – список слоёв и их решений,
- временные метки (`started_at`, `finished_at`),
- текст ответа.

MetricsAggregator вычисляет:
- `pass_rate` – ориентир устойчивости модели,
- `by_category` – сравнение по видам атак (direct, obfuscation и др.),
- `by_layer` – вклад каждого слоя в блокировки/перезаписи,
- `false_positives` – помогает калибровать профили и избегать агрессивных настроек.

## Интеграция
- CLI (`llm-security-cli`) может экспортировать отчёты любой комбинацией флагов `--export-json`, `--export-csv`, `--export-html`.
- GUI может использовать агрегатор для отображения сводки в интерфейсе (Pass%, Δ Pass%).

## Расширение
- Добавление формата PDF – подключить генератор (WeasyPrint/ReportLab) на базе JSON-данных.
- Интеграция с SIEM – отправка событий через REST/Message Queue.
- Дэшборды – импорт JSON в BI-инструменты или Grafana.

