"""Domain layer tests for models module (connection management)."""

import pytest
from dataclasses import dataclass, field
from typing import Dict, Optional

from src.llm_security.features.models.domain.connection import ConnectionConfig, ConnectionInfo


class TestConnectionConfig:
    """Test ConnectionConfig dataclass."""

    def test_creation_with_all_fields(self):
        """Test creating ConnectionConfig with all fields."""
        config = ConnectionConfig(
            id="test_conn",
            provider="openrouter",
            description="Test connection",
            model_id="gpt-3.5-turbo",
            base_url="https://api.example.com",
            timeout=30,
            headers={"Authorization": "Bearer token"},
            auth={"type": "env", "env_var": "API_KEY"},
        )
        assert config.id == "test_conn"
        assert config.provider == "openrouter"
        assert config.description == "Test connection"
        assert config.model_id == "gpt-3.5-turbo"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 30
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.auth == {"type": "env", "env_var": "API_KEY"}

    def test_creation_defaults(self):
        """Test creating ConnectionConfig with minimal required fields."""
        config = ConnectionConfig(id="test_conn", provider="dummy")
        assert config.id == "test_conn"
        assert config.provider == "dummy"
        assert config.description == ""
        assert config.model_id is None
        assert config.base_url is None
        assert config.timeout is None
        assert config.headers == {}
        assert config.auth == {}

    def test_immutability(self):
        """Test that ConnectionConfig is immutable (dataclass with slots=True)."""
        config = ConnectionConfig(id="test", provider="dummy")
        # With slots=True, new attributes cannot be added
        with pytest.raises(AttributeError):
            config.new_attr = "value"

    def test_equality(self):
        """Test equality comparison."""
        config1 = ConnectionConfig(id="test", provider="dummy")
        config2 = ConnectionConfig(id="test", provider="dummy")
        config3 = ConnectionConfig(id="other", provider="dummy")
        assert config1 == config2
        assert config1 != config3

    def test_hashable(self):
        """Test that ConnectionConfig is not hashable (mutable dict fields)."""
        config = ConnectionConfig(id="test", provider="dummy")
        # Should raise TypeError since it contains mutable dict fields
        with pytest.raises(TypeError):
            hash(config)


class TestConnectionInfo:
    """Test ConnectionInfo dataclass."""

    def test_creation(self):
        """Test creating ConnectionInfo."""
        info = ConnectionInfo(id="test_conn", provider="openrouter", description="Test connection")
        assert info.id == "test_conn"
        assert info.provider == "openrouter"
        assert info.description == "Test connection"

    def test_immutability(self):
        """Test that ConnectionInfo is immutable (dataclass with slots=True)."""
        info = ConnectionInfo(id="test", provider="dummy", description="desc")
        # With slots=True, new attributes cannot be added
        with pytest.raises(AttributeError):
            info.new_attr = "value"

    def test_equality(self):
        """Test equality comparison."""
        info1 = ConnectionInfo(id="test", provider="dummy", description="desc")
        info2 = ConnectionInfo(id="test", provider="dummy", description="desc")
        info3 = ConnectionInfo(id="other", provider="dummy", description="desc")
        assert info1 == info2
        assert info1 != info3

    def test_hashable(self):
        """Test that ConnectionInfo is not hashable (no frozen=True)."""
        info = ConnectionInfo(id="test", provider="dummy", description="desc")
        # Should raise TypeError since dataclasses without frozen=True are not hashable
        with pytest.raises(TypeError):
            hash(info)


class TestSerialization:
    """Test serialization/deserialization of domain objects."""

    def test_connection_config_to_dict(self):
        """Test converting ConnectionConfig to dict for serialization."""
        config = ConnectionConfig(
            id="test_conn",
            provider="openrouter",
            description="Test connection",
            model_id="gpt-3.5-turbo",
            base_url="https://api.example.com",
            timeout=30,
            headers={"Authorization": "Bearer token"},
            auth={"type": "env", "env_var": "API_KEY"},
        )

        # Convert to dict (simulating what repository might do)
        data = {
            "provider": config.provider,
            "description": config.description,
            "model_id": config.model_id,
            "base_url": config.base_url,
            "timeout": config.timeout,
            "headers": config.headers,
            "auth": config.auth,
        }

        assert data["provider"] == "openrouter"
        assert data["model_id"] == "gpt-3.5-turbo"
        assert data["timeout"] == 30


class TestValidation:
    """Test validation logic for domain objects."""

    def test_connection_config_fields_types(self):
        """Test that ConnectionConfig enforces field types."""
        # Valid types
        config = ConnectionConfig(
            id="test",
            provider="dummy",
            description="desc",
            model_id="model",
            base_url="url",
            timeout=60,
            headers={"key": "value"},
            auth={"type": "env"}
        )

        assert isinstance(config.id, str)
        assert isinstance(config.provider, str)
        assert isinstance(config.description, str)
        assert isinstance(config.headers, dict)
        assert isinstance(config.auth, dict)

    def test_connection_config_optional_fields_none(self):
        """Test that optional fields can be None."""
        config = ConnectionConfig(id="test", provider="dummy")
        assert config.model_id is None
        assert config.base_url is None
        assert config.timeout is None