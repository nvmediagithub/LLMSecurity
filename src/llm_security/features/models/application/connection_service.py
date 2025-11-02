from __future__ import annotations

import os
from typing import Dict, List, Optional

from ..domain.connection import ConnectionConfig, ConnectionInfo
from ..domain.interfaces import ModelClient
from ..infrastructure.connections_repository import ModelConnectionRepository
from ..infrastructure.dummy import DummyModelClient
from ..infrastructure.openrouter import OpenRouterModelClient


class ModelConnectionService:
    """Сервис управления подключениями к LLM."""

    def __init__(self, repository: ModelConnectionRepository | None = None):
        self._repository = repository or ModelConnectionRepository()
        self._client_cache: Dict[str, ModelClient] = {}

    def list_connections(self) -> List[ConnectionInfo]:
        configs = self._repository.load_all()
        infos = [
            ConnectionInfo(id=config.id, provider=config.provider, description=config.description or config.provider)
            for config in configs.values()
        ]
        if "dummy" not in configs:
            infos.insert(0, ConnectionInfo(id="dummy", provider="dummy", description="Built-in dummy client"))
        return infos

    def get_connection_config(self, connection_id: str) -> ConnectionConfig:
        """Получает конфигурацию подключения."""
        return self._repository.get(connection_id)

    def create_client(self, connection_id: Optional[str]) -> ModelClient:
        if connection_id is None:
            return DummyModelClient()
        if connection_id in self._client_cache:
            return self._client_cache[connection_id]
        try:
            config = self._repository.get(connection_id)
        except KeyError:
            if connection_id == "dummy":
                client = DummyModelClient()
                self._client_cache[connection_id] = client
                return client
            raise
        client = self._build_client(config)
        self._client_cache[connection_id] = client
        return client

    # region internal
    def _build_client(self, config: ConnectionConfig) -> ModelClient:
        provider = config.provider.lower()
        if provider == "dummy":
            return DummyModelClient(model_id=config.model_id or "dummy")
        if provider == "openrouter":
            return self._build_openrouter_client(config)
        raise ValueError(f"Unsupported provider '{config.provider}' for connection '{config.id}'")

    def _build_openrouter_client(self, config: ConnectionConfig) -> OpenRouterModelClient:
        api_key = self._resolve_api_key(config)
        return OpenRouterModelClient(
            model_id=config.model_id or "",
            base_url=config.base_url or OpenRouterModelClient.base_url,
            timeout=config.timeout or 60,
            default_headers=config.headers or None,
            api_key=api_key,
        )

    def create_connection(self, config: ConnectionConfig) -> None:
        """Создает новое подключение."""
        if config.id in self._repository.load_all():
            raise ValueError(f"Connection '{config.id}' already exists")
        self._repository.save(config)

    def update_connection(self, config: ConnectionConfig) -> None:
        """Обновляет существующее подключение."""
        if config.id not in self._repository.load_all():
            raise ValueError(f"Connection '{config.id}' does not exist")
        self._repository.save(config)
        # Очищаем кэш клиента, чтобы использовать обновленную конфигурацию
        self._client_cache.pop(config.id, None)

    def delete_connection(self, connection_id: str) -> None:
        """Удаляет подключение."""
        if connection_id == "dummy":
            raise ValueError("Cannot delete built-in dummy connection")
        self._repository.delete(connection_id)
        self._client_cache.pop(connection_id, None)

    def _resolve_api_key(self, config: ConnectionConfig) -> str:
        auth_type = config.auth.get("type")
        if auth_type == "env":
            env_var = config.auth.get("env_var")
            if not env_var:
                raise ValueError(f"Connection '{config.id}' requires auth.env_var")
            value = os.getenv(env_var)
            if not value:
                raise RuntimeError(f"Environment variable '{env_var}' is not set for connection '{config.id}'")
            return value
        if not auth_type:
            raise ValueError(f"Connection '{config.id}' missing auth configuration")
        raise ValueError(f"Unsupported auth type '{auth_type}' for connection '{config.id}'")

    # endregion
