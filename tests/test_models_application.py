"""Application layer tests for models module (connection service)."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict

from src.llm_security.features.models.application.connection_service import ModelConnectionService
from src.llm_security.features.models.domain.connection import ConnectionConfig, ConnectionInfo
from src.llm_security.features.models.infrastructure.connections_repository import ModelConnectionRepository
from src.llm_security.features.models.infrastructure.dummy import DummyModelClient
from src.llm_security.features.models.infrastructure.openrouter import OpenRouterModelClient
from src.llm_security.features.defense.domain.entities import PromptBundle


@pytest.fixture
def sample_config():
    """Sample connection config for testing."""
    return ConnectionConfig(
        id="test_openrouter",
        provider="openrouter",
        description="Test OpenRouter connection",
        model_id="gpt-3.5-turbo",
        base_url="https://api.example.com",
        timeout=30,
        headers={"Custom": "Header"},
        auth={"type": "env", "env_var": "TEST_API_KEY"},
    )


@pytest.fixture
def mock_repository():
    """Mock repository for testing."""
    repo = Mock(spec=ModelConnectionRepository)
    repo.load_all.return_value = {}
    repo.get.return_value = None
    return repo


@pytest.fixture
def service(mock_repository):
    """Service instance with mocked repository."""
    return ModelConnectionService(repository=mock_repository)


class TestModelConnectionService:
    """Test ModelConnectionService CRUD operations and client creation."""

    def test_list_connections_empty(self, service, mock_repository):
        """Test listing connections when none exist."""
        mock_repository.load_all.return_value = {}
        infos = service.list_connections()
        assert len(infos) == 1  # Should include built-in dummy
        assert infos[0].id == "dummy"
        assert infos[0].provider == "dummy"
        assert infos[0].description == "Built-in dummy client"

    def test_list_connections_with_configs(self, service, mock_repository, sample_config):
        """Test listing connections with existing configs."""
        configs = {"test_openrouter": sample_config}
        mock_repository.load_all.return_value = configs
        infos = service.list_connections()
        assert len(infos) == 2  # dummy + test connection
        # First should be dummy
        assert infos[0].id == "dummy"
        # Second should be the test connection
        assert infos[1].id == "test_openrouter"
        assert infos[1].provider == "openrouter"
        assert infos[1].description == "Test OpenRouter connection"

    def test_get_connection_config(self, service, mock_repository, sample_config):
        """Test getting a specific connection config."""
        mock_repository.get.return_value = sample_config
        config = service.get_connection_config("test_openrouter")
        assert config == sample_config
        mock_repository.get.assert_called_once_with("test_openrouter")

    def test_create_client_none_returns_dummy(self, service):
        """Test creating client with None connection_id returns DummyModelClient."""
        client = service.create_client(None)
        assert isinstance(client, DummyModelClient)
        assert client.model_id == "dummy"

    def test_create_client_dummy(self, service, mock_repository):
        """Test creating dummy client by ID."""
        mock_repository.get.side_effect = KeyError("Unknown connection")
        client = service.create_client("dummy")
        assert isinstance(client, DummyModelClient)
        assert client.model_id == "dummy"
        # Should be cached
        cached_client = service.create_client("dummy")
        assert client is cached_client

    def test_create_client_cached(self, service, mock_repository, sample_config):
        """Test client caching."""
        mock_repository.get.return_value = sample_config

        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            client1 = service.create_client("test_openrouter")
            client2 = service.create_client("test_openrouter")
            assert client1 is client2
            mock_repository.get.assert_called_once_with("test_openrouter")

    def test_create_client_openrouter(self, service, mock_repository, sample_config):
        """Test creating OpenRouter client."""
        mock_repository.get.return_value = sample_config

        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            client = service.create_client("test_openrouter")
            assert isinstance(client, OpenRouterModelClient)
            assert client.model_id == "gpt-3.5-turbo"
            assert client.base_url == "https://api.example.com"
            assert client.timeout == 30
            assert "Custom" in client.default_headers

    def test_create_client_unsupported_provider(self, service, mock_repository):
        """Test creating client with unsupported provider."""
        config = ConnectionConfig(id="test", provider="unsupported")
        mock_repository.get.return_value = config

        with pytest.raises(ValueError, match="Unsupported provider 'unsupported'"):
            service.create_client("test")

    def test_create_client_missing_env_var(self, service, mock_repository, sample_config):
        """Test creating client with missing environment variable."""
        mock_repository.get.return_value = sample_config

        # Ensure env var is not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="Environment variable 'TEST_API_KEY' is not set"):
                service.create_client("test_openrouter")

    def test_create_client_invalid_auth_config(self, service, mock_repository):
        """Test creating client with invalid auth configuration."""
        config = ConnectionConfig(
            id="test",
            provider="openrouter",
            auth={}  # Missing auth type
        )
        mock_repository.get.return_value = config

        with pytest.raises(ValueError, match="missing auth configuration"):
            service.create_client("test")

    def test_create_client_unsupported_auth_type(self, service, mock_repository):
        """Test creating client with unsupported auth type."""
        config = ConnectionConfig(
            id="test",
            provider="openrouter",
            auth={"type": "unsupported"}
        )
        mock_repository.get.return_value = config

        with pytest.raises(ValueError, match="Unsupported auth type 'unsupported'"):
            service.create_client("test")

    def test_create_client_missing_env_var_in_auth(self, service, mock_repository):
        """Test creating client with missing env_var in auth config."""
        config = ConnectionConfig(
            id="test",
            provider="openrouter",
            auth={"type": "env"}  # Missing env_var
        )
        mock_repository.get.return_value = config

        with pytest.raises(ValueError, match="requires auth.env_var"):
            service.create_client("test")

    def test_create_connection_success(self, service, mock_repository, sample_config):
        """Test creating a new connection successfully."""
        mock_repository.load_all.return_value = {}
        service.create_connection(sample_config)
        mock_repository.save.assert_called_once_with(sample_config)

    def test_create_connection_duplicate(self, service, mock_repository, sample_config):
        """Test creating connection that already exists."""
        mock_repository.load_all.return_value = {"test_openrouter": sample_config}
        with pytest.raises(ValueError, match="Connection 'test_openrouter' already exists"):
            service.create_connection(sample_config)

    def test_update_connection_success(self, service, mock_repository, sample_config):
        """Test updating existing connection."""
        mock_repository.load_all.return_value = {"test_openrouter": sample_config}
        updated_config = ConnectionConfig(
            id="test_openrouter",
            provider="openrouter",
            description="Updated description"
        )
        service.update_connection(updated_config)
        mock_repository.save.assert_called_once_with(updated_config)
        # Cache should be cleared
        assert "test_openrouter" not in service._client_cache

    def test_update_connection_not_exists(self, service, mock_repository, sample_config):
        """Test updating non-existent connection."""
        mock_repository.load_all.return_value = {}
        with pytest.raises(ValueError, match="Connection 'test_openrouter' does not exist"):
            service.update_connection(sample_config)

    def test_delete_connection_success(self, service, mock_repository):
        """Test deleting connection successfully."""
        mock_repository.load_all.return_value = {"test": Mock()}
        service.delete_connection("test")
        mock_repository.delete.assert_called_once_with("test")
        # Cache should be cleared
        assert "test" not in service._client_cache

    def test_delete_connection_dummy_forbidden(self, service):
        """Test that deleting dummy connection is forbidden."""
        with pytest.raises(ValueError, match="Cannot delete built-in dummy connection"):
            service.delete_connection("dummy")

    def test_client_cache_invalidation_on_update(self, service, mock_repository, sample_config):
        """Test that client cache is invalidated when connection is updated."""
        mock_repository.get.return_value = sample_config

        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            # Create and cache client
            client1 = service.create_client("test_openrouter")
            assert "test_openrouter" in service._client_cache

            # Update connection
            mock_repository.load_all.return_value = {"test_openrouter": sample_config}
            service.update_connection(sample_config)

            # Cache should be cleared
            assert "test_openrouter" not in service._client_cache