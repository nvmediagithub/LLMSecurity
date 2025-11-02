# Feature: Model Clients

## Назначение
Модуль Models предоставляет унифицированный интерфейс обращения к LLM, используемый Test Runner и Defense Pipeline. DOC1 и DOC2 подчёркивают необходимость тестирования разных поставщиков (локальные, OpenRouter и др.), а также аккуратного обращения с ключами.

## Архитектура
- `domain/interfaces.py` – протокол `ModelClient` с методом `generate(PromptBundle) -> str`.
- `domain/connection.py` – описание `ConnectionConfig` и `ConnectionInfo`.
- `infrastructure/dummy.py` – `DummyModelClient`, имитирует уязвимую модель для оффлайн-тестов и демо.
- `infrastructure/openrouter.py` – адаптер к OpenRouter API (использует HTTP POST, читает `OPENROUTER_API_KEY`).
- `infrastructure/connections_repository.py` – загрузка `config/llm_connections.yaml`.
- `application/connection_service.py` – фабрика клиентов по ID подключения.

## Жизненный цикл вызова
1. `TestRunner` передаёт `PromptBundle`.
2. Клиент формирует запрос (system/user prompts) и обращается к модели.
3. Ответ возвращается в Defense Pipeline для post-processing.

## Настройка подключений
- Конфигурация хранится в `config/llm_connections.yaml`. Пример:
  ```yaml
  connections:
    openrouter_qwen_demo:
      provider: openrouter
      model_id: "qwen/QwQ-32B"
      auth:
        type: env
        env_var: OPENROUTER_API_KEY
      headers:
        HTTP-Referer: "https://llm-security-lab"
  ```
- Поддерживаются поля:
  - `provider` – тип клиента (`dummy`, `openrouter`, и т.д.).
  - `model_id` – целевая модель в API.
  - `auth` – схема авторизации (сейчас `type: env` + `env_var`).
  - `headers` – дополнительные заголовки (например, `HTTP-Referer`, `X-Title`).
  - `timeout`, `base_url` – переопределение значений по умолчанию.
- `ModelConnectionService` валидирует конфигурацию, достаёт секреты из переменных окружения и кэширует клиенты.
- CLI (`llm-security-cli connections`) и UI показывают доступные подключения; аргумент `--connection` позволяет выбрать нужный контур.

## Безопасность
- API ключи хранятся в переменных окружения (не в коде).
- Ошибки сети/авторизации пробрасываются в TestRunner для логирования.
- В соответствии с рекомендациями OpenAI – перед передачей данным в модель проходит обработку защитными слоями.

## Расширение
- Добавление новых клиентов (Azure OpenAI, OpenAI API, локальные движки) через реализацию `ModelClient`.
- Поддержка потоковых ответов – расширить интерфейс или добавить отдельную абстракцию.
- Кэширование ответов: можно внедрить в новый класс-обёртку.
