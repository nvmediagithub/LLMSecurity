# Feature: Defense Pipeline

## Назначение
Конвейер защит (L1–L9) реализует многоуровневую оборону против prompt-инъекций, как рекомендовано в DOC1/DOC2 и OWASP LLM Top 10: приоритет системных правил, фильтрация данных, контроль инструментов и аудит.

## Архитектура
- `domain/entities.py` – типы `Decision`, `DefenseResult`, `PromptBundle`.
- `domain/interfaces.py` – контракт `IDefenseLayer`.
- `domain/profile.py` и `application/profiles_service.py` – загрузка профилей из `config/profiles.yaml`.
- `application/pipeline.py` – оркестратор `DefensePipeline`.
- `infrastructure/factory.py` – связывает профиль с реализациями L1–L9.
- `infrastructure/layers/*` – конкретные слои защиты.

## Слои защиты (L1–L9)
| ID | Назначение | Реализация | Источник требований |
|----|------------|------------|---------------------|
| L1 InputSanitizer | NFC-нормализация, фильтр невидимых символов | `l1_input_sanitizer.py` | DOC1 §2.1 (омографы) |
| L2 PromptClassifier | Эвристика + ключевые слова для детекта jailbreak | `l2_prompt_classifier.py` | DOC1 табл. слоёв, OWASP LLM01 |
| L3 ContextFirewall | Очистка HTML, блок скрытых инструкций | `l3_context_firewall.py` | DOC1 §2.3, DOC2 косвенные атаки |
| L4 PolicyEngine | Запрет смены роли, раскрытия промпта, опасных действий | `l4_policy_engine.py`, `config/policy.yaml` | DOC1 §2.4 |
| L5 ToolGatekeeper | Контроль инструментов и ответов, требование токенов | `l5_tool_gatekeeper.py` | DOC1 §2.5, NCSC guidance |
| L6 AdversarialSuffix | Срез энтропийных хвостов, бессмысленные суффиксы | `l6_suffix_detector.py` | DOC1 §2.6 |
| L7 OutputGuard | Пост-модерация ответов | `l7_output_guard.py` | DOC1 §2.7 |
| L8 MemoryGuard | Запрет записи инструкций в память | `l8_memory_guard.py` | DOC1 §2.8 |
| L9 RateScopeGuard | Лимиты частоты и размера | `l9_rate_scope_guard.py` | DOC1 §2.9 |

## Конфигурация
- **Профили**: `config/profiles.yaml` – включенные слои и параметры (стройнные профили `strict_demo`, `research`, `custom`).
- **Политики**: `config/policy.yaml` – запреты на роли, раскрытие скрытых инструкций, ключи эскалации.

## Поток данных
1. `PromptBundle` формируется TestRunner/CLI/UI.
2. `DefensePipeline.guard_before` вызывает слои в порядке профиля.
3. После ответа модели `guard_after` повторяет цикл.
4. Решение (`allow`, `block`, `rewrite`, `escalate`) и `layer_logs` возвращаются в TestRunner.

## Метрики и аудит
- Каждый слой возвращает `DefenseResult` с `metadata`.
- CLI/отчеты показывают вклад слоёв (см. JSON/HTML отчеты).
- Поле `false_positive` рассчитывается в MetricsAggregator при работе с контрольными тестами.

## Расширение
- Добавление нового слоя: реализовать `IDefenseLayer`, зарегистрировать его в `DefensePipelineBuilder`.
- Интеграция внешних guard-моделей: расширить L2/L7 адаптерами к Llama Guard, OpenAI Moderation, NeMo Guardrails.
- Настройка порогов: обновить `profiles.yaml` (порог L2, ключевые слова L7 и т.д.).

