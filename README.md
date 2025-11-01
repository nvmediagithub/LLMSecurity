# LLMSecurity Lab

Платформа для тестирования устойчивости LLM к prompt-инъекциям. Проект построен по принципам Clean Architecture и feature-first: каждая ключевая функциональность оформлена как самостоятельный модуль со своими доменными сущностями, use-case слоями и инфраструктурой.

## Ключевые возможности
- Конвейер защит (Defense Pipeline) с независимыми слоями L1-L9 и YAML-профилями.
- Тест-раннер с A/B-прогонами (без защит и с выбранным профилем), сбором метрик и артефактов.
- PyQt GUI с панелью защиты, сводкой результатов и фильтрами по сработавшим слоям.
- Экспорт отчётов (CSV/JSON/HTML) и сохранение логов для аудита.

## Структура каталога
```
src/llm_security
├── core                # общие сервисы (конфиги, логирование, сериализация)
├── shared              # переиспользуемые утилиты и типы
└── features            # feature-first модули
    ├── defense         # конвейер защит L1-L9
    ├── models          # абстракции клиентов LLM (OpenRouter, локальные)
    ├── testing         # тесты prompt-инъекций, раннер и оценка
    ├── reporting       # экспорт результатов в CSV/JSON/HTML
    └── ui              # PyQt-приложение и интеракция
```

Конфигурация профилей `config/profiles.yaml`, политики `config/policy.yaml`, сценарии тестов `data/prompt_tests.yaml`.

## Быстрый старт
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .

# CLI прогон тестов
llm-security-cli run --model dummy --profile strict_demo

# Запуск GUI
llm-security-ui
```

> Для работы GUI установите PyQt6: `pip install PyQt6`.

## Документация
- Архитектура: `docs/architecture.md`
- Требования: `docs/requirements_summary.md`
- Агенты и политика безопасности: `AGENTS.md`
- Документация по фичам: `docs/features/*.md`

## Развитие
- Добавляйте новые слои защиты как реализации `IDefenseLayer`.
- Расширяйте каталог тестов, пополняя `data/prompt_tests.yaml`.
- Подключайте реальные LLM через `features.models.infrastructure`.
- Используйте A/B-метрики для демонстрации эффекта защит.
