from __future__ import annotations

from typing import Dict, Mapping

from ....core.config.loader import ConfigLoader
from ..domain.connection import ConnectionConfig


class ModelConnectionRepository:
    """Загружает конфигурации подключений к LLM из YAML."""

    def __init__(self, loader: ConfigLoader | None = None):
        self._loader = loader or ConfigLoader()
        self._cache: Dict[str, ConnectionConfig] = {}

    def load_all(self, force: bool = False) -> Dict[str, ConnectionConfig]:
        if force or not self._cache:
            raw = self._loader.load_connections().get("connections", {})
            configs: Dict[str, ConnectionConfig] = {}
            for conn_id, data in raw.items():
                configs[conn_id] = self._hydrate(conn_id, data)
            self._cache = configs
        return self._cache

    def get(self, connection_id: str) -> ConnectionConfig:
        configs = self.load_all()
        if connection_id not in configs:
            raise KeyError(f"Unknown LLM connection: {connection_id}")
        return configs[connection_id]

    def save(self, config: ConnectionConfig) -> None:
        """Сохраняет новую или обновленную конфигурацию подключения."""
        all_configs = self.load_all()
        all_configs[config.id] = config
        data = self._serialize_all(all_configs)
        self._loader.save_connections(data)
        self._cache = all_configs

    def delete(self, connection_id: str) -> None:
        """Удаляет конфигурацию подключения."""
        all_configs = self.load_all()
        if connection_id not in all_configs:
            raise KeyError(f"Connection '{connection_id}' not found")
        del all_configs[connection_id]
        data = self._serialize_all(all_configs)
        self._loader.save_connections(data)
        self._cache = all_configs

    @staticmethod
    def _hydrate(connection_id: str, data: Mapping[str, object]) -> ConnectionConfig:
        model_id = data.get("model_id")
        base_url = data.get("base_url")
        timeout = data.get("timeout")
        headers_raw = data.get("headers", {})
        auth_raw = data.get("auth", {})
        return ConnectionConfig(
            id=connection_id,
            provider=str(data.get("provider", "dummy")),
            description=str(data.get("description", "")),
            model_id=str(model_id) if model_id is not None else None,
            base_url=str(base_url) if base_url is not None else None,
            timeout=int(timeout) if timeout is not None and isinstance(timeout, (int, str)) else None,
            headers={str(k): str(v) for k, v in dict(headers_raw).items()} if isinstance(headers_raw, dict) else {},
            auth={str(k): str(v) for k, v in dict(auth_raw).items()} if isinstance(auth_raw, dict) else {},
        )

    @staticmethod
    def _serialize_all(configs: Dict[str, ConnectionConfig]) -> Dict[str, object]:
        """Сериализует все конфигурации в формат YAML."""
        result: Dict[str, object] = {"connections": {}}
        connections = result["connections"]
        if not isinstance(connections, dict):
            connections = {}
            result["connections"] = connections
        for config in configs.values():
            connections[config.id] = {
                "provider": config.provider,
                "description": config.description,
                "model_id": config.model_id,
                "base_url": config.base_url,
                "timeout": config.timeout,
                "headers": config.headers,
                "auth": config.auth,
            }
        return result
