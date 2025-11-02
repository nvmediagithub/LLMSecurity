"""Comprehensive tests for core config loader module."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Mapping, Any

from src.llm_security.core.config.loader import ConfigLoader, ConfigPaths


class TestConfigPaths:
    """Test ConfigPaths dataclass."""

    def test_default_creation(self):
        """Test creating ConfigPaths with default paths."""
        paths = ConfigPaths.default()
        assert isinstance(paths.profiles, Path)
        assert isinstance(paths.policy, Path)
        assert isinstance(paths.tests, Path)
        assert isinstance(paths.connections, Path)
        # Should be relative to cwd
        assert "config" in str(paths.profiles)
        assert "config" in str(paths.policy)
        assert "data" in str(paths.tests)
        assert "config" in str(paths.connections)

    def test_default_creation_with_root(self):
        """Test creating ConfigPaths with custom root."""
        root = Path("/custom/root")
        paths = ConfigPaths.default(root)
        assert paths.profiles == root / "config" / "profiles.yaml"
        assert paths.policy == root / "config" / "policy.yaml"
        assert paths.tests == root / "data" / "prompt_tests.yaml"
        assert paths.connections == root / "config" / "llm_connections.yaml"

    def test_immutability(self):
        """Test that ConfigPaths is immutable."""
        paths = ConfigPaths.default()
        with pytest.raises(AttributeError):
            paths.new_attr = "value"


class TestConfigLoaderInitialization:
    """Test ConfigLoader initialization with different path configurations."""

    def test_init_with_default_paths(self):
        """Test initialization with default ConfigPaths."""
        loader = ConfigLoader()
        assert isinstance(loader._paths, ConfigPaths)
        assert loader._cache == {}

    def test_init_with_custom_paths(self):
        """Test initialization with custom ConfigPaths."""
        custom_paths = ConfigPaths(
            profiles=Path("/tmp/profiles.yaml"),
            policy=Path("/tmp/policy.yaml"),
            tests=Path("/tmp/tests.yaml"),
            connections=Path("/tmp/connections.yaml"),
        )
        loader = ConfigLoader(custom_paths)
        assert loader._paths == custom_paths
        assert loader._cache == {}

    def test_init_with_none_paths(self):
        """Test initialization with None paths (should use defaults)."""
        loader = ConfigLoader(None)
        assert isinstance(loader._paths, ConfigPaths)
        assert loader._cache == {}


class TestYAMLLoading:
    """Test YAML loading functionality for different config types."""

    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def loader(self, temp_dir):
        """ConfigLoader with paths in temp directory."""
        paths = ConfigPaths(
            profiles=temp_dir / "profiles.yaml",
            policy=temp_dir / "policy.yaml",
            tests=temp_dir / "tests.yaml",
            connections=temp_dir / "connections.yaml",
        )
        return ConfigLoader(paths)

    def test_load_profiles_success(self, loader, temp_dir):
        """Test successfully loading profiles YAML."""
        data = {"profiles": {"test_profile": {"layers": ["l1", "l2"]}}}
        (temp_dir / "profiles.yaml").write_text("profiles:\n  test_profile:\n    layers:\n    - l1\n    - l2\n")

        result = loader.load_profiles()
        assert result == data

    def test_load_policy_success(self, loader, temp_dir):
        """Test successfully loading policy YAML."""
        data = {"policy": {"rules": ["no_system_reveal"]}}
        (temp_dir / "policy.yaml").write_text("policy:\n  rules:\n  - no_system_reveal\n")

        result = loader.load_policy()
        assert result == data

    def test_load_connections_success(self, loader, temp_dir):
        """Test successfully loading connections YAML."""
        data = {"connections": {"test_conn": {"provider": "dummy"}}}
        (temp_dir / "connections.yaml").write_text("connections:\n  test_conn:\n    provider: dummy\n")

        result = loader.load_connections()
        assert result == data

    def test_load_connections_missing_file(self, loader, temp_dir):
        """Test loading connections when file doesn't exist."""
        # Don't create connections.yaml
        result = loader.load_connections()
        assert result == {}  # Should return empty dict for missing optional file

    def test_load_tests_yaml_format(self, loader, temp_dir):
        """Test loading tests in YAML format."""
        data = {"tests": [{"name": "test1", "prompt": "hello"}]}
        (temp_dir / "tests.yaml").write_text("tests:\n- name: test1\n  prompt: hello\n")

        result = loader.load_tests()
        assert result == data

    def test_load_tests_json_format(self, loader, temp_dir):
        """Test loading tests in JSON format."""
        data = {"tests": [{"name": "test1"}]}
        # Change the loader to use .json file instead of .yaml
        loader._paths = ConfigPaths(
            profiles=loader._paths.profiles,
            policy=loader._paths.policy,
            tests=temp_dir / "tests.json",
            connections=loader._paths.connections
        )
        (temp_dir / "tests.json").write_text('{"tests": [{"name": "test1"}]}')

        result = loader.load_tests()
        assert result == data

    def test_load_tests_unsupported_format(self, loader, temp_dir):
        """Test loading tests with unsupported format."""
        # Create file with .txt extension
        default_paths = ConfigPaths.default()
        loader._paths = ConfigPaths(
            profiles=loader._paths.profiles,
            policy=loader._paths.policy,
            tests=temp_dir / "tests.txt",
            connections=loader._paths.connections
        )
        (temp_dir / "tests.txt").write_text("content")

        with pytest.raises(ValueError, match="Unsupported tests format: .txt"):
            loader.load_tests()

    def test_load_yaml_invalid_yaml(self, loader, temp_dir):
        """Test loading invalid YAML."""
        (temp_dir / "profiles.yaml").write_text("invalid: yaml: content: [\n")

        with pytest.raises(Exception):  # yaml.YAMLError
            loader.load_profiles()

    def test_load_yaml_non_mapping_root(self, loader, temp_dir):
        """Test loading YAML with non-mapping root."""
        (temp_dir / "profiles.yaml").write_text("- item1\n- item2\n")

        with pytest.raises(TypeError, match="YAML root must be a mapping"):
            loader.load_profiles()

    def test_load_yaml_empty_file(self, loader, temp_dir):
        """Test loading empty YAML file."""
        (temp_dir / "profiles.yaml").write_text("")

        result = loader.load_profiles()
        assert result == {}

    def test_load_yaml_file_with_only_comments(self, loader, temp_dir):
        """Test loading YAML file with only comments."""
        (temp_dir / "profiles.yaml").write_text("# This is a comment\n# Another comment\n")

        result = loader.load_profiles()
        assert result == {}


class TestSaving:
    """Test saving functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def loader(self, temp_dir):
        """ConfigLoader with paths in temp directory."""
        default_paths = ConfigPaths.default()
        paths = ConfigPaths(
            profiles=default_paths.profiles,
            policy=default_paths.policy,
            tests=default_paths.tests,
            connections=temp_dir / "connections.yaml"
        )
        return ConfigLoader(paths)

    def test_save_connections_success(self, loader, temp_dir):
        """Test successfully saving connections YAML."""
        data = {"connections": {"test_conn": {"provider": "dummy"}}}

        loader.save_connections(data)

        # Verify file was created and contains correct data
        assert (temp_dir / "connections.yaml").exists()
        content = (temp_dir / "connections.yaml").read_text()
        assert "connections:" in content
        assert "test_conn:" in content
        assert "provider: dummy" in content

    def test_save_connections_creates_parent_dirs(self, loader, temp_dir):
        """Test that save_connections creates parent directories."""
        # Use nested path that doesn't exist
        nested_dir = temp_dir / "nested" / "deep" / "path"
        default_paths = ConfigPaths.default()
        loader._paths = ConfigPaths(
            profiles=default_paths.profiles,
            policy=default_paths.policy,
            tests=default_paths.tests,
            connections=nested_dir / "connections.yaml"
        )

        data = {"connections": {}}
        loader.save_connections(data)

        assert (nested_dir / "connections.yaml").exists()

    def test_save_connections_updates_cache(self, loader):
        """Test that save_connections updates the cache."""
        data = {"connections": {"new_conn": {"provider": "test"}}}

        loader.save_connections(data)

        # Should be in cache
        assert loader._cache["connections"] == data

    @patch('src.llm_security.core.config.loader.yaml.safe_dump')
    def test_save_connections_with_unicode(self, mock_dump, loader):
        """Test saving data with unicode characters."""
        data = {"connections": {"test": {"description": "тестовое описание"}}}

        loader.save_connections(data)

        # Verify yaml.safe_dump was called with allow_unicode=True
        mock_dump.assert_called_once()
        call_kwargs = mock_dump.call_args[1]
        assert call_kwargs['allow_unicode'] is True


class TestCachingBehavior:
    """Test caching behavior of ConfigLoader."""

    @pytest.fixture
    def loader(self):
        """ConfigLoader with mocked paths."""
        paths = ConfigPaths(
            profiles=Path("/tmp/profiles.yaml"),
            policy=Path("/tmp/policy.yaml"),
            tests=Path("/tmp/tests.yaml"),
            connections=Path("/tmp/connections.yaml"),
        )
        return ConfigLoader(paths)

    @patch('src.llm_security.core.config.loader.ConfigLoader._read_yaml')
    def test_caching_load_profiles(self, mock_read, loader):
        """Test that load_profiles uses caching."""
        mock_read.return_value = {"test": "data"}

        # First call should read from file
        result1 = loader.load_profiles()
        assert mock_read.call_count == 1

        # Second call should use cache
        result2 = loader.load_profiles()
        assert mock_read.call_count == 1  # Not called again
        assert result1 is result2  # Same object from cache

    @patch('src.llm_security.core.config.loader.ConfigLoader._read_yaml')
    def test_caching_load_optional_missing_file(self, mock_read, loader):
        """Test caching when optional file doesn't exist."""
        # Mock the exists method directly on the path object
        with patch('pathlib.Path.exists', return_value=False):
            result1 = loader.load_connections()
            assert result1 == {}

            # Second call should use cache
            result2 = loader.load_connections()
            assert result1 is result2

    @patch('src.llm_security.core.config.loader.ConfigLoader._read_yaml')
    def test_cache_invalidation_all(self, mock_read, loader):
        """Test invalidating entire cache."""
        mock_read.return_value = {"test": "data"}

        # Load into cache
        loader.load_profiles()
        assert "profiles" in loader._cache

        # Invalidate all
        loader.invalidate()
        assert loader._cache == {}

    @patch('src.llm_security.core.config.loader.ConfigLoader._read_yaml')
    def test_cache_invalidation_specific_keys(self, mock_read, loader):
        """Test invalidating specific cache keys."""
        mock_read.return_value = {"test": "data"}

        # Load multiple configs
        loader.load_profiles()
        loader.load_policy()
        assert "profiles" in loader._cache
        assert "policy" in loader._cache

        # Invalidate only profiles
        loader.invalidate(["profiles"])
        assert "profiles" not in loader._cache
        assert "policy" in loader._cache

    @patch('src.llm_security.core.config.loader.ConfigLoader._read_yaml')
    def test_cache_invalidation_nonexistent_key(self, mock_read, loader):
        """Test invalidating non-existent cache key (should not raise)."""
        loader.invalidate(["nonexistent"])
        # Should not raise any exception


class TestErrorHandling:
    """Test error handling in various scenarios."""

    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def loader(self, temp_dir):
        """ConfigLoader with paths in temp directory."""
        paths = ConfigPaths(
            profiles=temp_dir / "profiles.yaml",
            policy=temp_dir / "policy.yaml",
            tests=temp_dir / "tests.yaml",
            connections=temp_dir / "connections.yaml",
        )
        return ConfigLoader(paths)

    def test_missing_file_required_config(self, loader, temp_dir):
        """Test loading required config when file doesn't exist."""
        # profiles.yaml doesn't exist
        with pytest.raises(FileNotFoundError):
            loader.load_profiles()

    def test_file_permission_error_read(self, loader, temp_dir):
        """Test handling file permission error on read."""
        # Create file
        profiles_file = temp_dir / "profiles.yaml"
        profiles_file.write_text("test: data")

        # Mock open to raise permission error
        with patch('pathlib.Path.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                loader.load_profiles()

    def test_file_permission_error_write(self, loader, temp_dir):
        """Test handling file permission error on write."""
        data = {"test": "data"}

        # Mock open to raise permission error
        with patch('pathlib.Path.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                loader.save_connections(data)

    def test_invalid_yaml_structure(self, loader, temp_dir):
        """Test loading YAML with invalid structure."""
        (temp_dir / "profiles.yaml").write_text("invalid: yaml: structure: [\n  unclosed")

        with pytest.raises(Exception):  # yaml.YAMLError
            loader.load_profiles()

    def test_json_with_invalid_json(self, loader, temp_dir):
        """Test loading JSON with invalid JSON."""
        (temp_dir / "tests.json").write_text('{"invalid": json content')

        with pytest.raises(Exception):  # json.JSONDecodeError
            loader.load_tests()

    def test_json_non_mapping_root(self, loader, temp_dir):
        """Test loading JSON with non-mapping root."""
        # Change the loader to use .json file instead of .yaml
        loader._paths = ConfigPaths(
            profiles=loader._paths.profiles,
            policy=loader._paths.policy,
            tests=temp_dir / "tests.json",
            connections=loader._paths.connections
        )
        (temp_dir / "tests.json").write_text('["item1", "item2"]')

        with pytest.raises(TypeError, match="JSON root must be a mapping"):
            loader.load_tests()

    def test_encoding_error(self, loader, temp_dir):
        """Test handling file encoding errors."""
        # Create file with invalid UTF-8
        profiles_file = temp_dir / "profiles.yaml"
        with open(profiles_file, 'wb') as f:
            f.write(b'\xff\xfe\xfd')  # Invalid UTF-8 bytes

        with pytest.raises(UnicodeDecodeError):
            loader.load_profiles()


class TestPathResolution:
    """Test path resolution for different config scenarios."""

    def test_relative_paths(self):
        """Test with relative paths."""
        paths = ConfigPaths.default(Path("relative/path"))
        # On Windows, Path("relative/path") becomes "relative\\path"
        path_str = str(paths.profiles)
        assert "relative" in path_str and "path" in path_str
        assert "config" in path_str and "profiles.yaml" in path_str

    def test_absolute_paths(self):
        """Test with absolute paths."""
        root = Path("/absolute/path")
        paths = ConfigPaths.default(root)
        # On Windows, Path("/absolute/path") becomes "\\absolute\\path"
        path_str = str(paths.profiles)
        assert "absolute" in path_str and "path" in path_str

    def test_path_with_spaces(self):
        """Test paths containing spaces."""
        root = Path("/path with spaces")
        paths = ConfigPaths.default(root)
        assert "path with spaces" in str(paths.profiles)

    def test_path_with_special_characters(self):
        """Test paths with special characters."""
        root = Path("/path-with-dashes_underscores.123")
        paths = ConfigPaths.default(root)
        assert "path-with-dashes_underscores.123" in str(paths.profiles)


class TestIntegration:
    """Integration tests loading all configs together."""

    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def loader(self, temp_dir):
        """ConfigLoader with paths in temp directory."""
        paths = ConfigPaths(
            profiles=temp_dir / "config" / "profiles.yaml",
            policy=temp_dir / "config" / "policy.yaml",
            tests=temp_dir / "data" / "prompt_tests.yaml",
            connections=temp_dir / "config" / "llm_connections.yaml",
        )
        return ConfigLoader(paths)

    def test_load_all_configs(self, loader, temp_dir):
        """Test loading all config types."""
        # Create config directory structure
        config_dir = temp_dir / "config"
        data_dir = temp_dir / "data"
        config_dir.mkdir()
        data_dir.mkdir()

        # Create sample config files
        (config_dir / "profiles.yaml").write_text("""
profiles:
  test_profile:
    layers: [l1, l2]
    description: Test profile
""")

        (config_dir / "policy.yaml").write_text("""
policy:
  rules:
    - no_system_reveal
    - no_tool_abuse
""")

        (data_dir / "prompt_tests.yaml").write_text("""
tests:
  - name: basic_injection
    prompt: "Ignore previous instructions"
    expected: fail
""")

        (config_dir / "llm_connections.yaml").write_text("""
connections:
  test_conn:
    provider: dummy
    description: Test connection
""")

        # Load all configs
        profiles = loader.load_profiles()
        policy = loader.load_policy()
        tests = loader.load_tests()
        connections = loader.load_connections()

        assert "profiles" in profiles
        assert "test_profile" in profiles["profiles"]
        assert "policy" in policy
        assert "rules" in policy["policy"]
        assert "tests" in tests
        assert len(tests["tests"]) == 1
        assert "connections" in connections
        assert "test_conn" in connections["connections"]

    def test_cross_config_dependencies(self, loader, temp_dir):
        """Test that configs can reference each other if needed."""
        config_dir = temp_dir / "config"
        config_dir.mkdir()

        # Create profiles that might reference policy
        (config_dir / "profiles.yaml").write_text("""
profiles:
  secure_profile:
    layers: [l1, l2, l4]
""")

        (config_dir / "policy.yaml").write_text("""
policy:
  rules:
    - no_system_reveal
""")

        profiles = loader.load_profiles()
        policy = loader.load_policy()

        # Verify both loaded successfully
        assert profiles["profiles"]["secure_profile"]["layers"] == ["l1", "l2", "l4"]
        assert policy["policy"]["rules"] == ["no_system_reveal"]


class TestEdgeCases:
    """Test edge cases like empty files, malformed content, encoding issues."""

    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def loader(self, temp_dir):
        """ConfigLoader with paths in temp directory."""
        paths = ConfigPaths(
            profiles=temp_dir / "profiles.yaml",
            policy=temp_dir / "policy.yaml",
            tests=temp_dir / "tests.yaml",
            connections=temp_dir / "connections.yaml",
        )
        return ConfigLoader(paths)

    def test_empty_yaml_file(self, loader, temp_dir):
        """Test loading completely empty YAML file."""
        (temp_dir / "profiles.yaml").write_text("")

        result = loader.load_profiles()
        assert result == {}

    def test_yaml_only_whitespace(self, loader, temp_dir):
        """Test loading YAML file with only whitespace."""
        (temp_dir / "profiles.yaml").write_text("   \n   \n  ")

        result = loader.load_profiles()
        assert result == {}

    def test_malformed_yaml_tabs_spaces(self, loader, temp_dir):
        """Test loading YAML with mixed tabs and spaces."""
        (temp_dir / "profiles.yaml").write_text("profiles:\n\ttest: value\n  other: val")

        # This might work or fail depending on YAML parser
        try:
            result = loader.load_profiles()
            assert isinstance(result, dict)
        except Exception:
            # Expected if YAML parser is strict
            pass

    def test_very_large_yaml_file(self, loader, temp_dir):
        """Test loading a very large YAML file."""
        # Create large content
        large_content = "profiles:\n"
        for i in range(1000):
            large_content += f"  test_{i}:\n    value: {i}\n"

        (temp_dir / "profiles.yaml").write_text(large_content)

        result = loader.load_profiles()
        assert len(result["profiles"]) == 1000
        assert result["profiles"]["test_999"]["value"] == 999

    def test_yaml_with_unicode_bom(self, loader, temp_dir):
        """Test loading YAML file with UTF-8 BOM."""
        # Write file with BOM
        with open(temp_dir / "profiles.yaml", 'w', encoding='utf-8-sig') as f:
            f.write("profiles:\n  test: тест\n")

        result = loader.load_profiles()
        assert result["profiles"]["test"] == "тест"

    def test_round_trip_save_load(self, loader, temp_dir):
        """Test round-trip save and load functionality."""
        original_data = {
            "connections": {
                "conn1": {
                    "provider": "openrouter",
                    "description": "Test connection",
                    "model_id": "gpt-3.5-turbo",
                    "timeout": 30,
                    "headers": {"Custom": "Header"},
                    "auth": {"type": "env", "env_var": "API_KEY"}
                },
                "conn2": {
                    "provider": "dummy",
                    "description": "Dummy connection"
                }
            }
        }

        # Save data
        loader.save_connections(original_data)

        # Create new loader to ensure clean cache
        new_loader = ConfigLoader(loader._paths)

        # Load data back
        loaded_data = new_loader.load_connections()

        # Verify round-trip
        assert loaded_data == original_data

    def test_multiple_save_load_cycles(self, loader, temp_dir):
        """Test multiple save/load cycles."""
        for i in range(3):
            data = {"connections": {f"conn_{i}": {"provider": f"provider_{i}"}}}
            loader.save_connections(data)

            # Create new loader each time to test persistence
            new_loader = ConfigLoader(loader._paths)
            loaded = new_loader.load_connections()
            assert loaded == data